package com.astercompanion.android.awareness

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

/**
 * Unit tests for PerceptualDifferencer.
 * Verifies adaptive frame sampling per PRD v1.1 §5.4:
 * - Detects static frames and avoids redundant transmissions.
 * - Dispatches immediately upon material UI transitions.
 * - Dispatches heartbeat keyframes periodically.
 * - Computes accurate SSIM and pHash Hamming distances.
 */
class PerceptualDifferencerTest {

    private lateinit var differencer: PerceptualDifferencer

    @Before
    fun setUp() {
        differencer = PerceptualDifferencer(
            pHashThreshold = 4,
            ssimThreshold = 0.96f,
            heartbeatIntervalMs = 3000L
        )
    }

    private fun createSolidRgbaFrame(width: Int, height: Int, r: Int, g: Int, b: Int): ByteArray {
        val bytes = ByteArray(width * height * 4)
        for (i in 0 until width * height) {
            val offset = i * 4
            bytes[offset] = r.toByte()
            bytes[offset + 1] = g.toByte()
            bytes[offset + 2] = b.toByte()
            bytes[offset + 3] = 255.toByte()
        }
        return bytes
    }

    @Test
    fun testFirstFrameAlwaysDispatchedAsKeyframe() {
        val frame = createSolidRgbaFrame(64, 64, 255, 255, 255)
        val result = differencer.evaluateFrame(frame, 64, 64, 64 * 4, 1000L)

        assertTrue("First frame must always be dispatched", result.shouldDispatch)
        assertTrue("First frame must be flagged as material transition / keyframe", result.isMaterialTransition)
        assertEquals("Initial Hamming distance is 0", 0, result.hammingDistance)
        assertEquals("Initial SSIM score is 1.0", 1.0f, result.ssimScore, 0.001f)
    }

    @Test
    fun testIdenticalFramesNotDispatchedBeforeHeartbeat() {
        val frame = createSolidRgbaFrame(64, 64, 100, 100, 100)

        // First frame
        val res1 = differencer.evaluateFrame(frame, 64, 64, 64 * 4, 1000L)
        assertTrue(res1.shouldDispatch)

        // Second identical frame 50ms later
        val res2 = differencer.evaluateFrame(frame, 64, 64, 64 * 4, 1050L)
        assertFalse("Static identical frame must not be dispatched", res2.shouldDispatch)
        assertEquals("Hamming distance between identical frames is 0", 0, res2.hammingDistance)
        assertEquals("SSIM between identical frames is 1.0", 1.0f, res2.ssimScore, 0.001f)
    }

    @Test
    fun testHeartbeatDispatchedWhenScreenIsStaticAfterInterval() {
        val frame = createSolidRgbaFrame(64, 64, 50, 50, 50)

        // First frame at t = 1000ms
        differencer.evaluateFrame(frame, 64, 64, 64 * 4, 1000L)

        // Identical frame at t = 2000ms (1000ms elapsed, less than 3000ms heartbeat)
        val res2 = differencer.evaluateFrame(frame, 64, 64, 64 * 4, 2000L)
        assertFalse("Frame before heartbeat interval must not be dispatched", res2.shouldDispatch)

        // Identical frame at t = 4500ms (3500ms elapsed, exceeds 3000ms heartbeat)
        val res3 = differencer.evaluateFrame(frame, 64, 64, 64 * 4, 4500L)
        assertTrue("Heartbeat frame must be dispatched after heartbeat interval", res3.shouldDispatch)
        assertTrue("Dispatch must be flagged as heartbeat", res3.isHeartbeat)
        assertFalse("Static heartbeat is not a material UI transition", res3.isMaterialTransition)
    }

    @Test
    fun testMaterialUiTransitionTriggersImmediateDispatch() {
        val whiteFrame = createSolidRgbaFrame(64, 64, 255, 255, 255)
        differencer.evaluateFrame(whiteFrame, 64, 64, 64 * 4, 1000L)

        // Material transition: frame with high contrast checkerboard pattern
        val patternedFrame = ByteArray(64 * 64 * 4)
        for (y in 0 until 64) {
            for (x in 0 until 64) {
                val offset = (y * 64 + x) * 4
                val isDark = ((x / 8) + (y / 8)) % 2 == 0
                val c = if (isDark) 0.toByte() else 255.toByte()
                patternedFrame[offset] = c
                patternedFrame[offset + 1] = c
                patternedFrame[offset + 2] = c
                patternedFrame[offset + 3] = 255.toByte()
            }
        }

        val result = differencer.evaluateFrame(patternedFrame, 64, 64, 64 * 4, 1050L)
        assertTrue("Material UI transition must be dispatched immediately", result.shouldDispatch)
        assertTrue("Material transition flag must be true", result.isMaterialTransition)
        assertTrue("SSIM should be significantly degraded", result.ssimScore < 0.96f)
    }

    @Test
    fun testResetClearsKeyframeMemory() {
        val frame = createSolidRgbaFrame(64, 64, 128, 128, 128)
        differencer.evaluateFrame(frame, 64, 64, 64 * 4, 1000L)

        differencer.reset()

        // After reset, next frame should be treated as first frame (dispatched immediately)
        val resAfterReset = differencer.evaluateFrame(frame, 64, 64, 64 * 4, 1100L)
        assertTrue("After reset, frame must be dispatched as initial keyframe", resAfterReset.shouldDispatch)
        assertTrue(resAfterReset.isMaterialTransition)
    }

    @Test
    fun testSsimCalculationLimits() {
        val gridA = FloatArray(64) { 100.0f }
        val gridB = FloatArray(64) { 100.0f }
        val ssimIdentical = differencer.computeSSIM(gridA, gridB)
        assertEquals("SSIM of identical grids should be 1.0", 1.0f, ssimIdentical, 0.001f)

        val gridC = FloatArray(64) { 0.0f }
        val gridD = FloatArray(64) { 255.0f }
        val ssimDivergent = differencer.computeSSIM(gridC, gridD)
        assertTrue("SSIM of opposite grids should be close to 0.0", ssimDivergent < 0.1f)
    }
}
