package com.astercompanion.android.testutil

import com.astercompanion.android.data.local.ChatMessageDao
import com.astercompanion.android.data.local.ChatMessageEntity
import com.astercompanion.android.data.local.MemoryDao
import com.astercompanion.android.data.local.MemoryEntity
import com.astercompanion.android.data.local.OutboxDao
import com.astercompanion.android.data.local.OutboxEventEntity
import com.astercompanion.android.data.local.ProfileDao
import com.astercompanion.android.data.local.ProfileEntity
import com.astercompanion.android.data.local.ReminderEntity
import com.astercompanion.android.data.local.ScreenEventDao
import com.astercompanion.android.data.local.ScreenEventEntity
import com.astercompanion.android.data.local.SyncCheckpointDao
import com.astercompanion.android.data.local.SyncCheckpointEntity
import com.astercompanion.android.data.local.SyncGapDao
import com.astercompanion.android.data.local.SyncGapEntity
import com.astercompanion.android.data.local.TaskEntity
import com.astercompanion.android.data.local.TodayDao
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.map
import java.util.concurrent.ConcurrentHashMap

class FakeProfileDao : ProfileDao {
    private val profiles = ConcurrentHashMap<String, ProfileEntity>()
    private val profilesFlow = MutableStateFlow<List<ProfileEntity>>(emptyList())

    private fun emit() {
        profilesFlow.value = profiles.values.sortedBy { it.createdAt }
    }

    override fun getProfiles(): Flow<List<ProfileEntity>> = profilesFlow.asStateFlow()

    override fun getAllProfiles(): Flow<List<ProfileEntity>> = getProfiles()

    override fun getAllProfilesSync(): List<ProfileEntity> = profiles.values.sortedBy { it.createdAt }

    override suspend fun getProfileById(id: String): ProfileEntity? = profiles[id]

    override fun observeProfileById(id: String): Flow<ProfileEntity?> =
        profilesFlow.map { list -> list.firstOrNull { it.id == id } }

    override fun getActiveProfile(): Flow<ProfileEntity?> =
        profilesFlow.map { list -> list.firstOrNull { it.isActive } }

    override suspend fun getActiveProfileSync(): ProfileEntity? =
        profiles.values.firstOrNull { it.isActive }

    override suspend fun countProfiles(): Int = profiles.size

    override suspend fun insertProfile(profile: ProfileEntity) {
        profiles[profile.id] = profile
        emit()
    }

    override suspend fun insertProfiles(profiles: List<ProfileEntity>) {
        profiles.forEach { this.profiles[it.id] = it }
        emit()
    }

    override suspend fun updateProfile(profile: ProfileEntity) {
        profiles[profile.id] = profile
        emit()
    }

    override suspend fun deleteProfile(id: String) {
        profiles.remove(id)
        emit()
    }

    override suspend fun deactivateAllProfiles(timestamp: Long) {
        profiles.forEach { (k, v) ->
            if (v.isActive) {
                profiles[k] = v.copy(isActiveOnDevice = false, updatedAt = timestamp)
            }
        }
        emit()
    }

    override suspend fun activateProfile(profileId: String, timestamp: Long) {
        profiles[profileId]?.let {
            profiles[profileId] = it.copy(isActiveOnDevice = true, updatedAt = timestamp)
        }
        emit()
    }

    override suspend fun updateSettings(
        profileId: String,
        name: String,
        avatar: String,
        voice: String,
        style: String,
        updatedAt: Long
    ) {
        profiles[profileId]?.let {
            profiles[profileId] = it.copy(
                name = name,
                avatarUrl = avatar,
                voice = voice,
                style = style,
                updatedAt = updatedAt
            )
            emit()
        }
    }

    override suspend fun updateAppearance(
        profileId: String,
        hairColor: String,
        eyeColor: String,
        updatedAt: Long
    ) {
        profiles[profileId]?.let {
            profiles[profileId] = it.copy(
                hairColor = hairColor,
                eyeColor = eyeColor,
                updatedAt = updatedAt
            )
            emit()
        }
    }
}

class FakeMemoryDao : MemoryDao {
    private val memories = ConcurrentHashMap<String, MemoryEntity>()
    private val memoriesFlow = MutableStateFlow<List<MemoryEntity>>(emptyList())

    private fun emit() {
        memoriesFlow.value = memories.values.toList()
    }

    override fun getActiveMemories(profileId: String): Flow<List<MemoryEntity>> =
        memoriesFlow.map { list ->
            list.filter { it.profileId == profileId && !it.isForgotten }
                .sortedWith(compareByDescending<MemoryEntity> { it.isPinned }.thenByDescending { it.updatedAt })
        }

