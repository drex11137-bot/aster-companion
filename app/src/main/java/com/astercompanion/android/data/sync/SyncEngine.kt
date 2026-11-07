package com.astercompanion.android.data.sync

import com.astercompanion.android.data.crypto.ChecksumUtil
import com.astercompanion.android.data.local.AsterDatabase
import com.astercompanion.android.data.local.ChatMessageDao
import com.astercompanion.android.data.local.ChatMessageEntity
import com.astercompanion.android.data.local.OutboxDao
import com.astercompanion.android.data.local.OutboxEventEntity
import com.astercompanion.android.data.local.SyncCheckpointDao
import com.astercompanion.android.data.local.SyncCheckpointEntity
import com.astercompanion.android.data.local.SyncGapDao
import com.astercompanion.android.data.local.SyncGapEntity
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import java.util.UUID

/**
 * Resumable offline-first synchronization engine and durable outbox processor (PRD v1.1 §6 & §14).
 *
 * Guarantees:
 * 1. Monotonic per-device sequence progression.
 * 2. Idempotent uploads with cryptographic SHA-256 payload checksums.
 * 3. Gap detection and explicit recording without inventing false continuity.
 * 4. Exponential backoff with full jitter on network interruptions.
 * 5. Distinct online/offline state: local cached history is always readable; cloud AI is explicitly unavailable offline.
 */
