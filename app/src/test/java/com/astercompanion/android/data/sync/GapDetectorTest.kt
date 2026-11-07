package com.astercompanion.android.data.sync

import com.astercompanion.android.data.local.OutboxEventEntity
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class GapDetectorTest {

    private val detector = GapDetector(syncGapDao = null)

    @Test
    fun testContinuousSequenceProducesNoGap() = runBlocking {
        val result = detector.checkSequence(
            deviceId = "pixel_9",
            profileId = "profile_1",
            lastKnownSequence = 42L,
            incomingSequence = 43L
        )
        assertTrue(result is GapDetectionResult.Continuous)
    }

    @Test
    fun testDuplicateOrOlderSequence() = runBlocking {
        val resultOld = detector.checkSequence(
            deviceId = "pixel_9",
            profileId = "profile_1",
            lastKnownSequence = 42L,
            incomingSequence = 40L
        )
        assertTrue(resultOld is GapDetectionResult.DuplicateOrOlder)

        val resultExactSame = detector.checkSequence(
            deviceId = "pixel_9",
            profileId = "profile_1",
            lastKnownSequence = 42L,
            incomingSequence = 42L
        )
        assertTrue(resultExactSame is GapDetectionResult.DuplicateOrOlder)
    }

    @Test
    fun testSequenceGapDetectionAndRecord() = runBlocking {
        // Last known sequence was 10, next is 15 -> missing 11, 12, 13, 14 (count = 4)
        val result = detector.checkSequence(
            deviceId = "pixel_9",
            profileId = "profile_1",
            lastKnownSequence = 10L,
            incomingSequence = 15L,
            reason = "NETWORK_INTERRUPT_GAP"
        )

        assertTrue(result is GapDetectionResult.GapDetected)
        val gap = (result as GapDetectionResult.GapDetected).gap
        assertEquals("pixel_9", gap.deviceId)
        assertEquals("profile_1", gap.profileId)
        assertEquals(11L, gap.fromSequence)
        assertEquals(14L, gap.toSequence)
        assertEquals(4L, gap.missingCount)
        assertEquals("NETWORK_INTERRUPT_GAP", gap.reason)
        assertEquals(false, gap.isAcknowledged)
    }

    @Test
    fun testFindGapsInBatch() {
        val events = listOf(
            createStubEvent(sequenceNumber = 1L),
            createStubEvent(sequenceNumber = 2L),
            // Missing 3 and 4
            createStubEvent(sequenceNumber = 5L),
            createStubEvent(sequenceNumber = 6L),
            // Missing 7, 8, 9
            createStubEvent(sequenceNumber = 10L)
        )

        val gaps = detector.findGapsInBatch(
            deviceId = "device_test",
            profileId = "profile_1",
            events = events,
            initialExpectedSequence = 1L
        )

        assertEquals(2, gaps.size)

        val gap1 = gaps[0]
        assertEquals(3L, gap1.fromSequence)
        assertEquals(4L, gap1.toSequence)
        assertEquals(2L, gap1.missingCount)

        val gap2 = gaps[1]
        assertEquals(7L, gap2.fromSequence)
        assertEquals(9L, gap2.toSequence)
        assertEquals(3L, gap2.missingCount)
    }

    private fun createStubEvent(sequenceNumber: Long): OutboxEventEntity {
        return OutboxEventEntity(
            id = "evt_$sequenceNumber",
            sequenceNumber = sequenceNumber,
            deviceId = "device_test",
            profileId = "profile_1",
            eventType = "TEST",
            checksum = "dummy",
            payloadJson = "{}"
        )
    }
}