    override fun getAllMemories(profileId: String): Flow<List<MemoryEntity>> =
        memoriesFlow.map { list ->
            list.filter { it.profileId == profileId }
                .sortedByDescending { it.updatedAt }
        }

    override fun getPinnedMemories(profileId: String): Flow<List<MemoryEntity>> =
        memoriesFlow.map { list ->
            list.filter { it.profileId == profileId && it.isPinned && !it.isForgotten }
                .sortedByDescending { it.updatedAt }
        }

    override fun getMemoriesByCategory(profileId: String, category: String): Flow<List<MemoryEntity>> =
        memoriesFlow.map { list ->
            list.filter { it.profileId == profileId && it.category == category && !it.isForgotten }
                .sortedWith(compareByDescending<MemoryEntity> { it.isPinned }.thenByDescending { it.updatedAt })
        }

    override fun searchMemories(profileId: String, query: String): Flow<List<MemoryEntity>> =
        memoriesFlow.map { list ->
            list.filter { it.profileId == profileId && !it.isForgotten && it.content.contains(query, ignoreCase = true) }
                .sortedWith(compareByDescending<MemoryEntity> { it.isPinned }.thenByDescending { it.updatedAt })
        }

    override fun getMemories(profileId: String, category: String, query: String): Flow<List<MemoryEntity>> =
        memoriesFlow.map { list ->
            list.filter { it.profileId == profileId && !it.isForgotten }
                .filter { category == "All" || it.category == category }
                .filter { query.isEmpty() || it.content.contains(query, ignoreCase = true) }
                .sortedWith(compareByDescending<MemoryEntity> { it.isPinned }.thenByDescending { it.updatedAt })
        }

    override suspend fun getMemoryById(profileId: String, id: String): MemoryEntity? {
        val mem = memories[id]
        return if (mem?.profileId == profileId) mem else null
    }

    override suspend fun getMemoryByIdGlobal(id: String): MemoryEntity? = memories[id]

    override suspend fun insertMemory(memory: MemoryEntity) {
        memories[memory.id] = memory
        emit()
    }

    override suspend fun insertMemories(memories: List<MemoryEntity>) {
        memories.forEach { this.memories[it.id] = it }
        emit()
    }

    override suspend fun updateMemory(memory: MemoryEntity) {
        memories[memory.id] = memory
        emit()
    }

    override suspend fun setPinned(profileId: String, id: String, isPinned: Boolean, timestamp: Long) {
        val existing = memories[id]
        if (existing != null && existing.profileId == profileId) {
            memories[id] = existing.copy(isPinned = isPinned, updatedAt = timestamp)
            emit()
        }
    }

    override suspend fun setForgotten(profileId: String, id: String, isForgotten: Boolean, timestamp: Long) {
        val existing = memories[id]
        if (existing != null && existing.profileId == profileId) {
            memories[id] = existing.copy(isForgotten = isForgotten, updatedAt = timestamp)
            emit()
        }
    }

    override suspend fun deleteMemory(profileId: String, id: String) {
        val existing = memories[id]
        if (existing != null && existing.profileId == profileId) {
            memories.remove(id)
            emit()
        }
    }

    override suspend fun delete(memory: MemoryEntity) {
        memories.remove(memory.id)
        emit()
    }

    override suspend fun deleteById(memoryId: String) {
        memories.remove(memoryId)
        emit()
    }

    override suspend fun deleteAllForProfile(profileId: String) {
        memories.entries.removeIf { it.value.profileId == profileId }
        emit()
    }

    override suspend fun countActiveMemories(profileId: String): Int =
        memories.values.count { it.profileId == profileId && !it.isForgotten }

    override fun getRecentMemories(profileId: String, limit: Int): Flow<List<MemoryEntity>> =
        memoriesFlow.map { list ->
            list.filter { it.profileId == profileId && !it.isForgotten }
                .sortedByDescending { it.createdAt }
                .take(limit)
        }

    override fun getMemoriesForProfile(profileId: String): Flow<List<MemoryEntity>> = getAllMemories(profileId)
}

class FakeChatDao : ChatMessageDao {
    private val messages = ConcurrentHashMap<String, ChatMessageEntity>()
    private val messagesFlow = MutableStateFlow<List<ChatMessageEntity>>(emptyList())

    private fun emit() {
        messagesFlow.value = messages.values.toList()
    }

