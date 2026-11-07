package com.astercompanion.android.awareness

import android.Manifest
import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioPlaybackCaptureConfiguration
import android.media.AudioRecord
import android.media.MediaRecorder
import android.media.projection.MediaProjection
import android.os.Build
import android.util.Log
import androidx.core.content.ContextCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.channels.BufferOverflow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicLong
import java.util.zip.CRC32

/**
 * Native Android Audio Awareness Engine for Aster Companion.
 * Adheres strictly to PRD v1.1 §5, §7 & §13:
 * - Dual audio mode:
 *   a) Environmental microphone (AudioRecord, 16kHz/24kHz 16-bit PCM mono).
 *   b) In-device audio capture via AudioPlaybackCaptureConfiguration (Android 10+) with opt-in permission check.
 * - Streaming buffer with chunk timestamps, sequence numbering, and CRC32 checksums.
 * - Instant mute / unmute action with continuity preservation.
 */
class AudioAwarenessEngine(
    private val context: Context,
    private val scope: CoroutineScope
) {

    companion object {
        private const val TAG = "AudioAwarenessEngine"
        const val CHUNK_DURATION_MS = 100L
    }

    private val isRunning = AtomicBoolean(false)
    private val isMuted = AtomicBoolean(false)
    private val sequenceCounter = AtomicLong(0L)

    private var micRecord: AudioRecord? = null
    private var playbackRecord: AudioRecord? = null
    private var recordingJob: Job? = null
    private var metricsTracker: MetricsTracker? = null

    private val _audioFlow = MutableSharedFlow<AudioChunk>(
        extraBufferCapacity = 64,
        onBufferOverflow = BufferOverflow.DROP_OLDEST
    )
    val audioFlow: SharedFlow<AudioChunk> = _audioFlow.asSharedFlow()

    /**
     * Starts audio capture based on requested mode and configuration.
     *
     * @param mediaProjection Active MediaProjection session (required for in-device playback capture).
     * @param mode AudioCaptureMode (ENVIRONMENTAL_MIC, IN_DEVICE_PLAYBACK, or DUAL).
     * @param sampleRate 16000 or 24000 Hz.
     * @param tracker Performance metrics tracker.
     */
    @Synchronized
    fun start(
        mediaProjection: MediaProjection?,
        mode: AudioCaptureMode,
        sampleRate: Int = 16000,
        tracker: MetricsTracker? = null
    ) {
        if (isRunning.get()) {
            Log.w(TAG, "AudioAwarenessEngine is already running. Stopping previous session.")
            stop()
        }

        this.metricsTracker = tracker
        sequenceCounter.set(0L)
        isMuted.set(false)

        if (mode == AudioCaptureMode.NONE) {
            Log.i(TAG, "Audio capture mode is NONE; audio awareness will remain idle.")
            return
        }

        // Initialize environmental mic if requested
        if (mode == AudioCaptureMode.ENVIRONMENTAL_MIC || mode == AudioCaptureMode.DUAL) {
            if (hasRecordAudioPermission()) {
                micRecord = createMicAudioRecord(sampleRate)
            } else {
                Log.w(TAG, "RECORD_AUDIO permission not granted; environmental mic capture disabled.")
            }
        }

        // Initialize in-device playback capture if requested
        if (mode == AudioCaptureMode.IN_DEVICE_PLAYBACK || mode == AudioCaptureMode.DUAL) {
            if (mediaProjection != null && Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                playbackRecord = createPlaybackAudioRecord(mediaProjection, sampleRate)
            } else {
                Log.w(TAG, "In-device playback capture unavailable: requires Android 10+ and valid MediaProjection consent.")
            }
        }

        val activeMic = micRecord
        val activePlayback = playbackRecord

        if (activeMic == null && activePlayback == null) {
            Log.e(TAG, "No audio record could be initialized for mode $mode.")
            return
        }

        isRunning.set(true)

        recordingJob = scope.launch(Dispatchers.IO) {
            runStreamingLoop(activeMic, activePlayback, sampleRate, mode)
        }
        Log.i(TAG, "AudioAwarenessEngine started with mode: $mode @ ${sampleRate}Hz")
    }

    private fun hasRecordAudioPermission(): Boolean {
        return ContextCompat.checkSelfPermission(
            context,
            Manifest.permission.RECORD_AUDIO
        ) == PackageManager.PERMISSION_GRANTED
    }

    @SuppressLint("MissingPermission")
    private fun createMicAudioRecord(sampleRate: Int): AudioRecord? {
        return try {
            val channelConfig = AudioFormat.CHANNEL_IN_MONO
            val audioFormat = AudioFormat.ENCODING_PCM_16BIT
            val minBufferSize = AudioRecord.getMinBufferSize(sampleRate, channelConfig, audioFormat)
            val chunkSize = calculateChunkByteSize(sampleRate)
            val bufferSize = maxOf(minBufferSize, chunkSize * 4)

            val record = AudioRecord(
                MediaRecorder.AudioSource.VOICE_RECOGNITION,
                sampleRate,
                channelConfig,
                audioFormat,
                bufferSize
            )

            if (record.state != AudioRecord.STATE_INITIALIZED) {
                Log.e(TAG, "Failed to initialize environmental mic AudioRecord")
                record.release()
                null
            } else {
                record
            }
        } catch (e: Exception) {
            Log.e(TAG, "Exception initializing mic AudioRecord", e)
            null
        }
    }

    private fun createPlaybackAudioRecord(mediaProjection: MediaProjection, sampleRate: Int): AudioRecord? {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) return null

        return try {
            val playbackConfig = AudioPlaybackCaptureConfiguration.Builder(mediaProjection)
                .addMatchingUsage(AudioAttributes.USAGE_MEDIA)
                .addMatchingUsage(AudioAttributes.USAGE_GAME)
                .addMatchingUsage(AudioAttributes.USAGE_UNKNOWN)
                .build()

            val audioFormat = AudioFormat.Builder()
                .setEncoding(AudioFormat.ENCODING_PCM_16BIT)
                .setSampleRate(sampleRate)
                .setChannelMask(AudioFormat.CHANNEL_IN_MONO)
                .build()

            val chunkSize = calculateChunkByteSize(sampleRate)
            val minBufferSize = AudioRecord.getMinBufferSize(sampleRate, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT)
            val bufferSize = maxOf(minBufferSize, chunkSize * 4)

            val record = AudioRecord.Builder()
                .setAudioPlaybackCaptureConfig(playbackConfig)
                .setAudioFormat(audioFormat)
                .setBufferSizeInBytes(bufferSize)
                .build()

            if (record.state != AudioRecord.STATE_INITIALIZED) {
                Log.e(TAG, "Failed to initialize in-device playback AudioRecord")
                record.release()
                null
            } else {
                record
            }
        } catch (e: Exception) {
            Log.e(TAG, "Exception initializing in-device playback AudioRecord", e)
            null
        }
    }

    private fun calculateChunkByteSize(sampleRate: Int): Int {
        val bytesPerSample = 2 // 16-bit PCM
        val samplesPerChunk = (sampleRate * CHUNK_DURATION_MS / 1000L).toInt()
        return samplesPerChunk * bytesPerSample
    }

    private suspend fun runStreamingLoop(
        mic: AudioRecord?,
        playback: AudioRecord?,
        sampleRate: Int,
        configuredMode: AudioCaptureMode
    ) {
        val chunkByteSize = calculateChunkByteSize(sampleRate)
        val micBuffer = ByteArray(chunkByteSize)
        val playbackBuffer = ByteArray(chunkByteSize)
        val combinedBuffer = ByteArray(chunkByteSize)

        try {
            mic?.startRecording()
            playback?.startRecording()
        } catch (e: Exception) {
            Log.e(TAG, "Error starting AudioRecord streams", e)
            return
        }

        while (scope.isActive && isRunning.get()) {
            val timestampNs = System.nanoTime()
            val timestampEpochMs = System.currentTimeMillis()
            val sequence = sequenceCounter.getAndIncrement()

            val muted = isMuted.get()
            var micBytesRead = 0
            var playbackBytesRead = 0

            if (mic != null) {
                micBytesRead = readFully(mic, micBuffer, chunkByteSize)
            }
            if (playback != null) {
                playbackBytesRead = readFully(playback, playbackBuffer, chunkByteSize)
            }

            if (micBytesRead <= 0 && playbackBytesRead <= 0) {
                continue
            }

            // Determine chunk payload
            val outputBytes: ByteArray
            if (muted) {
                // When muted, emit silent PCM data to preserve monotonic timeline without exposing private audio
                outputBytes = ByteArray(chunkByteSize)
            } else if (mic != null && playback != null) {
                // Mix mono streams linearly with soft saturation clipping
                mixPcm16(micBuffer, playbackBuffer, combinedBuffer, chunkByteSize)
                outputBytes = combinedBuffer.copyOf()
            } else if (mic != null) {
                outputBytes = micBuffer.copyOf()
            } else {
                outputBytes = playbackBuffer.copyOf()
            }

            val crc = CRC32()
            crc.update(outputBytes)
            val checksum = crc.value

            val chunk = AudioChunk(
                sequenceNumber = sequence,
                timestampNs = timestampNs,
                timestampEpochMs = timestampEpochMs,
                mode = configuredMode,
                sampleRate = sampleRate,
                channelCount = 1,
                pcmData = outputBytes,
                durationMs = CHUNK_DURATION_MS,
                checksum = checksum,
                isMuted = muted
            )

            metricsTracker?.recordAudioChunk()
            _audioFlow.tryEmit(chunk)
        }
    }

    private fun readFully(record: AudioRecord, buffer: ByteArray, targetSize: Int): Int {
        var totalRead = 0
        while (totalRead < targetSize && isRunning.get()) {
            val read = record.read(buffer, totalRead, targetSize - totalRead)
            if (read < 0) {
                Log.w(TAG, "AudioRecord read error code: $read")
                return totalRead
            }
            totalRead += read
        }
        return totalRead
    }

    /**
     * Mixes two 16-bit PCM mono byte buffers into an output buffer with saturation protection.
     */
    fun mixPcm16(srcA: ByteArray, srcB: ByteArray, dst: ByteArray, byteCount: Int) {
        val sampleCount = byteCount / 2
        for (i in 0 until sampleCount) {
            val byteIndex = i * 2
            val sampleA = (srcA[byteIndex].toInt() and 0xFF) or (srcA[byteIndex + 1].toInt() shl 8)
            val sampleB = (srcB[byteIndex].toInt() and 0xFF) or (srcB[byteIndex + 1].toInt() shl 8)

            // Sign-extend 16-bit to signed Int
            val valA = sampleA.toShort().toInt()
            val valB = sampleB.toShort().toInt()

            val mixed = (valA + valB).coerceIn(-32768, 32767)

            dst[byteIndex] = (mixed and 0xFF).toByte()
            dst[byteIndex + 1] = ((mixed shr 8) and 0xFF).toByte()
        }
    }

    /**
     * Mutes audio capture, preserving temporal sequence continuity with silent markers.
     */
    fun mute() {
        if (isMuted.compareAndSet(false, true)) {
            Log.i(TAG, "Audio awareness muted.")
            metricsTracker?.setAudioMuted(true)
        }
    }

    /**
     * Unmutes audio capture.
     */
    fun unmute() {
        if (isMuted.compareAndSet(true, false)) {
            Log.i(TAG, "Audio awareness unmuted.")
            metricsTracker?.setAudioMuted(false)
        }
    }

    /**
     * Stops audio streams and releases hardware AudioRecord instances.
     */
    @Synchronized
    fun stop() {
        isRunning.set(false)
        isMuted.set(false)

        recordingJob?.cancel()
        recordingJob = null

        try {
            micRecord?.stop()
            micRecord?.release()
        } catch (e: Exception) {
            Log.w(TAG, "Error stopping mic AudioRecord", e)
        } finally {
            micRecord = null
        }

        try {
            playbackRecord?.stop()
            playbackRecord?.release()
        } catch (e: Exception) {
            Log.w(TAG, "Error stopping playback AudioRecord", e)
        } finally {
            playbackRecord = null
        }

        Log.i(TAG, "AudioAwarenessEngine stopped and audio resources released.")
    }

    fun isRunning(): Boolean = isRunning.get()
    fun isMuted(): Boolean = isMuted.get()
}