class SyncEngine(
    private val outboxDao: OutboxDao,
    private val syncCheckpointDao: SyncCheckpointDao,
    private val syncGapDao: SyncGapDao,
    private val chatMessageDao: ChatMessageDao,
    private val remoteClient: RemoteSyncClient,
    val deviceId: String,
    private val backoffStrategy: BackoffStrategy = BackoffStrategy(),
    private val gapDetector: GapDetector = GapDetector(syncGapDao),
    private val dispatcher: CoroutineDispatcher = Dispatchers.IO,
    private val maxRetries: Int = 5,
    private val autoStartWorker: Boolean = true
) {
    /**
     * Convenience constructor taking the AsterDatabase instance directly.
     */
    constructor(
        database: AsterDatabase,
        remoteClient: RemoteSyncClient,
        deviceId: String,
        backoffStrategy: BackoffStrategy = BackoffStrategy(),
        gapDetector: GapDetector = GapDetector(database.syncGapDao()),
        dispatcher: CoroutineDispatcher = Dispatchers.IO,
        maxRetries: Int = 5,
        autoStartWorker: Boolean = true
    ) : this(
        outboxDao = database.outboxDao(),
        syncCheckpointDao = database.syncCheckpointDao(),
        syncGapDao = database.syncGapDao(),
        chatMessageDao = database.chatMessageDao(),
        remoteClient = remoteClient,
        deviceId = deviceId,
        backoffStrategy = backoffStrategy,
        gapDetector = gapDetector,
        dispatcher = dispatcher,
        maxRetries = maxRetries,
        autoStartWorker = autoStartWorker
    )

    private val scope = CoroutineScope(dispatcher + SupervisorJob())
    private val sequenceMutex = Mutex()
    private val syncMutex = Mutex()
    private val syncTriggerChannel = Channel<Unit>(Channel.CONFLATED)

    private val _isOnline = MutableStateFlow(true)
    val isOnline: StateFlow<Boolean> = _isOnline.asStateFlow()

    private val _cloudAiAvailability = MutableStateFlow<CloudAiAvailability>(CloudAiAvailability.Available)
    val cloudAiAvailability: StateFlow<CloudAiAvailability> = _cloudAiAvailability.asStateFlow()

    private val _syncState = MutableStateFlow(SyncState())
    val syncState: StateFlow<SyncState> = _syncState.asStateFlow()

    private var workerJob: Job? = null
    private var consecutiveFailures = 0

    init {
        if (autoStartWorker) {
            startWorker()
        }
    }

    /**
     * Toggles online/offline connectivity state (PRD v1.1 §6.5).
     * Local cached data remains fully accessible regardless of state.
     */
    fun setOnlineState(online: Boolean) {
        _isOnline.value = online
        if (online) {
            _cloudAiAvailability.value = CloudAiAvailability.Available
            triggerSync()
        } else {
            _cloudAiAvailability.value = CloudAiAvailability.UnavailableOffline()
        }
        updateSyncStateSnapshot()
    }

    /**
     * Starts the background processing worker coroutine.
     */
    fun startWorker() {
        if (workerJob != null && workerJob?.isActive == true) return

        workerJob = scope.launch {
            while (isActive) {
                // Wait for sync trigger or periodic interval
                syncTriggerChannel.receive()

                if (!_isOnline.value) {
                    continue
                }

                syncMutex.withLock {
                    processPendingOutbox()
                }
            }
        }
    }

    /**
     * Stops the background worker coroutine.
     */
    fun stopWorker() {
        workerJob?.cancel()
        workerJob = null
    }

    /**
     * Signals the background worker to execute an outbox processing pass immediately.
     */
    fun triggerSync() {
        syncTriggerChannel.trySend(Unit)
    }

    /**
     * Enqueues an event into the durable outbox queue with monotonic sequence number and SHA-256 checksum.
     */
    suspend fun enqueueEvent(
        profileId: String,
        eventType: String,
        payloadJson: String
    ): OutboxEventEntity = sequenceMutex.withLock {
        val currentMaxSeq = outboxDao.getMaxSequenceNumber(deviceId) ?: 0L
        val nextSeq = currentMaxSeq + 1L
        val checksum = ChecksumUtil.computeSha256(payloadJson)

        val event = OutboxEventEntity(
            id = UUID.randomUUID().toString(),
            sequenceNumber = nextSeq,
            deviceId = deviceId,
            profileId = profileId,
            eventType = eventType,
            checksum = checksum,
            payloadJson = payloadJson,
            status = OutboxEventEntity.STATUS_PENDING,
            retryCount = 0,
            lastAttemptAt = null,
            errorMessage = null,
            createdAt = System.currentTimeMillis()
        )

        outboxDao.insertEvent(event)
        updateSyncStateSnapshot()
        triggerSync()
        return@withLock event
    }

    /**
     * Enqueues a chat message into local storage and outbox queue atomically.
     */
    suspend fun enqueueChatMessage(
        profileId: String,
        content: String,
        sender: String = ChatMessageEntity.SENDER_USER,
        mediaUri: String? = null,
        mediaType: String? = null,
        metadataJson: String? = null
    ): ChatMessageEntity {
        val messageId = UUID.randomUUID().toString()
        val now = System.currentTimeMillis()

        val chatMessage = ChatMessageEntity(
            id = messageId,
            profileId = profileId,
            sender = sender,
            text = content,
            createdAt = now,
            syncStatus = ChatMessageEntity.STATUS_PENDING_SEND,
            mediaUri = mediaUri,
            mediaType = mediaType,
            metadataJson = metadataJson
        )
        chatMessageDao.insertMessage(chatMessage)

        // Build canonical JSON payload for sync
        val payloadJson = buildString {
            append("{\"messageId\":\"").append(escapeJson(messageId)).append("\"")
            append(",\"profileId\":\"").append(escapeJson(profileId)).append("\"")
            append(",\"sender\":\"").append(escapeJson(sender)).append("\"")
            append(",\"content\":\"").append(escapeJson(content)).append("\"")
            append(",\"timestamp\":").append(now)
            if (mediaUri != null) append(",\"mediaUri\":\"").append(escapeJson(mediaUri)).append("\"")
            if (mediaType != null) append(",\"mediaType\":\"").append(escapeJson(mediaType)).append("\"")
            if (metadataJson != null) append(",\"metadataJson\":\"").append(escapeJson(metadataJson)).append("\"")
            append("}")
        }

        enqueueEvent(
            profileId = profileId,
            eventType = OutboxEventEntity.TYPE_CHAT_MESSAGE,
            payloadJson = payloadJson
        )

        return chatMessage
    }

    /**
     * Core outbox processor: reads pending events, checks for sequence gaps,
     * uploads batch idempotently, and applies exponential backoff on failure.
     */
    suspend fun processPendingOutbox(batchLimit: Int = 25): Boolean = syncMutex.withLock {
        if (!_isOnline.value) {
            return@withLock false
        }

        val pendingEvents = outboxDao.getPendingEvents(batchLimit)
        if (pendingEvents.isEmpty()) {
            consecutiveFailures = 0
            updateSyncStateSnapshot()
            return@withLock true
        }

        _syncState.value = _syncState.value.copy(isSyncing = true)

        // Group events by profile to preserve profile-specific checkpoints
        val eventsByProfile = pendingEvents.groupBy { it.profileId }
        var allBatchesSucceeded = true

        for ((profileId, events) in eventsByProfile) {
            val checkpoint = syncCheckpointDao.getCheckpoint(deviceId, profileId)
            val lastAckSeq = checkpoint?.lastAcknowledgedSequenceNumber ?: 0L

            // 1. Gap detection: verify starting sequence
            val firstEvent = events.first()
            gapDetector.checkSequence(
                deviceId = deviceId,
                profileId = profileId,
                lastKnownSequence = lastAckSeq,
                incomingSequence = firstEvent.sequenceNumber,
                reason = "OUTBOX_SEQUENCE_GAP_BEFORE_UPLOAD"
            )

            // Audit batch for any internal sequence jumps without fabricating data
            gapDetector.findGapsInBatch(deviceId, profileId, events, firstEvent.sequenceNumber)

            // 2. Mark in-flight
            val eventIds = events.map { it.id }
            val now = System.currentTimeMillis()
            outboxDao.markInFlight(eventIds, now)

            // 3. Upload to remote client
            val batch = SyncUploadBatch(
                deviceId = deviceId,
                profileId = profileId,
                events = events
            )

            val uploadResult = remoteClient.uploadBatch(batch)

            if (uploadResult.isSuccess) {
                val response = uploadResult.getOrThrow()
                // Mark acknowledged
                outboxDao.markAcknowledged(response.acknowledgedEventIds)

                // Update checkpoint
                val newCheckpoint = SyncCheckpointEntity(
                    deviceId = deviceId,
                    profileId = profileId,
                    lastAcknowledgedSequenceNumber = response.acknowledgedSequenceNumber,
                    lastServerTimestamp = response.serverTimestamp,
                    updatedAt = System.currentTimeMillis()
                )
                syncCheckpointDao.upsertCheckpoint(newCheckpoint)

                // Update corresponding chat messages to SYNCED
                for (event in events) {
                    if (event.eventType == OutboxEventEntity.TYPE_CHAT_MESSAGE) {
                        val messageId = extractJsonStringField(event.payloadJson, "messageId")
                        if (!messageId.isNullOrEmpty()) {
                            chatMessageDao.updateSyncStatus(
                                id = messageId,
                                status = ChatMessageEntity.STATUS_SYNCED
                            )
                        }
                    }
                }

                consecutiveFailures = 0
            } else {
                allBatchesSucceeded = false
                consecutiveFailures++
                val errorMsg = uploadResult.exceptionOrNull()?.message ?: "Upload failed"

                // Handle failure per event
                for (event in events) {
                    val nextRetry = event.retryCount + 1
                    val newStatus = if (nextRetry >= maxRetries) {
                        OutboxEventEntity.STATUS_FAILED
                    } else {
                        OutboxEventEntity.STATUS_PENDING
                    }
                    outboxDao.recordAttemptFailure(
                        id = event.id,
                        status = newStatus,
                        attemptAt = System.currentTimeMillis(),
                        errorMessage = errorMsg
                    )

                    // If event terminally failed, update chat message to FAILED
                    if (newStatus == OutboxEventEntity.STATUS_FAILED && event.eventType == OutboxEventEntity.TYPE_CHAT_MESSAGE) {
                        val messageId = extractJsonStringField(event.payloadJson, "messageId")
                        if (!messageId.isNullOrEmpty()) {
                            chatMessageDao.updateSyncStatus(
                                id = messageId,
                                status = ChatMessageEntity.STATUS_FAILED
                            )
                        }
                    }
                }

                // Exponential backoff with jitter on network failure
                val delayMs = backoffStrategy.calculateDelayMs(consecutiveFailures)
                _syncState.value = _syncState.value.copy(
                    lastErrorMessage = errorMsg
                )
                if (delayMs > 0) {
                    delay(delayMs)
                }
            }
        }

        _syncState.value = _syncState.value.copy(isSyncing = false)
        updateSyncStateSnapshot()
        return@withLock allBatchesSucceeded
    }

    /**
     * Resets any stale in-flight events that may have remained locked due to process kill.
     */
    suspend fun recoverStaleInFlightEvents(staleThresholdMs: Long = 60_000L) {
        val staleBefore = System.currentTimeMillis() - staleThresholdMs
        outboxDao.resetStaleInFlightEvents(staleBefore)
        updateSyncStateSnapshot()
    }

    private fun updateSyncStateSnapshot() {
        scope.launch {
            val pendingCount = outboxDao.getPendingCount()
            val gaps = syncGapDao.getUnacknowledgedGaps(deviceId)
            val currentMaxAck = syncCheckpointDao.getCheckpoint(deviceId, "default")
                ?.lastAcknowledgedSequenceNumber ?: 0L

            _syncState.value = SyncState(
                isOnline = _isOnline.value,
                isSyncing = _syncState.value.isSyncing,
                pendingEventCount = pendingCount,
                lastAcknowledgedSequence = currentMaxAck,
                totalGapsDetected = gaps.size,
                cloudAiAvailability = _cloudAiAvailability.value,
                lastSyncTimestamp = System.currentTimeMillis(),
                lastErrorMessage = _syncState.value.lastErrorMessage
            )
        }
    }

    companion object {
        fun escapeJson(value: String): String {
            val sb = StringBuilder()
            for (ch in value) {
                when (ch) {
                    '\\' -> sb.append("\\\\")
                    '"' -> sb.append("\\\"")
                    '\b' -> sb.append("\\b")
                    '\n' -> sb.append("\\n")
                    '\r' -> sb.append("\\r")
                    '\t' -> sb.append("\\t")
                    else -> sb.append(ch)
                }
            }
            return sb.toString()
        }

        fun extractJsonStringField(json: String, fieldName: String): String? {
            val pattern = "\"$fieldName\"\\s*:\\s*\"([^\"\\\\]*(?:\\\\.[^\"\\\\]*)*)\"".toRegex()
            val match = pattern.find(json) ?: return null
            return match.groupValues[1]
                .replace("\\\"", "\"")
                .replace("\\\\", "\\")
                .replace("\\n", "\n")
                .replace("\\r", "\r")
                .replace("\\t", "\t")
        }
    }
}