    fun getMessages(profileId: String): Flow<List<ChatMessageEntity>> = getMessagesForProfile(profileId)

    override fun getMessagesForProfile(profileId: String): Flow<List<ChatMessageEntity>> =
        messagesFlow.map { list ->
            list.filter { it.profileId == profileId }.sortedBy { it.createdAt }
        }

    override suspend fun getRecentMessages(profileId: String, limit: Int): List<ChatMessageEntity> =
        messages.values.filter { it.profileId == profileId }
            .sortedByDescending { it.createdAt }
            .take(limit)

    override suspend fun getPendingMessages(profileId: String): List<ChatMessageEntity> =
        messages.values.filter { it.profileId == profileId && it.syncStatus == ChatMessageEntity.STATUS_PENDING_SEND }
            .sortedBy { it.createdAt }

    override suspend fun getAllPendingMessages(): List<ChatMessageEntity> =
        messages.values.filter { it.syncStatus == ChatMessageEntity.STATUS_PENDING_SEND }
            .sortedBy { it.createdAt }

    override suspend fun getMessageById(id: String): ChatMessageEntity? = messages[id]

    override suspend fun insertMessage(message: ChatMessageEntity) {
        messages[message.id] = message
        emit()
    }

    override suspend fun insertMessages(messages: List<ChatMessageEntity>) {
        messages.forEach { this.messages[it.id] = it }
        emit()
    }

    override suspend fun updateMessage(message: ChatMessageEntity) {
        messages[message.id] = message
        emit()
    }

    suspend fun updateMessageContent(id: String, text: String) {
        messages[id]?.let {
            messages[id] = it.copy(text = text)
            emit()
        }
    }

    override suspend fun updateSyncStatus(id: String, status: String) {
        messages[id]?.let {
            messages[id] = it.copy(syncStatus = status)
            emit()
        }
    }

    override suspend fun updateSyncStatusBatch(ids: List<String>, status: String) {
        ids.forEach { id ->
            messages[id]?.let {
                messages[id] = it.copy(syncStatus = status)
            }
        }
        emit()
    }

    override suspend fun deleteMessage(profileId: String, id: String) {
        val existing = messages[id]
        if (existing?.profileId == profileId) {
            messages.remove(id)
            emit()
        }
    }

    override suspend fun deleteMessagesForProfile(profileId: String) {
        messages.entries.removeIf { it.value.profileId == profileId }
        emit()
    }

    override suspend fun countMessagesForProfile(profileId: String): Int =
        messages.values.count { it.profileId == profileId }
}

typealias FakeChatMessageDao = FakeChatDao

class FakeTodayDao : TodayDao {
    private val reminders = ConcurrentHashMap<String, ReminderEntity>()
    private val remindersFlow = MutableStateFlow<List<ReminderEntity>>(emptyList())
    private val tasks = ConcurrentHashMap<String, TaskEntity>()
    private val tasksFlow = MutableStateFlow<List<TaskEntity>>(emptyList())

    private fun emitReminders() {
        remindersFlow.value = reminders.values.toList()
    }

    private fun emitTasks() {
        tasksFlow.value = tasks.values.toList()
    }

    override fun getNextReminder(profileId: String): Flow<ReminderEntity?> =
        remindersFlow.map { list ->
            list.filter { it.profileId == profileId }
                .maxByOrNull { it.createdAt }
        }

    override fun getTasks(profileId: String): Flow<List<TaskEntity>> =
        tasksFlow.map { list ->
            list.filter { it.profileId == profileId }
                .sortedBy { it.createdAt }
        }

    override suspend fun insertReminder(reminder: ReminderEntity) {
        reminders[reminder.id] = reminder
        emitReminders()
    }

    override suspend fun insertReminders(reminders: List<ReminderEntity>) {
        reminders.forEach { this.reminders[it.id] = it }
        emitReminders()
    }

    override suspend fun insertTask(task: TaskEntity) {
        tasks[task.id] = task
        emitTasks()
    }

    override suspend fun insertTasks(tasks: List<TaskEntity>) {
        tasks.forEach { this.tasks[it.id] = it }
        emitTasks()
    }

    override suspend fun updateTask(task: TaskEntity) {
        tasks[task.id] = task
        emitTasks()
    }
}

class FakeScreenEventDao : ScreenEventDao {
    private val events = ConcurrentHashMap<String, ScreenEventEntity>()
    private val eventsFlow = MutableStateFlow<List<ScreenEventEntity>>(emptyList())

    private fun emit() {
        eventsFlow.value = events.values.toList()
    }

