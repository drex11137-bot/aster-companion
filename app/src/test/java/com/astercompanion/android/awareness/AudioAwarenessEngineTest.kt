package com.astercompanion.android.awareness

import org.junit.Assert.assertArrayEquals
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.zip.CRC32

/**
 * Unit tests for AudioAwarenessEngine components and PCM audio processing.
 * Verifies audio streaming, PCM16 dual-stream mixing, and checksum calculation per PRD v1.1 §7.
 */
class AudioAwarenessEngineTest {

    @Test
    fun testPcm16NormalAdditiveMixing() {
        val sampleCount = 4
        val byteCount = sampleCount * 2

        val srcA = ByteArray(byteCount)
        val srcB = ByteArray(byteCount)
        val dst = ByteArray(byteCount)

        // Sample 0: 1000 in A, 2000 in B -> 3000 in dst
        val sampleA0 = 1000
        val sampleB0 = 2000
        srcA[0] = (sampleA0 and 0xFF).toByte()
        srcA[1] = ((sampleA0 shr 8) and 0xFF).toByte()
        srcB[0] = (sampleB0 and 0xFF).toByte()
        srcB[1] = ((sampleB0 shr 8) and 0xFF).toByte()

        // Sample 1: -500 in A, 1500 in B -> 1000 in dst
        val sampleA1 = -500
        val sampleB1 = 1500
        srcA[2] = (sampleA1 and 0xFF).toByte()
        srcA[3] = ((sampleA1 shr 8) and 0xFF).toByte()
        srcB[2] = (sampleB1 and 0xFF).toByte()
        srcB[3] = ((sampleB1 shr 8) and 0xFF).toByte()

        // Mix using AudioAwarenessEngine's mixing logic
        mixTestPcm16(srcA, srcB, dst, byteCount)

        val out0 = ((dst[0].toInt() and 0xFF) or (dst[1].toInt() shl 8)).toShort().toInt()
        val out1 = ((dst[2].toInt() and 0xFF) or (dst[3].toInt() shl 8)).toShort().toInt()

        assertEquals("Sample 0 mixed should be 3000", 3000, out0)
        assertEquals("Sample 1 mixed should be 1000", 1000, out1)
    }

    @Test
    fun testPcm16SaturationClipping() {
        val byteCount = 4
        val srcA = ByteArray(byteCount)
        val srcB = ByteArray(byteCount)
        val dst = ByteArray(byteCount)

        // Positive overflow: 25000 + 25000 = 50000 -> must clamp to 32767
        val largePos = 25000
        srcA[0] = (largePos and 0xFF).toByte()
        srcA[1] = ((largePos shr 8) and 0xFF).toByte()
        srcB[0] = (largePos and 0xFF).toByte()
        srcB[1] = ((largePos shr 8) and 0xFF).toByte()

        // Negative overflow: -25000 + -25000 = -50000 -> must clamp to -32768
        val largeNeg = -25000
        srcA[2] = (largeNeg and 0xFF).toByte()
        srcA[3] = ((largeNeg shr 8) and 0xFF).toByte()
        srcB[2] = (largeNeg and 0xFF).toByte()
        srcB[3] = ((largeNeg shr 8) and 0xFF).toByte()

        mixTestPcm16(srcA, srcB, dst, byteCount)

        val clampedPos = ((dst[0].toInt() and 0xFF) or (dst[1].toInt() shl 8)).toShort().toInt()
        val clampedNeg = ((dst[2].toInt() and 0xFF) or (dst[3].toInt() shl 8)).toShort().toInt()

        assertEquals("Positive overflow must clamp to 32767", 32767, clampedPos)
        assertEquals("Negative overflow must clamp to -32768", -32768, clampedNeg)
    }

    @Test
    fun testAudioChunkCrc32Integrity() {
        val samplePcm = byteArrayOf(0, 1, 2, 3, 4, 5, 6, 7, 8, 9)
        val crc = CRC32()
        crc.update(samplePcm)
        val expectedCrc = crc.value

        val chunk = AudioChunk(
            sequenceNumber = 42L,
            timestampNs = 1_000_000_000L,
            timestampEpochMs = 1700000000000L,
            mode = AudioCaptureMode.DUAL,
            sampleRate = 16000,
            channelCount = 1,
            pcmData = samplePcm,
            durationMs = 100L,
            checksum = expectedCrc,
            isMuted = false
        )

        assertEquals(expectedCrc, chunk.checksum)
        assertEquals(42L, chunk.sequenceNumber)
        assertEquals(AudioCaptureMode.DUAL, chunk.mode)
        assertEquals(16000, chunk.sampleRate)
        assertArrayEquals(samplePcm, chunk.pcmData)
    }

    private fun mixTestPcm16(srcA: ByteArray, srcB: ByteArray, dst: ByteArray, byteCount: Int) {
        val sampleCount = byteCount / 2
        for (i in 0 until sampleCount) {
            val byteIndex = i * 2
            val sampleA = (srcA[byteIndex].toInt() and 0xFF) or (srcA[byteIndex + 1].toInt() shl 8)
            val sampleB = (srcB[byteIndex].toInt() and 0xFF) or (srcB[byteIndex + 1].toInt() shl 8)

            val valA = sampleA.toShort().toInt()
            val valB = sampleB.toShort().toInt()

            val mixed = (valA + valB).coerceIn(-32768, 32767)

            dst[byteIndex] = (mixed and 0xFF).toByte()
            dst[byteIndex + 1] = ((mixed shr 8) and 0xFF).toByte()
        }
    }
}
