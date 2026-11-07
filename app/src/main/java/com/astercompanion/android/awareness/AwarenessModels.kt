package com.astercompanion.android.awareness

import java.nio.ByteBuffer

/**
 * Operating status of the Awareness subsystem.
 * Adheres strictly to PRD v1.1 §5 & §13:
 * Continuous awareness must accurately indicate its current operating state.
 */
enum class AwarenessStatus {
    IDLE,
    INITIALIZING,
    ACTIVE,
    PAUSED,
    MUTED,
    REVOKED,
    ERROR
}

/**
 * Supported audio awareness capture modes.
 * Dual-mode audio supports environmental mic and/or in-device playback.
 */
enum class AudioCaptureMode {
    NONE,
    ENVIRONMENTAL_MIC,
    IN_DEVICE_PLAYBACK,
    DUAL
}

/**
 * Structured audio chunk dispatched by the AudioAwarenessEngine.
 * Contains monotonic sequence numbering, timestamps, CRC32 checksum, and raw PCM data.
 */
data class AudioChunk(
    val sequenceNumber: Long,
    val timestampNs: Long,
    val timestampEpochMs: Long,
    val mode: AudioCaptureMode,
    val sampleRate: Int,
    val channelCount: Int,
    val pcmData: ByteArray,
    val durationMs: Long,
    val checksum: Long,
    val isMuted: Boolean = false
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false

        other as AudioChunk
        if (sequenceNumber != other.sequenceNumber) return false
        if (timestampNs != other.timestampNs) return false
        if (checksum != other.checksum) return false
        return pcmData.contentEquals(other.pcmData)
    }

    override fun hashCode(): Int {
        var result = sequenceNumber.hashCode()
        result = 31 * result + timestampNs.hashCode()
        result = 31 * result + checksum.hashCode()
        return result
    }
}

/**
 * Structured frame captured by ScreenCaptureEngine.
 * Includes perceptual hash, SSIM difference score, keyframe flag, and checksum.
 */
data class CapturedFrame(
    val sequenceNumber: Long,
    val timestampNs: Long,
    val timestampEpochMs: Long,
    val width: Int,
    val height: Int,
    val stride: Int,
    val pixelFormat: Int,
    val perceptualHash: Long,
    val ssimScore: Float,
    val isKeyframe: Boolean,
    val rgbaBytes: ByteArray,
    val checksum: Long
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false

        other as CapturedFrame
        if (sequenceNumber != other.sequenceNumber) return false
        if (timestampNs != other.timestampNs) return false
        if (checksum != other.checksum) return false
        return rgbaBytes.contentEquals(other.rgbaBytes)
    }

    override fun hashCode(): Int {
        var result = sequenceNumber.hashCode()
        result = 31 * result + timestampNs.hashCode()
        result = 31 * result + checksum.hashCode()
        return result
    }
}

/**
 * Represents an explicit gap in captured context.
 * As mandated by PRD §5 & §6: Aster never invents missing frames or false continuity;
 * missing intervals are accurately detected and reported.
 */
data class TimelineGap(
    val startSequence: Long,
    val endSequence: Long,
    val durationMs: Long,
    val reason: String,
    val timestampEpochMs: Long
)

/**
 * Separate real-time performance instrumentation metrics.
 * PRD §5.3 explicitly requires tracking capture, upload, ingest, and analysis FPS separately.
 */
data class AwarenessMetrics(
    val captureFps: Float = 0.0f,
    val uploadFps: Float = 0.0f,
    val ingestFps: Float = 0.0f,
    val analysisFps: Float = 0.0f,
    val droppedFramesCount: Long = 0L,
    val timelineGapsCount: Long = 0L,
    val lastGap: TimelineGap? = null,
    val endToEndLatencyMs: Long = 0L,
    val audioChunksTransmitted: Long = 0L,
    val activeProfileId: String = "profile_aster",
    val sessionDurationMs: Long = 0L,
    val isScreenPaused: Boolean = false,
    val isAudioMuted: Boolean = false
)

/**
 * Configuration options for screen & audio awareness session.
 */
data class AwarenessConfig(
    val targetWidth: Int = 1080,
    val targetHeight: Int = 2400,
    val targetDpi: Int = 420,
    val captureFpsLimit: Int = 60,
    val audioSampleRate: Int = 16000,
    val audioMode: AudioCaptureMode = AudioCaptureMode.DUAL,
    val ssimChangeThreshold: Float = 0.96f,
    val pHashHammingThreshold: Int = 4,
    val heartbeatIntervalMs: Long = 3000L,
    val enableOverlayIndicator: Boolean = true
)
