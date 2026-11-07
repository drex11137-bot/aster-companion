package com.astercompanion.android.awareness

import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.Image
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.os.Handler
import android.os.HandlerThread
import android.os.Process
import android.util.Log
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import java.nio.ByteBuffer
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicLong
import java.util.zip.CRC32

/**
 * Native Android Screen Capture Engine for Aster Companion.
 * Adheres strictly to PRD v1.1 §5 & §13:
 * - Manages VirtualDisplay & ImageReader (PixelFormat.RGBA_8888).
 * - Implements adaptive frame sampling (pHash/SSIM differencing).
 * - Never blindly streams static frames.
 * - Integrates with MetricsTracker for separate FPS measurements.
 * - Detects frame drops and sequence gaps without faking continuity.
 */
class ScreenCaptureEngine {

    companion object {
        private const val TAG = "ScreenCaptureEngine"
        private const val VIRTUAL_DISPLAY_NAME = "AsterScreenCapture"
        private const val IMAGE_READER_MAX_IMAGES = 3
    }

    private var virtualDisplay: VirtualDisplay? = null
    private var imageReader: ImageReader? = null
    private var handlerThread: HandlerThread? = null
    private var backgroundHandler: Handler? = null

    private val isRunning = AtomicBoolean(false)
    private val isPaused = AtomicBoolean(false)
    private val sequenceCounter = AtomicLong(0L)

    private var differencer = PerceptualDifferencer()
    private var metricsTracker: MetricsTracker? = null

    private val _frameFlow = MutableSharedFlow<CapturedFrame>(
        extraBufferCapacity = 16
    )
    val frameFlow: SharedFlow<CapturedFrame> = _frameFlow.asSharedFlow()

    /**
     * Starts screen capture using granted MediaProjection consent.
     *
     * @param mediaProjection Valid MediaProjection session from MediaProjectionManager.
     * @param config AwarenessConfig specifying dimensions, dpi, and differencing thresholds.
     * @param tracker Performance metrics tracker instance.
     */
    @Synchronized
    fun start(
        mediaProjection: MediaProjection,
        config: AwarenessConfig,
        tracker: MetricsTracker
    ) {
        if (isRunning.get()) {
            Log.w(TAG, "ScreenCaptureEngine is already running. Stopping existing session.")
            stop()
        }

        this.metricsTracker = tracker
        this.differencer = PerceptualDifferencer(
            pHashThreshold = config.pHashHammingThreshold,
            ssimThreshold = config.ssimChangeThreshold,
            heartbeatIntervalMs = config.heartbeatIntervalMs
        )
        sequenceCounter.set(0L)
        isPaused.set(false)

        Log.i(TAG, "Initializing VirtualDisplay ${config.targetWidth}x${config.targetHeight} @ ${config.targetDpi}dpi")

        // Dedicated background thread for image reader callbacks
        val thread = HandlerThread("AsterImageReaderThread", Process.THREAD_PRIORITY_DISPLAY).apply {
            start()
        }
        handlerThread = thread
        val handler = Handler(thread.looper)
        backgroundHandler = handler

        val reader = ImageReader.newInstance(
            config.targetWidth,
            config.targetHeight,
            PixelFormat.RGBA_8888,
            IMAGE_READER_MAX_IMAGES
        )
        imageReader = reader

        reader.setOnImageAvailableListener({ ir ->
            onImageAvailable(ir)
        }, handler)

        val vDisplay = mediaProjection.createVirtualDisplay(
            VIRTUAL_DISPLAY_NAME,
            config.targetWidth,
            config.targetHeight,
            config.targetDpi,
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
            reader.surface,
            null,
            handler
        )
        virtualDisplay = vDisplay
        isRunning.set(true)
        Log.i(TAG, "Screen capture successfully started.")
    }

