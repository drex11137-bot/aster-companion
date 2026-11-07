package com.astercompanion.android.model

/**
 * Models for Continuous Awareness subsystem in Aster Companion.
 * Adheres strictly to PRD v1.1 §5 & §13:
 * - Distinguishes Capture FPS (target up to 120 FPS), Upload FPS, and actual Analysis FPS.
 * - Enforces monotonic sequence numbers, timestamps, and checksums.
 * - Quick non-obstructive pause, stop, and mute controls.
 */

data class ScreenEvent(
    val id: String,
    val profileId: String,
    val timestamp: Long = System.currentTimeMillis(),
    val sequenceNumber: Long,
    val eventType: String = EVENT_TYPE_SCENE_CHANGE,
    val summary: String,
    val captureFps: Float = 120.0f,
    val uploadFps: Float = 30.0f,
    val analysisFps: Float = 5.0f,
    val checksum: String = ""
) {
    companion object {
        const val EVENT_TYPE_SCENE_CHANGE = "SCENE_CHANGE"
        const val EVENT_TYPE_USER_INPUT = "USER_INPUT"
        const val EVENT_TYPE_APP_TRANSITION = "APP_TRANSITION"
        const val EVENT_TYPE_TEXT_DETECTED = "TEXT_DETECTED"
        const val EVENT_TYPE_PERIODIC_SAMPLE = "PERIODIC_SAMPLE"
    }
}

data class AwarenessState(
    val activeProfileId: String,
    val isCaptureActive: Boolean = true,
    val isPaused: Boolean = false,
    val isStopped: Boolean = false,
    val isMuted: Boolean = false,
    val captureFps: Float = 120.0f,   // Aspirational screen capture rate
    val uploadFps: Float = 30.0f,     // Network transport rate
    val analysisFps: Float = 5.0f,    // Multimodal AI reasoning / inference rate
    val lastEventTimestamp: Long = 0L,
    val totalEventsCaptured: Long = 0L,
    val totalGapsDetected: Int = 0,
    val connectionStatus: String = "Active (Connected)"
)