    override fun getRecentEvents(profileId: String, limit: Int): Flow<List<ScreenEventEntity>> =
        eventsFlow.map { list ->
            list.filter { it.profileId == profileId }
                .sortedByDescending { it.timestamp }
                .take(limit)
        }

    override fun getAllEvents(profileId: String): Flow<List<ScreenEventEntity>> =
        eventsFlow.map { list ->
            list.filter { it.profileId == profileId }
                .sortedBy { it.timestamp }
        }

    override suspend fun insertEvent(event: ScreenEventEntity) {
        events[event.id] = event
        emit()
    }

    override suspend fun insertEvents(events: List<ScreenEventEntity>) {
        events.forEach { this.events[it.id] = it }
        emit()
    }

    override suspend fun clearEvents(profileId: String) {
        events.entries.removeIf { it.value.profileId == profileId }
        emit()
    }

    override suspend fun getMaxSequenceNumber(profileId: String): Long? =
        events.values.filter { it.profileId == profileId }
            .maxOfOrNull { it.sequenceNumber }
}

class FakeOutboxDao : OutboxDao {
    private val events = ConcurrentHashMap<String, OutboxEventEntity>()
    private val pendingCountFlow = MutableStateFlow(0)

    private fun emit() {
        pendingCountFlow.value = events.values.count {
            it.status == OutboxEventEntity.STATUS_PENDING || it.status == OutboxEventEntity.STATUS_IN_FLIGHT
        }
    }

    override suspend fun getMaxSequenceNumber(deviceId: String): Long? =
        events.values.filter { it.deviceId == deviceId }
            .maxOfOrNull { it.sequenceNumber }

    override suspend fun getPendingEvents(limit: Int): List<OutboxEventEntity> =
        events.values.filter { it.status == OutboxEventEntity.STATUS_PENDING }
            .sortedBy { it.sequenceNumber }
            .take(limit)

    override suspend fun getPendingEventsForProfile(profileId: String, limit: Int): List<OutboxEventEntity> =
        events.values.filter { it.profileId == profileId && it.status == OutboxEventEntity.STATUS_PENDING }
            .sortedBy { it.sequenceNumber }
            .take(limit)

    override suspend fun getInFlightEvents(): List<OutboxEventEntity> =
        events.values.filter { it.status == OutboxEventEntity.STATUS_IN_FLIGHT }
            .sortedBy { it.sequenceNumber }

    override suspend fun getEventById(id: String): OutboxEventEntity? = events[id]

    override suspend fun getEventBySequenceNumber(deviceId: String, sequenceNumber: Long): OutboxEventEntity? =
        events.values.firstOrNull { it.deviceId == deviceId && it.sequenceNumber == sequenceNumber }

    override suspend fun getAllEventsForDevice(deviceId: String): List<OutboxEventEntity> =
        events.values.filter { it.deviceId == deviceId }
            .sortedBy { it.sequenceNumber }

    override suspend fun insertEvent(event: OutboxEventEntity) {
        events[event.id] = event
        emit()
    }

    override suspend fun insertEvents(events: List<OutboxEventEntity>) {
        events.forEach { this.events[it.id] = it }
        emit()
    }

    override suspend fun updateEvent(event: OutboxEventEntity) {
        events[event.id] = event
        emit()
    }

    override suspend fun markInFlight(ids: List<String>, attemptAt: Long) {
        ids.forEach { id ->
            events[id]?.let {
                events[id] = it.copy(status = OutboxEventEntity.STATUS_IN_FLIGHT, lastAttemptAt = attemptAt)
            }
        }
        emit()
    }

    override suspend fun markAcknowledged(ids: List<String>) {
        ids.forEach { id ->
            events[id]?.let {
                events[id] = it.copy(status = OutboxEventEntity.STATUS_ACKNOWLEDGED, errorMessage = null)
            }
        }
        emit()
    }

    override suspend fun acknowledgeUpToSequence(deviceId: String, sequenceNumber: Long) {
        events.values.filter { it.deviceId == deviceId && it.sequenceNumber <= sequenceNumber }
            .forEach {
                events[it.id] = it.copy(status = OutboxEventEntity.STATUS_ACKNOWLEDGED, errorMessage = null)
            }
        emit()
    }

    override suspend fun recordAttemptFailure(id: String, status: String, attemptAt: Long, errorMessage: String?) {
        events[id]?.let {
            events[id] = it.copy(
                status = status,
                retryCount = it.retryCount + 1,
                lastAttemptAt = attemptAt,
                errorMessage = errorMessage
            )
        }
        emit()
    }