    private fun onImageAvailable(reader: ImageReader) {
        var image: Image? = null
        try {
            image = reader.acquireLatestImage()
            if (image == null) return

            if (isPaused.get()) {
                return
            }

            val sequence = sequenceCounter.getAndIncrement()
            val timestampNs = System.nanoTime()
            val timestampEpochMs = System.currentTimeMillis()

            metricsTracker?.recordCaptureFrame(sequence, timestampEpochMs)

            val planes = image.planes
            if (planes.isEmpty()) return

            val plane = planes[0]
            val buffer = plane.buffer
            val pixelStride = plane.pixelStride
            val rowStride = plane.rowStride
            val width = image.width
            val height = image.height

            val tightlyPackedRgba = extractTightlyPackedRgba(buffer, width, height, pixelStride, rowStride)

            // Perceptual differencing & adaptive frame sampling
            val diffResult = differencer.evaluateFrame(
                rgbaBytes = tightlyPackedRgba,
                width = width,
                height = height,
                rowStride = width * 4,
                currentTimeMs = timestampEpochMs
            )

            if (diffResult.shouldDispatch) {
                val crc = CRC32()
                crc.update(tightlyPackedRgba)
                val checksum = crc.value

                val capturedFrame = CapturedFrame(
                    sequenceNumber = sequence,
                    timestampNs = timestampNs,
                    timestampEpochMs = timestampEpochMs,
                    width = width,
                    height = height,
                    stride = width * 4,
                    pixelFormat = PixelFormat.RGBA_8888,
                    perceptualHash = diffResult.pHash,
                    ssimScore = diffResult.ssimScore,
                    isKeyframe = diffResult.isMaterialTransition || diffResult.isHeartbeat,
                    rgbaBytes = tightlyPackedRgba,
                    checksum = checksum
                )

                metricsTracker?.recordUploadFrame()
                _frameFlow.tryEmit(capturedFrame)
            }
        } catch (t: Throwable) {
            Log.e(TAG, "Error acquiring or processing captured frame", t)
        } finally {
            try {
                image?.close()
            } catch (e: Exception) {
                Log.w(TAG, "Error closing ImageReader image", e)
            }
        }
    }

    /**
     * Extracts RGBA bytes removing GPU padding if rowStride > width * pixelStride.
     */
    private fun extractTightlyPackedRgba(
        buffer: ByteBuffer,
        width: Int,
        height: Int,
        pixelStride: Int,
        rowStride: Int
    ): ByteArray {
        val bytesPerPixel = 4
        val tightlyPackedSize = width * height * bytesPerPixel
        val result = ByteArray(tightlyPackedSize)

        buffer.rewind()

        if (rowStride == width * bytesPerPixel && pixelStride == bytesPerPixel) {
            buffer.get(result, 0, tightlyPackedSize.coerceAtMost(buffer.remaining()))
        } else {
            // Remove padding row by row
            val rowWidthInBytes = width * bytesPerPixel
            val rowBuffer = ByteArray(rowWidthInBytes)
            var destOffset = 0

            for (row in 0 until height) {
                buffer.position(row * rowStride)
                val bytesToRead = rowWidthInBytes.coerceAtMost(buffer.remaining())
                buffer.get(rowBuffer, 0, bytesToRead)
                System.arraycopy(rowBuffer, 0, result, destOffset, bytesToRead)
                destOffset += bytesToRead
            }
        }
        return result
    }

    /**
     * Pauses frame capture. VirtualDisplay continues running but frames are discarded,
     * halting transmission and updating awareness metrics.
     */
    fun pause() {
        if (isPaused.compareAndSet(false, true)) {
            Log.i(TAG, "Screen capture paused.")
            metricsTracker?.setScreenPaused(true)
        }
    }

    /**
     * Resumes frame capture and triggers an immediate keyframe on the next acquired frame.
     */
    fun resume() {
        if (isPaused.compareAndSet(true, false)) {
            Log.i(TAG, "Screen capture resumed.")
            differencer.reset()
            metricsTracker?.setScreenPaused(false)
        }
    }

    /**
     * Stops screen capture, releasing VirtualDisplay, ImageReader, and HandlerThread.
     */
    @Synchronized
    fun stop() {
        isRunning.set(false)
        isPaused.set(false)

        try {
            virtualDisplay?.release()
        } catch (e: Exception) {
            Log.w(TAG, "Error releasing VirtualDisplay", e)
        } finally {
            virtualDisplay = null
        }

        try {
            imageReader?.close()
        } catch (e: Exception) {
            Log.w(TAG, "Error closing ImageReader", e)
        } finally {
            imageReader = null
        }

        try {
            handlerThread?.quitSafely()
        } catch (e: Exception) {
            Log.w(TAG, "Error quitting ImageReader HandlerThread", e)
        } finally {
            handlerThread = null
            backgroundHandler = null
        }

        differencer.reset()
        Log.i(TAG, "Screen capture stopped and resources released.")
    }

    fun isRunning(): Boolean = isRunning.get()
    fun isPaused(): Boolean = isPaused.get()
}
