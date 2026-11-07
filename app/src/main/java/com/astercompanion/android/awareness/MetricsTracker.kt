package com.astercompanion.android.awareness

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.util.ArrayDeque

/**
 * Performance instrumentation tracker for Aster Companion awareness subsystem.
 * Accurately tracks separate FPS metrics per PRD v1.1 §5.3:
 * - captureFps: Frames acquired by VirtualDisplay into ImageReader
 * - uploadFps: Frames dispatched across network/client layer
 * - ingestFps: Frames accepted by cloud backend
 * - analysisFps: Vision model inference throughput
 *
 * Implements strict gap detection per PRD §6.4:
 * Aster accurately detects and reports missing segments, never inventing false continuity.
 */
class MetricsTracker(
    private val scope: CoroutineScope,
    private val profileId: String = "profile_aster",
    private val windowDurationMs: Long = 1000L
) {

    private var currentProfileId: String = profileId
    private val _metrics = MutableStateFlow(AwarenessMetrics(activeProfileId = profileId))
    val metrics: StateFlow<AwarenessMetrics> = _metrics.asStateFlow()

    private val captureTimestamps = ArrayDeque<Long>()
    private val uploadTimestamps = ArrayDeque<Long>()
    private val ingestTimestamps = ArrayDeque<Long>()
    private val analysisTimestamps = ArrayDeque<Long>()

    private var expectedCaptureSequence: Long = 0L
    private var lastFrameTimestampMs: Long = 0L

    private var totalDroppedFrames: Long = 0L
    private var totalTimelineGaps: Long = 0L
    private var lastRecordedGap: TimelineGap? = null
    private var totalAudioChunks: Long = 0L
    private var currentEndToEndLatencyMs: Long = 0L
    private var sessionStartTimeMs: Long = System.currentTimeMillis()

    private var isScreenPaused: Boolean = false
    private var isAudioMuted: Boolean = false

    private var tickerJob: Job? = null

    init {
        startMetricsTicker()
    }

    /**
     * Resets sequence counters and timers for a new awareness session.
     */
    @Synchronized
    fun reset(newProfileId: String = profileId) {
        currentProfileId = newProfileId
        captureTimestamps.clear()
        uploadTimestamps.clear()
        ingestTimestamps.clear()
        analysisTimestamps.clear()
        expectedCaptureSequence = 0L
        lastFrameTimestampMs = 0L
        totalDroppedFrames = 0L
        totalTimelineGaps = 0L
        lastRecordedGap = null
        totalAudioChunks = 0L
        currentEndToEndLatencyMs = 0L
        sessionStartTimeMs = System.currentTimeMillis()
        publishSnapshot(System.currentTimeMillis())
    }

    /**
     * Records a frame captured from VirtualDisplay.
     * Evaluates sequence continuity and detects missing frames.
     */
    @Synchronized
    fun recordCaptureFrame(sequenceNumber: Long, timestampEpochMs: Long = System.currentTimeMillis()) {
        val now = System.currentTimeMillis()
        captureTimestamps.addLast(now)

        if (expectedCaptureSequence > 0L && sequenceNumber > expectedCaptureSequence) {
            val missedFrames = sequenceNumber - expectedCaptureSequence
            totalDroppedFrames += missedFrames
            totalTimelineGaps++

            val durationMs = if (lastFrameTimestampMs > 0L) timestampEpochMs - lastFrameTimestampMs else 0L
            val gap = TimelineGap(
                startSequence = expectedCaptureSequence,
                endSequence = sequenceNumber - 1L,
                durationMs = durationMs,
                reason = "VirtualDisplay buffer drop or backpressure: $missedFrames frame(s) skipped",
                timestampEpochMs = timestampEpochMs
            )
            lastRecordedGap = gap
        }

        expectedCaptureSequence = sequenceNumber + 1L
        lastFrameTimestampMs = timestampEpochMs
        publishSnapshot(now)
    }

    /**
     * Records an uploaded/dispatched frame after perceptual diff filtering.
     */
    @Synchronized
    fun recordUploadFrame() {
        val now = System.currentTimeMillis()
        uploadTimestamps.addLast(now)
        publishSnapshot(now)
    }

    /**
     * Records an ingested frame acknowledged by backend ingestion queue.
     */
    @Synchronized
    fun recordIngestFrame() {
        val now = System.currentTimeMillis()
        ingestTimestamps.addLast(now)
        publishSnapshot(now)
    }

    /**
     * Records a completed analysis/inference step from multimodal perception.
     */
    @Synchronized
    fun recordAnalysisFrame() {
        val now = System.currentTimeMillis()
        analysisTimestamps.addLast(now)
        publishSnapshot(now)
    }

    /**
     * Records an audio chunk transmitted.
     */
    @Synchronized
    fun recordAudioChunk() {
        totalAudioChunks++
        publishSnapshot(System.currentTimeMillis())
    }

    /**
     * Records end-to-end round-trip latency in ms.
     */
    @Synchronized
    fun recordLatency(latencyMs: Long) {
        currentEndToEndLatencyMs = latencyMs
        publishSnapshot(System.currentTimeMillis())
    }

    /**
     * Updates paused state of screen capture.
     */
    @Synchronized
    fun setScreenPaused(paused: Boolean) {
        isScreenPaused = paused
        publishSnapshot(System.currentTimeMillis())
    }

    /**
     * Updates muted state of audio awareness.
     */
    @Synchronized
    fun setAudioMuted(muted: Boolean) {
        isAudioMuted = muted
        publishSnapshot(System.currentTimeMillis())
    }

    private fun startMetricsTicker() {
        tickerJob?.cancel()
        tickerJob = scope.launch(Dispatchers.Default) {
            while (isActive) {
                delay(250L) // Refresh metrics 4 times per second
                synchronized(this@MetricsTracker) {
                    publishSnapshot(System.currentTimeMillis())
                }
            }
        }
    }

    private fun calculateRollingFps(deque: ArrayDeque<Long>, now: Long): Float {
        val cutoff = now - windowDurationMs
        while (deque.isNotEmpty() && deque.first < cutoff) {
            deque.removeFirst()
        }
        val count = deque.size
        return if (windowDurationMs > 0L) {
            (count.toFloat() * 1000.0f) / windowDurationMs.toFloat()
        } else {
            0.0f
        }
    }

    private fun publishSnapshot(now: Long) {
        val capFps = calculateRollingFps(captureTimestamps, now)
        val upFps = calculateRollingFps(uploadTimestamps, now)
        val inFps = calculateRollingFps(ingestTimestamps, now)
        val anFps = calculateRollingFps(analysisTimestamps, now)

        val duration = now - sessionStartTimeMs

        _metrics.value = AwarenessMetrics(
            captureFps = capFps,
            uploadFps = upFps,
            ingestFps = inFps,
            analysisFps = anFps,
            droppedFramesCount = totalDroppedFrames,
            timelineGapsCount = totalTimelineGaps,
            lastGap = lastRecordedGap,
            endToEndLatencyMs = currentEndToEndLatencyMs,
            audioChunksTransmitted = totalAudioChunks,
            activeProfileId = currentProfileId,
            sessionDurationMs = duration,
            isScreenPaused = isScreenPaused,
            isAudioMuted = isAudioMuted
        )
    }

    fun stop() {
        tickerJob?.cancel()
        tickerJob = null
    }
}