    override suspend fun resetStaleInFlightEvents(staleThreshold: Long) {
        events.values.filter { it.status == OutboxEventEntity.STATUS_IN_FLIGHT && (it.lastAttemptAt ?: 0L) < staleThreshold }
            .forEach {
                events[it.id] = it.copy(status = OutboxEventEntity.STATUS_PENDING)
            }
        emit()
    }

    override fun getPendingCountFlow(): Flow<Int> = pendingCountFlow.asStateFlow()

    override suspend fun getPendingCount(): Int =
        events.values.count {
            it.status == OutboxEventEntity.STATUS_PENDING || it.status == OutboxEventEntity.STATUS_IN_FLIGHT
        }

    override suspend fun pruneAcknowledgedEvents(olderThan: Long): Int {
        var count = 0
        events.entries.removeIf {
            if (it.value.status == OutboxEventEntity.STATUS_ACKNOWLEDGED && it.value.createdAt < olderThan) {
                count++
                true
            } else false
        }
        emit()
        return count
    }

    override suspend fun clearDeviceEvents(deviceId: String) {
        events.entries.removeIf { it.value.deviceId == deviceId }
        emit()
    }
}

class FakeSyncCheckpointDao : SyncCheckpointDao {
    private val checkpoints = ConcurrentHashMap<String, SyncCheckpointEntity>()
    private val checkpointsFlow = MutableStateFlow<Map<String, SyncCheckpointEntity>>(emptyMap())

    private fun key(deviceId: String, profileId: String) = "$deviceId:$profileId"

    override suspend fun getCheckpoint(deviceId: String, profileId: String): SyncCheckpointEntity? =
        checkpoints[key(deviceId, profileId)]

    override fun getCheckpointFlow(deviceId: String, profileId: String): Flow<SyncCheckpointEntity?> =
        checkpointsFlow.map { it[key(deviceId, profileId)] }

    override suspend fun upsertCheckpoint(checkpoint: SyncCheckpointEntity) {
        checkpoints[key(checkpoint.deviceId, checkpoint.profileId)] = checkpoint
        checkpointsFlow.value = checkpoints.toMap()
    }

    override suspend fun updateCheckpoint(
        deviceId: String,
        profileId: String,
        seqNumber: Long,
        serverTimestamp: Long,
        updatedAt: Long
    ): Int {
        val k = key(deviceId, profileId)
        val cp = SyncCheckpointEntity(
            deviceId = deviceId,
            profileId = profileId,
            lastAcknowledgedSequenceNumber = seqNumber,
            lastServerTimestamp = serverTimestamp,
            updatedAt = updatedAt
        )
        checkpoints[k] = cp
        checkpointsFlow.value = checkpoints.toMap()
        return 1
    }

    override suspend fun deleteCheckpointsForDevice(deviceId: String) {
        checkpoints.entries.removeIf { it.key.startsWith("$deviceId:") }
        checkpointsFlow.value = checkpoints.toMap()
    }
}

class FakeSyncGapDao : SyncGapDao {
    private val gaps = ConcurrentHashMap<String, SyncGapEntity>()
    private val gapsFlow = MutableStateFlow<List<SyncGapEntity>>(emptyList())

    private fun emit() {
        gapsFlow.value = gaps.values.toList()
    }

    override fun getGapsForDevice(deviceId: String): Flow<List<SyncGapEntity>> =
        gapsFlow.map { list -> list.filter { it.deviceId == deviceId }.sortedBy { it.fromSequence } }

    override suspend fun getGapsForProfileSync(deviceId: String, profileId: String): List<SyncGapEntity> =
        gaps.values.filter { it.deviceId == deviceId && it.profileId == profileId }
            .sortedBy { it.fromSequence }

    override suspend fun getUnacknowledgedGaps(deviceId: String): List<SyncGapEntity> =
        gaps.values.filter { it.deviceId == deviceId && !it.isAcknowledged }
            .sortedBy { it.fromSequence }

    override suspend fun insertGap(gap: SyncGapEntity) {
        gaps[gap.id] = gap
        emit()
    }

    override suspend fun acknowledgeGap(gapId: String) {
        gaps[gapId]?.let {
            gaps[gapId] = it.copy(isAcknowledged = true)
            emit()
        }
    }

    override suspend fun deleteGapsForDevice(deviceId: String) {
        gaps.entries.removeIf { it.value.deviceId == deviceId }
        emit()
    }
}
