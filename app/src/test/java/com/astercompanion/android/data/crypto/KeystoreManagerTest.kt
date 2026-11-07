package com.astercompanion.android.data.crypto

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class KeystoreManagerTest {

    private lateinit var keystoreManager: KeystoreManager

    @Before
    fun setUp() {
        keystoreManager = KeystoreManager(useFallbackJce = true)
    }

    @Test
    fun testKeyGenerationAndExistence() {
        val alias = "test_companion_key"
        keystoreManager.deleteKey(alias)
        assertFalse(keystoreManager.hasKey(alias))

        val key = keystoreManager.getOrCreateKey(alias)
        assertNotNull(key)
        assertTrue(keystoreManager.hasKey(alias))

        // Subsequent call returns identical key
        val keyAgain = keystoreManager.getOrCreateKey(alias)
        assertEquals(key, keyAgain)
    }

    @Test
    fun testEncryptDecryptRoundTripBytes() {
        val alias = "byte_test_key"
        val originalPlaintext = "Sensitive companion memory: User prefers dark roast coffee".toByteArray(Charsets.UTF_8)

        val encryptedPayload = keystoreManager.encrypt(originalPlaintext, alias)
        assertNotNull(encryptedPayload.iv)
        assertEquals(12, encryptedPayload.iv.size)
        assertFalse(encryptedPayload.ciphertext.contentEquals(originalPlaintext))

        val decryptedBytes = keystoreManager.decrypt(encryptedPayload, alias)
        assertTrue(originalPlaintext.contentEquals(decryptedBytes))
        assertEquals(String(originalPlaintext, Charsets.UTF_8), String(decryptedBytes, Charsets.UTF_8))
    }

    @Test
    fun testCombinedPayloadRoundTrip() {
        val alias = "combined_key"
        val plaintext = "Personal reflections: slow morning on Saturday".toByteArray(Charsets.UTF_8)

        val combined = keystoreManager.encryptCombined(plaintext, alias)
        assertTrue(combined.size >= 12 + plaintext.size)

        val decrypted = keystoreManager.decryptCombined(combined, alias)
        assertTrue(plaintext.contentEquals(decrypted))
    }

    @Test
    fun testStringEncryptionDecryptionBase64() {
        val alias = "string_key"
        val message = "Good evening Aster! Can you plan my Saturday?"

        val encryptedBase64 = keystoreManager.encryptString(message, alias)
        assertNotNull(encryptedBase64)
        assertNotEquals(message, encryptedBase64)

        val decrypted = keystoreManager.decryptString(encryptedBase64, alias)
        assertEquals(message, decrypted)
    }

    @Test
    fun testSemanticSecurityRandomIvPerEncryption() {
        val alias = "semantic_key"
        val message = "Identical message payload"

        val enc1 = keystoreManager.encrypt(message.toByteArray(Charsets.UTF_8), alias)
        val enc2 = keystoreManager.encrypt(message.toByteArray(Charsets.UTF_8), alias)

        // IVs must be fresh and unique per encryption
        assertFalse(enc1.iv.contentEquals(enc2.iv))
        // Ciphertexts must differ due to different IVs
        assertFalse(enc1.ciphertext.contentEquals(enc2.ciphertext))

        // Both must decrypt to the same plaintext
        val dec1 = keystoreManager.decrypt(enc1, alias)
        val dec2 = keystoreManager.decrypt(enc2, alias)
        assertEquals(message, String(dec1, Charsets.UTF_8))
        assertEquals(message, String(dec2, Charsets.UTF_8))
    }

    @Test
    fun testDeleteKey() {
        val alias = "key_to_delete"
        keystoreManager.getOrCreateKey(alias)
        assertTrue(keystoreManager.hasKey(alias))

        keystoreManager.deleteKey(alias)
        assertFalse(keystoreManager.hasKey(alias))
    }
}
