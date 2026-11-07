package com.astercompanion.android.data.crypto

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test
import java.io.ByteArrayInputStream

class ChecksumUtilTest {

    @Test
    fun testSha256OfKnownString() {
        val input = "Hello, Aster!"
        val hash = ChecksumUtil.computeSha256(input)
        // SHA-256 for "Hello, Aster!"
        assertFalse(hash.isEmpty())
        assertEquals(64, hash.length) // 256 bits = 64 hex characters
        assertEquals(hash, ChecksumUtil.computeSha256(input))
    }

    @Test
    fun testSha256OfEmptyString() {
        val hash = ChecksumUtil.computeSha256("")
        // Known SHA-256 of empty string: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
        assertEquals("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", hash)
    }

    @Test
    fun testSha256OfInputStream() {
        val data = "Continuous awareness stream payload data"
        val stream = ByteArrayInputStream(data.toByteArray(Charsets.UTF_8))
        val streamHash = ChecksumUtil.computeSha256(stream)
        val stringHash = ChecksumUtil.computeSha256(data)
        assertEquals(stringHash, streamHash)
    }

    @Test
    fun testVerifyChecksumSuccessAndFailure() {
        val payload = "{\"action\": \"send_message\", \"text\": \"Good evening!\"}"
        val checksum = ChecksumUtil.computeSha256(payload)

        assertTrue(ChecksumUtil.verifyChecksum(payload, checksum))
        assertTrue(ChecksumUtil.verifyChecksum(payload, checksum.uppercase())) // case-insensitive hex

        // Tampered payload
        val tamperedPayload = "{\"action\": \"send_message\", \"text\": \"Bad evening!\"}"
        assertFalse(ChecksumUtil.verifyChecksum(tamperedPayload, checksum))
    }

    @Test
    fun testCanonicalEventChecksum() {
        val deviceId = "device_pixel_9_pro"
        val seqNumber = 1042L
        val payload = "{\"frame_id\": 88210, \"fps\": 120}"

        val checksum1 = ChecksumUtil.computeEventChecksum(deviceId, seqNumber, payload)
        val checksum2 = ChecksumUtil.computeEventChecksum(deviceId, seqNumber, payload)
        assertEquals(checksum1, checksum2)

        // Changing sequence number produces completely different checksum
        val checksumDifferentSeq = ChecksumUtil.computeEventChecksum(deviceId, seqNumber + 1L, payload)
        assertNotEquals(checksum1, checksumDifferentSeq)

        // Changing device ID produces completely different checksum
        val checksumDifferentDevice = ChecksumUtil.computeEventChecksum("other_device", seqNumber, payload)
        assertNotEquals(checksum1, checksumDifferentDevice)
    }
}
