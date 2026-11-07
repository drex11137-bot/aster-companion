package com.astercompanion.android.awareness

import kotlin.math.sqrt

/**
 * High-performance perceptual frame difference evaluator.
 * Implements perceptual hashing (pHash) and Structural Similarity Index (SSIM)
 * to support adaptive frame sampling per PRD v1.1 §5.4.
 *
 * Prevents streaming static frames while ensuring material UI transitions
 * and user interactions are immediately dispatched.
 */
class PerceptualDifferencer(
    private val pHashThreshold: Int = 4,
    private val ssimThreshold: Float = 0.96f,
    private val heartbeatIntervalMs: Long = 3000L
) {

    data class DiffResult(
        val pHash: Long,
        val hammingDistance: Int,
        val ssimScore: Float,
        val isMaterialTransition: Boolean,
        val isHeartbeat: Boolean,
        val shouldDispatch: Boolean
    )

    private var lastKeyframeHash: Long? = null
    private var lastKeyframeLuminance: FloatArray? = null
    private var lastKeyframeTimestampMs: Long = 0L

    /**
     * Resets the differencing state, e.g., on awareness session restart or resume.
     */
    @Synchronized
    fun reset() {
        lastKeyframeHash = null
        lastKeyframeLuminance = null
        lastKeyframeTimestampMs = 0L
    }

    /**
     * Evaluates a frame against the last dispatched keyframe.
     *
     * @param rgbaBytes Raw RGBA_8888 byte array.
     * @param width Frame width.
     * @param height Frame height.
     * @param rowStride Row stride in bytes (may include row padding).
     * @param currentTimeMs Monotonic or wall-clock timestamp of this frame.
     * @return DiffResult containing metrics and dispatch decision.
     */
    @Synchronized
    fun evaluateFrame(
        rgbaBytes: ByteArray,
        width: Int,
        height: Int,
        rowStride: Int,
        currentTimeMs: Long
    ): DiffResult {
        val currentLuminanceGrid = sampleLuminanceGrid(rgbaBytes, width, height, rowStride, 8)
        val currentHash = computePHashFromGrid(currentLuminanceGrid)

        val previousHash = lastKeyframeHash
        val previousLuminance = lastKeyframeLuminance
        val timeSinceLastKeyframe = currentTimeMs - lastKeyframeTimestampMs

        // First frame is always a keyframe
        if (previousHash == null || previousLuminance == null) {
            lastKeyframeHash = currentHash
            lastKeyframeLuminance = currentLuminanceGrid
            lastKeyframeTimestampMs = currentTimeMs
            return DiffResult(
                pHash = currentHash,
                hammingDistance = 0,
                ssimScore = 1.0f,
                isMaterialTransition = true,
                isHeartbeat = false,
                shouldDispatch = true
            )
        }

        val hamming = computeHammingDistance(previousHash, currentHash)
        val ssim = computeSSIM(previousLuminance, currentLuminanceGrid)

        val isHeartbeat = timeSinceLastKeyframe >= heartbeatIntervalMs
        val isMaterialTransition = hamming >= pHashThreshold || ssim <= ssimThreshold
        val shouldDispatch = isMaterialTransition || isHeartbeat

        if (shouldDispatch) {
            lastKeyframeHash = currentHash
            lastKeyframeLuminance = currentLuminanceGrid
            lastKeyframeTimestampMs = currentTimeMs
        }

        return DiffResult(
            pHash = currentHash,
            hammingDistance = hamming,
            ssimScore = ssim,
            isMaterialTransition = isMaterialTransition,
            isHeartbeat = isHeartbeat,
            shouldDispatch = shouldDispatch
        )
    }

    /**
     * Computes 64-bit perceptual hash (pHash) from downsampled 8x8 luminance grid.
     */
    fun computePHashFromGrid(grid: FloatArray): Long {
        require(grid.size == 64) { "Grid size must be 64 for 8x8 pHash" }
        var sum = 0.0f
        for (i in 0 until 64) {
            sum += grid[i]
        }
        val avg = sum / 64.0f

        var hash = 0L
        for (i in 0 until 64) {
            if (grid[i] >= avg) {
                hash = hash or (1L shl i)
            }
        }
        return hash
    }

    /**
     * Computes Hamming distance between two 64-bit pHashes.
     */
    fun computeHammingDistance(hash1: Long, hash2: Long): Int {
        return java.lang.Long.bitCount(hash1 xor hash2)
    }

    /**
     * Computes Structural Similarity Index (SSIM) between two normalized luminance grids.
     * Returns a value between -1.0 and 1.0 (typically 0.0 to 1.0 for valid images).
     */
    fun computeSSIM(gridA: FloatArray, gridB: FloatArray): Float {
        require(gridA.size == gridB.size) { "Grids must have the same size" }
        val n = gridA.size
        if (n == 0) return 1.0f

        var sumA = 0.0f
        var sumB = 0.0f
        for (i in 0 until n) {
            sumA += gridA[i]
            sumB += gridB[i]
        }
        val meanA = sumA / n
        val meanB = sumB / n

        var varA = 0.0f
        var varB = 0.0f
        var covAB = 0.0f
        for (i in 0 until n) {
            val diffA = gridA[i] - meanA
            val diffB = gridB[i] - meanB
            varA += diffA * diffA
            varB += diffB * diffB
            covAB += diffA * diffB
        }
        val denomN = if (n > 1) (n - 1).toFloat() else 1.0f
        varA /= denomN
        varB /= denomN
        covAB /= denomN

        // Constants to stabilize the division with weak denominator
        val c1 = 6.5025f // (0.01 * 255)^2
        val c2 = 58.5225f // (0.03 * 255)^2

        val numerator = (2.0f * meanA * meanB + c1) * (2.0f * covAB + c2)
        val denominator = (meanA * meanA + meanB * meanB + c1) * (varA + varB + c2)

        return (numerator / denominator).coerceIn(0.0f, 1.0f)
    }

    /**
     * Fast downsampling of RGBA_8888 buffer to an N x N luminance grid (default 8x8).
     */
    fun sampleLuminanceGrid(
        rgbaBytes: ByteArray,
        width: Int,
        height: Int,
        rowStride: Int,
        dim: Int = 8
    ): FloatArray {
        val grid = FloatArray(dim * dim)
        val blockWidth = width / dim
        val blockHeight = height / dim

        if (blockWidth <= 0 || blockHeight <= 0) {
            return grid
        }

        for (by in 0 until dim) {
            val sampleY = (by * blockHeight) + (blockHeight / 2)
            val rowOffset = sampleY * rowStride
            for (bx in 0 until dim) {
                val sampleX = (bx * blockWidth) + (blockWidth / 2)
                val pixelOffset = rowOffset + (sampleX * 4)

                if (pixelOffset + 2 < rgbaBytes.size) {
                    val r = rgbaBytes[pixelOffset].toInt() and 0xFF
                    val g = rgbaBytes[pixelOffset + 1].toInt() and 0xFF
                    val b = rgbaBytes[pixelOffset + 2].toInt() and 0xFF
                    // Standard luminance formula
                    val lum = 0.299f * r + 0.587f * g + 0.114f * b
                    grid[by * dim + bx] = lum
                }
            }
        }
        return grid
    }
}
