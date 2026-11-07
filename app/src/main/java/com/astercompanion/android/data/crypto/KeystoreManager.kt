package com.astercompanion.android.data.crypto

import java.nio.ByteBuffer
import java.security.Key
import java.security.KeyStore
import java.security.SecureRandom
import java.util.Base64
import java.util.concurrent.ConcurrentHashMap
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

/**
 * Data class representing encrypted payload with separated initialization vector and ciphertext.
 */
data class EncryptedPayload(
    val iv: ByteArray,
    val ciphertext: ByteArray
) {
    override fun equals(other: Any?): Boolean {
        if (this === other) return true
        if (javaClass != other?.javaClass) return false
        other as EncryptedPayload
        if (!iv.contentEquals(other.iv)) return false
        if (!ciphertext.contentEquals(other.ciphertext)) return false
        return true
    }

    override fun hashCode(): Int {
        var result = iv.contentHashCode()
        result = 31 * result + ciphertext.contentHashCode()
        return result
    }

    /**
     * Combines 12-byte IV and ciphertext into a single byte array.
     */
    fun toCombined(): ByteArray {
        val buffer = ByteBuffer.allocate(iv.size + ciphertext.size)
        buffer.put(iv)
        buffer.put(ciphertext)
        return buffer.array()
    }

    companion object {
        fun fromCombined(combined: ByteArray, ivSize: Int = 12): EncryptedPayload {
            require(combined.size >= ivSize) { "Combined data must be at least $ivSize bytes" }
            val iv = combined.copyOfRange(0, ivSize)
            val ciphertext = combined.copyOfRange(ivSize, combined.size)
            return EncryptedPayload(iv, ciphertext)
        }
    }
}

/**
 * KeystoreManager provides hardware-backed or JCE AES-256-GCM encryption at rest (PRD v1.1 §16.2).
 * When AndroidKeyStore is available (on Android devices), it securely uses hardware keystore.
 * In JVM unit tests or desktop clients, it automatically uses an in-memory secure JCE AES-256 provider.
 */
