package com.astercompanion.android.awareness

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

/**
 * Unit tests for MetricsTracker.
 * Verifies performance instrumentation and gap detection per PRD v1.1 §5.3 & §6.4:
 * - Accurately reports missing context; never invents missing frames.
 * - Tracks separate metrics for capture, upload, ingest, and analysis FPS.
 * - Handles pauses, mutes, and sequence resets cleanly.
 */
class MetricsTrackerTest {

    private val testScope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
    private lateinit var tracker: MetricsTracker

    @Before
    fun setUp() {
        tracker = MetricsTracker(
            scope = testScope,
            profileId = "profile_aster",
            windowDurationMs = 1000L
        )
    }

    @Test
    fun testInitialMetricsState() {
        runBlocking {
            val initial = tracker.metrics.value
            assertEquals("profile_aster", initial.activeProfileId)
            assertEquals(0L, initial.droppedFramesCount)
            assertEquals(0L, initial.timelineGapsCount)
            assertNull(initial.lastGap)
            assertEquals(0.0f, initial.captureFps, 0.001f)
            assertEquals(0.0f, initial.uploadFps, 0.001f)
        }
    }

    @Test
    fun testConsecutiveSequencesProduceZeroGaps() {
        runBlocking {
            val baseTime = 1000L
            tracker.recordCaptureFrame(0L, baseTime)
            tracker.recordCaptureFrame(1L, baseTime + 16L)
            tracker.recordCaptureFrame(2L, baseTime + 33L)
            tracker.recordCaptureFrame(3L, baseTime + 50L)

            val metrics = tracker.metrics.value
            assertEquals("Consecutive sequences must produce 0 gaps", 0L, metrics.timelineGapsCount)
            assertEquals("No dropped frames in consecutive sequence", 0L, metrics.droppedFramesCount)
            assertNull(metrics.lastGap)
        }
    }

    @Test
    fun testSequenceJumpAccuratelyDetectsAndReportsGap() {
        runBlocking {
            val baseTime = 1000L
            tracker.recordCaptureFrame(0L, baseTime)
            tracker.recordCaptureFrame(1L, baseTime + 16L)
            tracker.recordCaptureFrame(2L, baseTime + 33L)

            // Buffer backpressure/drop occurs: jump from sequence 2 to sequence 7 (missing 3, 4, 5, 6)
            tracker.recordCaptureFrame(7L, baseTime + 100L)

            val metrics = tracker.metrics.value
            assertEquals("Timeline gap count must be 1", 1L, metrics.timelineGapsCount)
            assertEquals("Dropped frames must equal 4", 4L, metrics.droppedFramesCount)

            val gap = metrics.lastGap
            assertNotNull("Gap must be accurately reported", gap)
            gap?.let {
                assertEquals("Gap start sequence must be 3", 3L, it.startSequence)
                assertEquals("Gap end sequence must be 6", 6L, it.endSequence)
                assertEquals("Gap duration must match timestamp delta", 67L, it.durationMs)
                assertTrue("Gap reason must describe backpressure", it.reason.contains("backpressure"))
            }
        }
    }

    @Test
    fun testAudioAndLatencyTracking() {
        runBlocking {
            tracker.recordAudioChunk()
            tracker.recordAudioChunk()
            tracker.recordLatency(42L)

            val metrics = tracker.metrics.value
            assertEquals(2L, metrics.audioChunksTransmitted)
            assertEquals(42L, metrics.endToEndLatencyMs)
        }
    }

    @Test
    fun testPauseAndMuteStatePropagation() {
        runBlocking {
            tracker.setScreenPaused(true)
            assertTrue(tracker.metrics.value.isScreenPaused)

            tracker.setAudioMuted(true)
            assertTrue(tracker.metrics.value.isAudioMuted)

            tracker.setScreenPaused(false)
            tracker.setAudioMuted(false)
            assertEquals(false, tracker.metrics.value.isScreenPaused)
            assertEquals(false, tracker.metrics.value.isAudioMuted)
        }
    }

    @Test
    fun testResetClearsMetricsAndCounters() {
        runBlocking {
            tracker.recordCaptureFrame(0L, 1000L)
            tracker.recordCaptureFrame(5L, 1200L) // Introduces gap
            tracker.recordAudioChunk()

            tracker.reset("profile_nova")

            val resetMetrics = tracker.metrics.value
            assertEquals("profile_nova", resetMetrics.activeProfileId)
            assertEquals(0L, resetMetrics.droppedFramesCount)
            assertEquals(0L, resetMetrics.timelineGapsCount)
            assertNull(resetMetrics.lastGap)
            assertEquals(0L, resetMetrics.audioChunksTransmitted)
        }
    }
}
