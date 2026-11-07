package com.astercompanion.android.awareness

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.zip.CRC32

/**
 * Unit tests for Awareness state transitions, configurations, and data models.
 * Verifies compliance with PRD v1.1 §5 & §13.
 */
class AwarenessStateTest {

    @Test
    fun testAwarenessStatusEnumValues() {
        val expectedStatuses = listOf(
            AwarenessStatus.IDLE,
            AwarenessStatus.INITIALIZING,
            AwarenessStatus.ACTIVE,
            AwarenessStatus.PAUSED,
            AwarenessStatus.MUTED,
            AwarenessStatus.REVOKED,
            AwarenessStatus.ERROR
        )
        for (status in expectedStatuses) {
            assertEquals(status, AwarenessStatus.valueOf(status.name))
        }
    }

    @Test
    fun testAudioCaptureModeEnumValues() {
        val modes = listOf(
            AudioCaptureMode.NONE,
            AudioCaptureMode.ENVIRONMENTAL_MIC,
            AudioCaptureMode.IN_DEVICE_PLAYBACK,
            AudioCaptureMode.DUAL
        )
        for (mode in modes) {
            assertEquals(mode, AudioCaptureMode.valueOf(mode.name))
        }
    }

    @Test
    fun testDefaultAwarenessConfigMatchesPrdRequirements() {
        val config = AwarenessConfig()
        assertEquals(1080, config.targetWidth)
        assertEquals(2400, config.targetHeight)
        assertEquals(420, config.targetDpi)
        assertEquals(60, config.captureFpsLimit)
        assertEquals(16000, config.audioSampleRate)
        assertEquals(AudioCaptureMode.DUAL, config.audioMode)
        assertEquals(0.96f, config.ssimChangeThreshold, 0.001f)
        assertEquals(4, config.pHashHammingThreshold)
        assertEquals(3000L, config.heartbeatIntervalMs)
        assertTrue(config.enableOverlayIndicator)
    }

    @Test
    fun testCapturedFrameEqualsAndHashCode() {
        val bytes1 = byteArrayOf(1, 2, 3, 4)
        val bytes2 = byteArrayOf(1, 2, 3, 4)
        val bytes3 = byteArrayOf(5, 6, 7, 8)

        val crc = CRC32()
        crc.update(bytes1)
        val checksum1 = crc.value

        val frame1 = CapturedFrame(
            sequenceNumber = 1L,
            timestampNs = 1000L,
            timestampEpochMs = 1700000000L,
            width = 100,
            height = 100,
            stride = 400,
            pixelFormat = 1,
            perceptualHash = 123456789L,
            ssimScore = 0.98f,
            isKeyframe = true,
            rgbaBytes = bytes1,
            checksum = checksum1
        )

        val frame2 = CapturedFrame(
            sequenceNumber = 1L,
            timestampNs = 1000L,
            timestampEpochMs = 1700000000L,
            width = 100,
            height = 100,
            stride = 400,
            pixelFormat = 1,
            perceptualHash = 123456789L,
            ssimScore = 0.98f,
            isKeyframe = true,
            rgbaBytes = bytes2,
            checksum = checksum1
        )

        val frame3 = frame1.copy(sequenceNumber = 2L)

        assertEquals("Identical frames must be equal", frame1, frame2)
        assertEquals("Identical frames must have equal hash code", frame1.hashCode(), frame2.hashCode())
        assertNotEquals("Different sequence must not be equal", frame1, frame3)
    }

    @Test
    fun testTimelineGapDataIntegrity() {
        val gap = TimelineGap(
            startSequence = 10L,
            endSequence = 15L,
            durationMs = 250L,
            reason = "Network backpressure drop",
            timestampEpochMs = 1700000000L
        )

        assertEquals(10L, gap.startSequence)
        assertEquals(15L, gap.endSequence)
        assertEquals(250L, gap.durationMs)
        assertEquals("Network backpressure drop", gap.reason)
        assertEquals(1700000000L, gap.timestampEpochMs)
    }
}