class KeystoreManager(
    private val useFallbackJce: Boolean = false
) {
    companion object {
        const val DEFAULT_ALIAS = "aster_db_encryption_key"
        private const val ANDROID_KEYSTORE = "AndroidKeyStore"
        private const val TRANSFORMATION_GCM = "AES/GCM/NoPadding"
        private const val AES_KEY_SIZE_BITS = 256
        private const val GCM_IV_LENGTH_BYTES = 12
        private const val GCM_TAG_LENGTH_BITS = 128

        @Volatile
        private var INSTANCE: KeystoreManager? = null

        fun getInstance(): KeystoreManager {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: KeystoreManager().also { INSTANCE = it }
            }
        }
    }

    private val secureRandom = SecureRandom()
    private val inMemoryKeyStore = ConcurrentHashMap<String, SecretKey>()

    private val isAndroidKeyStoreAvailable: Boolean by lazy {
        if (useFallbackJce) return@lazy false
        try {
            val ks = KeyStore.getInstance(ANDROID_KEYSTORE)
            ks.load(null)
            true
        } catch (_: Throwable) {
            false
        }
    }

    /**
     * Retrieves or generates a 256-bit AES key for the given alias.
     */
    @Synchronized
    fun getOrCreateKey(alias: String = DEFAULT_ALIAS): Key {
        if (isAndroidKeyStoreAvailable) {
            return getOrCreateAndroidKeyStoreKey(alias)
        }
        return inMemoryKeyStore.computeIfAbsent(alias) {
            val keyGen = KeyGenerator.getInstance("AES")
            keyGen.init(AES_KEY_SIZE_BITS, secureRandom)
            keyGen.generateKey()
        }
    }

    private fun getOrCreateAndroidKeyStoreKey(alias: String): Key {
        val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
        if (keyStore.containsAlias(alias)) {
            return keyStore.getKey(alias, null)
        }

        try {
            // Dynamically build KeyGenParameterSpec to prevent compilation failures on non-Android platforms
            val keyGenSpecClass = Class.forName("android.security.keystore.KeyGenParameterSpec\$Builder")
            val keyPropsClass = Class.forName("android.security.keystore.KeyProperties")

            val purposeEncrypt = keyPropsClass.getField("PURPOSE_ENCRYPT").getInt(null)
            val purposeDecrypt = keyPropsClass.getField("PURPOSE_DECRYPT").getInt(null)
            val blockModeGcm = keyPropsClass.getField("BLOCK_MODE_GCM").get(null) as String
            val paddingNone = keyPropsClass.getField("ENCRYPTION_PADDING_NONE").get(null) as String

            val constructor = keyGenSpecClass.getConstructor(String::class.java, Int::class.javaPrimitiveType)
            val builder = constructor.newInstance(alias, purposeEncrypt or purposeDecrypt)

            val setBlockModes = keyGenSpecClass.getMethod("setBlockModes", Array<String>::class.java)
            setBlockModes.invoke(builder, arrayOf(blockModeGcm))

            val setEncryptionPaddings = keyGenSpecClass.getMethod("setEncryptionPaddings", Array<String>::class.java)
            setEncryptionPaddings.invoke(builder, arrayOf(paddingNone))

            val setKeySize = keyGenSpecClass.getMethod("setKeySize", Int::class.javaPrimitiveType)
            setKeySize.invoke(builder, AES_KEY_SIZE_BITS)

            val buildMethod = keyGenSpecClass.getMethod("build")
            val spec = buildMethod.invoke(builder)

            val keyGenerator = KeyGenerator.getInstance("AES", ANDROID_KEYSTORE)
            val initMethod = KeyGenerator::class.java.getMethod("init", java.security.spec.AlgorithmParameterSpec::class.java)
            initMethod.invoke(keyGenerator, spec)

            return keyGenerator.generateKey()
        } catch (_: Throwable) {
            // Fallback to JCE if AndroidKeyStore reflection fails
            return inMemoryKeyStore.computeIfAbsent(alias) {
                val keyGen = KeyGenerator.getInstance("AES")
                keyGen.init(AES_KEY_SIZE_BITS, secureRandom)
                keyGen.generateKey()
            }
        }
    }

    /**
     * Encrypts plaintext bytes using AES-256-GCM.
     */
    fun encrypt(plaintext: ByteArray, alias: String = DEFAULT_ALIAS): EncryptedPayload {
        val key = getOrCreateKey(alias)
        val iv = ByteArray(GCM_IV_LENGTH_BYTES)
        secureRandom.nextBytes(iv)

        val cipher = Cipher.getInstance(TRANSFORMATION_GCM)
        val gcmSpec = GCMParameterSpec(GCM_TAG_LENGTH_BITS, iv)
        cipher.init(Cipher.ENCRYPT_MODE, key, gcmSpec)

        val ciphertext = cipher.doFinal(plaintext)
        return EncryptedPayload(iv = iv, ciphertext = ciphertext)
    }

    /**
     * Decrypts an EncryptedPayload using AES-256-GCM.
     */
    fun decrypt(encryptedPayload: EncryptedPayload, alias: String = DEFAULT_ALIAS): ByteArray {
        val key = getOrCreateKey(alias)
        val cipher = Cipher.getInstance(TRANSFORMATION_GCM)
        val gcmSpec = GCMParameterSpec(GCM_TAG_LENGTH_BITS, encryptedPayload.iv)
        cipher.init(Cipher.DECRYPT_MODE, key, gcmSpec)

        return cipher.doFinal(encryptedPayload.ciphertext)
    }

    /**
     * Encrypts plaintext and returns combined (IV + ciphertext) byte array.
     */
    fun encryptCombined(plaintext: ByteArray, alias: String = DEFAULT_ALIAS): ByteArray {
        return encrypt(plaintext, alias).toCombined()
    }

    /**
     * Decrypts combined (IV + ciphertext) byte array.
     */
    fun decryptCombined(combined: ByteArray, alias: String = DEFAULT_ALIAS): ByteArray {
        val payload = EncryptedPayload.fromCombined(combined, GCM_IV_LENGTH_BYTES)
        return decrypt(payload, alias)
    }

    /**
     * Encrypts UTF-8 string to Base64 encoded string.
     */
    fun encryptString(plaintext: String, alias: String = DEFAULT_ALIAS): String {
        val combined = encryptCombined(plaintext.toByteArray(Charsets.UTF_8), alias)
        return Base64.getEncoder().encodeToString(combined)
    }

    /**
     * Decrypts Base64 encoded string to UTF-8 plaintext.
     */
    fun decryptString(ciphertextBase64: String, alias: String = DEFAULT_ALIAS): String {
        val combined = Base64.getDecoder().decode(ciphertextBase64)
        val decryptedBytes = decryptCombined(combined, alias)
        return String(decryptedBytes, Charsets.UTF_8)
    }

    /**
     * Checks if a key exists for the given alias.
     */
    fun hasKey(alias: String = DEFAULT_ALIAS): Boolean {
        if (isAndroidKeyStoreAvailable) {
            try {
                val ks = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
                return ks.containsAlias(alias)
            } catch (_: Throwable) {
                // fall through
            }
        }
        return inMemoryKeyStore.containsKey(alias)
    }

    /**
     * Deletes the key associated with the given alias.
     */
    @Synchronized
    fun deleteKey(alias: String = DEFAULT_ALIAS) {
        if (isAndroidKeyStoreAvailable) {
            try {
                val ks = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
                if (ks.containsAlias(alias)) {
                    ks.deleteEntry(alias)
                }
            } catch (_: Throwable) {
                // ignore
            }
        }
        inMemoryKeyStore.remove(alias)
    }
}
