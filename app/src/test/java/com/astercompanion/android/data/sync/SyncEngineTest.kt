package com.astercompanion.android.data.sync

import com.astercompanion.android.data.crypto.ChecksumUtil
import com.astercompanion.android.data.local.ChatMessageEntity
import com.astercompanion.android.data.local.OutboxEventEntity
import com.astercompanion.android.data.testutil.FakeChatMessageDao
import com.astercompanion.android.data.testutil.FakeOutboxDao
import com.astercompanion.android.data.testutil.FakeSyncCheckpointDao
import com.astercompanion.android.data.testutil.FakeSyncGapDao
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class SyncEngineTest {

    private lateinit var outboxDao: FakeOutboxDao
    private lateinit var syncCheckpointDao: FakeSyncCheckpointDao
    private lateinit var syncGapDao: FakeSyncGapDao
    private lateinit var chatMessageDao: FakeChatMessageDao
    private lateinit var remoteClient: MockRemoteSyncClient
    private lateinit var syncEngine: SyncEngine

    private val testDeviceId = "device_samsung_s24_ultra"
    private val testProfileId = "profile_aster_primary"

    @Before
    fun setUp() {
        outboxDao = FakeOutboxDao()
        syncCheckpointDao = FakeSyncCheckpointDao()
        syncGapDao = FakeSyncGapDao()
        chatMessageDao = FakeChatMessageDao()
        remoteClient = MockRemoteSyncClient()

        syncEngine = SyncEngine(
            outboxDao = outboxDao,
            syncCheckpointDao = syncCheckpointDao,
            syncGapDao = syncGapDao,
            chatMessageDao = chatMessageDao,
            remoteClient = remoteClient,
            deviceId = testDeviceId,
            backoffStrategy = BackoffStrategy(initialDelayMs = 10L, maxDelayMs = 50L), // fast for tests
            maxRetries = 3,
            autoStartWorker = false
        )
    }

    @Test
    fun testMonotonicSequenceNumberProgression() = runBlocking {
        val event1 = syncEngine.enqueueEvent(
            profileId = testProfileId,
            eventType = OutboxEventEntity.TYPE_SCREEN_FRAME,
            payloadJson = "{\"frameNumber\": 1, \"fps\": 120}"
        )
        val event2 = syncEngine.enqueueEvent(
            profileId = testProfileId,
            eventType = OutboxEventEntity.TYPE_SCREEN_FRAME,
            payloadJson = "{\"frameNumber\": 2, \"fps\": 120}"
        )
        val event3 = syncEngine.enqueueEvent(
            profileId = testProfileId,
            eventType = OutboxEventEntity.TYPE_SCREEN_FRAME,
            payloadJson = "{\"frameNumber\": 3, \"fps\": 120}"
        )

        assertEquals(1L, event1.sequenceNumber)
        assertEquals(2L, event2.sequenceNumber)
        assertEquals(3L, event3.sequenceNumber)

        // Verify SHA-256 checksums
        assertTrue(ChecksumUtil.verifyChecksum(event1.payloadJson, event1.checksum))
        assertTrue(ChecksumUtil.verifyChecksum(event2.payloadJson, event2.checksum))
        assertTrue(ChecksumUtil.verifyChecksum(event3.payloadJson, event3.checksum))
    }

    @Test
    fun testEnqueueChatMessageCreatesLocalMessageAndOutboxEvent() = runBlocking {
        val chatMessage = syncEngine.enqueueChatMessage(
            profileId = testProfileId,
            content = "Can you plan my Saturday?",
            sender = ChatMessageEntity.SENDER_USER
        )

        // Message should be stored locally as PENDING_SEND
        val storedMsg = chatMessageDao.getMessageById(chatMessage.id)
        assertNotNull(storedMsg)
        assertEquals(ChatMessageEntity.STATUS_PENDING_SEND, storedMsg?.syncStatus)
        assertEquals("Can you plan my Saturday?", storedMsg?.content)

        // Outbox event should be queued
        val pendingEvents = outboxDao.getPendingEvents(10)
        assertEquals(1, pendingEvents.size)
        assertEquals(OutboxEventEntity.TYPE_CHAT_MESSAGE, pendingEvents[0].eventType)
        assertEquals(1L, pendingEvents[0].sequenceNumber)
    }

    @Test
    fun testSuccessfulOutboxBatchProcessingAndAck() = runBlocking {
        // Enqueue 2 chat messages
        val msg1 = syncEngine.enqueueChatMessage(testProfileId, "Hello Aster!")
        val msg2 = syncEngine.enqueueChatMessage(testProfileId, "What's the weather like?")

        // Process outbox
        val success = syncEngine.processPendingOutbox(batchLimit = 10)
        assertTrue(success)

        // Events must be marked ACKNOWLEDGED
        val remainingPending = outboxDao.getPendingEvents(10)
        assertEquals(0, remainingPending.size)

        val evt1 = outboxDao.getEventBySequenceNumber(testDeviceId, 1L)
        val evt2 = outboxDao.getEventBySequenceNumber(testDeviceId, 2L)
        assertEquals(OutboxEventEntity.STATUS_ACKNOWLEDGED, evt1?.status)
        assertEquals(OutboxEventEntity.STATUS_ACKNOWLEDGED, evt2?.status)

        // Chat messages must be updated to SYNCED
        val updatedMsg1 = chatMessageDao.getMessageById(msg1.id)
        val updatedMsg2 = chatMessageDao.getMessageById(msg2.id)
        assertEquals(ChatMessageEntity.STATUS_SYNCED, updatedMsg1?.syncStatus)
        assertEquals(ChatMessageEntity.STATUS_SYNCED, updatedMsg2?.syncStatus)

        // Checkpoint must reflect sequence number 2
        val checkpoint = syncCheckpointDao.getCheckpoint(testDeviceId, testProfileId)
        assertNotNull(checkpoint)
        assertEquals(2L, checkpoint?.lastAcknowledgedSequenceNumber)
    }

    @Test
    fun testGapDetectionWithoutInventingFalseContinuity() = runBlocking {
        // Suppose server checkpoint is sequence 10
        syncCheckpointDao.updateCheckpoint(
            deviceId = testDeviceId,
            profileId = testProfileId,
            seqNumber = 10L,
            serverTimestamp = System.currentTimeMillis()
        )

        // Outbox has an event with sequence 15 (jump from 10 to 15, missing 11, 12, 13, 14)
        val jumpedEvent = OutboxEventEntity(
            id = "evt_jump",
            sequenceNumber = 15L,
            deviceId = testDeviceId,
            profileId = testProfileId,
            eventType = OutboxEventEntity.TYPE_SCREEN_FRAME,
            checksum = ChecksumUtil.computeSha256("{\"screen\":\"jump\"}"),
            payloadJson = "{\"screen\":\"jump\"}",
            status = OutboxEventEntity.STATUS_PENDING
        )
        outboxDao.insertEvent(jumpedEvent)

        // Run sync
        syncEngine.processPendingOutbox()

        // Verify that gap was logged in SyncGapDao
        val gaps = syncGapDao.getUnacknowledgedGaps(testDeviceId)
        assertEquals(1, gaps.size)
        val recordedGap = gaps[0]
        assertEquals(11L, recordedGap.fromSequence)
        assertEquals(14L, recordedGap.toSequence)
        assertEquals(4L, recordedGap.missingCount)
        assertFalse(recordedGap.isAcknowledged)
    }

    @Test
    fun testNetworkFailureAndTerminalRetry() = runBlocking {
        // Enqueue a message
        val msg = syncEngine.enqueueChatMessage(testProfileId, "Test message under network drop")

        // Turn network off on remote client
        remoteClient.setNetworkAvailable(false)

        // Attempt sync: 1st failure
        val pass1 = syncEngine.processPendingOutbox()
        assertFalse(pass1)
        var evt = outboxDao.getEventBySequenceNumber(testDeviceId, 1L)
        assertEquals(1, evt?.retryCount)
        assertEquals(OutboxEventEntity.STATUS_PENDING, evt?.status)

        // 2nd failure
        val pass2 = syncEngine.processPendingOutbox()
        assertFalse(pass2)
        evt = outboxDao.getEventBySequenceNumber(testDeviceId, 1L)
        assertEquals(2, evt?.retryCount)

        // 3rd failure (hits maxRetries = 3)
        val pass3 = syncEngine.processPendingOutbox()
        assertFalse(pass3)
        evt = outboxDao.getEventBySequenceNumber(testDeviceId, 1L)
        assertEquals(3, evt?.retryCount)
        assertEquals(OutboxEventEntity.STATUS_FAILED, evt?.status)

        // Chat message must also transition to FAILED
        val failedMsg = chatMessageDao.getMessageById(msg.id)
        assertEquals(ChatMessageEntity.STATUS_FAILED, failedMsg?.syncStatus)
    }

    @Test
    fun testDistinctOnlineOfflineStateAndCloudAiAvailability() = runBlocking {
        // By default online
        assertTrue(syncEngine.isOnline.value)
        assertTrue(syncEngine.cloudAiAvailability.value is CloudAiAvailability.Available)

        // Go offline
        syncEngine.setOnlineState(false)
        assertFalse(syncEngine.isOnline.value)
        val offlineAvailability = syncEngine.cloudAiAvailability.value
        assertTrue(offlineAvailability is CloudAiAvailability.UnavailableOffline)
        val message = (offlineAvailability as CloudAiAvailability.UnavailableOffline).message
        assertTrue(message.contains("Cloud AI reasoning"))
        assertTrue(message.contains("Local cached history"))

        // While offline, local operations still succeed
        val offlineMsg = syncEngine.enqueueChatMessage(testProfileId, "Saved offline")
        val localList = chatMessageDao.getMessagesForProfile(testProfileId).first()
        assertEquals(1, localList.size)
        assertEquals("Saved offline", localList[0].content)

        // Outbox processing skipped while offline
        val result = syncEngine.processPendingOutbox()
        assertFalse(result)

        // Come back online
        syncEngine.setOnlineState(true)
        assertTrue(syncEngine.isOnline.value)
        assertTrue(syncEngine.cloudAiAvailability.value is CloudAiAvailability.Available)

        // Now outbox processes successfully
        val onlineResult = syncEngine.processPendingOutbox()
        assertTrue(onlineResult)
        val syncedMsg = chatMessageDao.getMessageById(offlineMsg.id)
        assertEquals(ChatMessageEntity.STATUS_SYNCED, syncedMsg?.syncStatus)
    }
}
