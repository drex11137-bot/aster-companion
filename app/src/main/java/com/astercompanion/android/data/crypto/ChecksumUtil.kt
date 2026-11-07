package com.astercompanion.android.data.crypto

import java.io.InputStream
import java.nio.charset.StandardCharsets
import java.security.MessageDigest

/**
 * Cryptographic checksum utility for data integrity and idempotent synchronization (PRD v1.1 §6.3, §14).
 * Uses SHA-256 with constant-time equality comparisons to prevent timing attacks.
 */
object ChecksumUtil {

    private const val ALGORITHM_SHA256 = "SHA-256"

    /**
     * Computes the SHA-256 hash of a byte array and returns lowercase hex string.
     */
    fun computeSha256(bytes: ByteArray): String {
        val digest = MessageDigest.getInstance(ALGORITHM_SHA256)
        val hash = digest.digest(bytes)
        return bytesToHex(hash)
    }

    /**
     * Computes the SHA-256 hash of a UTF-8 string and returns lowercase hex string.
     */
    fun computeSha256(text: String): String {
        return computeSha256(text.toByteArray(StandardCharsets.UTF_8))
    }

    /**
     * Computes the SHA-256 hash of an InputStream and returns lowercase hex string.
     */
    fun computeSha256(inputStream: InputStream): String {
        val digest = MessageDigest.getInstance(ALGORITHM_SHA256)
        val buffer = ByteArray(8192)
        var bytesRead: Int
        while (inputStream.read(buffer).also { bytesRead = it } != -1) {
            digest.update(buffer, 0, bytesRead)
        }
        return bytesToHex(digest.digest())
    }

    /**
     * Verifies that the computed SHA-256 of text matches expectedChecksum using constant-time comparison.
     */
    fun verifyChecksum(text: String, expectedChecksum: String): Boolean {
        return verifyChecksum(text.toByteArray(StandardCharsets.UTF_8), expectedChecksum)
    }

    /**
     * Verifies that the computed SHA-256 of bytes matches expectedChecksum using constant-time comparison.
     */
    fun verifyChecksum(bytes: ByteArray, expectedChecksum: String): Boolean {
        val computedHex = computeSha256(bytes)
        return MessageDigest.isEqual(
            computedHex.toByteArray(StandardCharsets.UTF_8),
            expectedChecksum.lowercase().toByteArray(StandardCharsets.UTF_8)
        )
    }

    /**
     * Computes canonical event checksum combining device ID, sequence number, and payload hash.
     * Guaranteed deterministic and tamper-evident across distributed nodes.
     */
    fun computeEventChecksum(deviceId: String, sequenceNumber: Long, payloadJson: String): String {
        val payloadHash = computeSha256(payloadJson)
        val canonicalRepresentation = "v1:$deviceId:$sequenceNumber:$payloadHash"
        return computeSha256(canonicalRepresentation)
    }

    private fun bytesToHex(bytes: ByteArray): String {
        val hexChars = CharArray(bytes.size * 2)
        val hexDigits = "0123456789abcdef".toCharArray()
        for (i in bytes.indices) {
            val v = bytes[i].toInt() and 0xFF
            hexChars[i * 2] = hexDigits[v ushr 4]
            hexChars[i * 2 + 1] = hexDigits[v and 0x0F]
        }
        return String(hexChars)
    }
}
