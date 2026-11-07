package com.astercompanion.android.data.repository

import com.astercompanion.android.data.local.AsterDatabase
import com.astercompanion.android.data.local.ChatMessageDao
import com.astercompanion.android.data.local.ChatMessageEntity
import com.astercompanion.android.data.local.MemoryDao
import com.astercompanion.android.data.local.MemoryEntity
import com.astercompanion.android.data.local.ProfileDao
import com.astercompanion.android.data.local.ProfileEntity
import com.astercompanion.android.data.sync.CloudAiAvailability
import com.astercompanion.android.data.sync.SyncEngine
import com.astercompanion.android.data.sync.SyncState
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.StateFlow
import java.util.UUID

/**
 * Unified repository providing offline-first access to Aster Companion data (PRD v1.1 §6 & §14).
 * Guarantees local cached reads are always available even when offline.
 */
class AsterRepository(
    private val profileDao: ProfileDao,
    private val memoryDao: MemoryDao,
    private val chatMessageDao: ChatMessageDao,
    private val syncEngine: SyncEngine
) {
    /**
     * Convenience constructor taking the AsterDatabase instance directly.
     */
    constructor(
        database: AsterDatabase,
        syncEngine: SyncEngine
    ) : this(
        profileDao = database.profileDao(),
        memoryDao = database.memoryDao(),
        chatMessageDao = database.chatMessageDao(),
        syncEngine = syncEngine
    )

    // --- Online / Offline & Sync State ---
    val isOnline: StateFlow<Boolean> = syncEngine.isOnline
    val cloudAiAvailability: StateFlow<CloudAiAvailability> = syncEngine.cloudAiAvailability
    val syncState: StateFlow<SyncState> = syncEngine.syncState

    fun setOnline(online: Boolean) {
        syncEngine.setOnlineState(online)
    }

    suspend fun triggerSync() {
        syncEngine.triggerSync()
    }

    // --- Profile Operations (PRD v1.1 §9) ---

    fun getProfiles(): Flow<List<ProfileEntity>> = profileDao.getProfiles()

    fun getActiveProfile(): Flow<ProfileEntity?> = profileDao.getActiveProfile()

    suspend fun getActiveProfileSync(): ProfileEntity? = profileDao.getActiveProfileSync()

    suspend fun createProfile(name: String, voice: String = "Warm voice"): Result<ProfileEntity> {
        val count = profileDao.countProfiles()
        if (count >= ProfileEntity.MAX_PROFILES_PER_ACCOUNT) {
            return Result.failure(IllegalStateException("Maximum of 2 companion profiles allowed per account (PRD §9.1)"))
        }

        val id = UUID.randomUUID().toString()
        val isFirst = count == 0
        val profile = ProfileEntity(
            id = id,
            name = name,
            voice = voice,
            isActiveOnDevice = isFirst
        )
        profileDao.insertProfile(profile)
        return Result.success(profile)
    }

    suspend fun switchProfile(profileId: String) {
        profileDao.switchActiveProfile(profileId)
    }

    suspend fun updateProfile(profile: ProfileEntity) {
        profileDao.updateProfile(profile.copy(updatedAt = System.currentTimeMillis()))
    }

    // --- Memory Operations (PRD v1.1 §14) ---

    fun getActiveMemories(profileId: String): Flow<List<MemoryEntity>> =
        memoryDao.getActiveMemories(profileId)

    fun getPinnedMemories(profileId: String): Flow<List<MemoryEntity>> =
        memoryDao.getPinnedMemories(profileId)

    fun getMemoriesByCategory(profileId: String, category: String): Flow<List<MemoryEntity>> =
        memoryDao.getMemoriesByCategory(profileId, category)

    fun searchMemories(profileId: String, query: String): Flow<List<MemoryEntity>> =
        memoryDao.searchMemories(profileId, query)

    suspend fun saveMemory(
        profileId: String,
        content: String,
        category: String = MemoryEntity.CATEGORY_CONVERSATIONAL,
        confidence: Float = 1.0f,
        source: String = MemoryEntity.SOURCE_USER_EXPLICIT
    ): MemoryEntity {
        val memory = MemoryEntity(
            id = UUID.randomUUID().toString(),
            profileId = profileId,
            title = content,
            category = category,
            confidence = confidence,
            source = source,
            isPinned = false,
            isForgotten = false,
            createdAt = System.currentTimeMillis(),
            updatedAt = System.currentTimeMillis()
        )
        memoryDao.insertMemory(memory)
        return memory
    }

    suspend fun setMemoryPinned(profileId: String, memoryId: String, isPinned: Boolean) {
        memoryDao.setPinned(profileId, memoryId, isPinned)
    }

    suspend fun setMemoryForgotten(profileId: String, memoryId: String, isForgotten: Boolean) {
        memoryDao.setForgotten(profileId, memoryId, isForgotten)
    }

    suspend fun deleteMemory(profileId: String, memoryId: String) {
        memoryDao.deleteMemory(profileId, memoryId)
    }

    // --- Chat & Conversation History (PRD v1.1 §6.2) ---

    fun getMessages(profileId: String): Flow<List<ChatMessageEntity>> =
        chatMessageDao.getMessagesForProfile(profileId)

    suspend fun sendMessage(
        profileId: String,
        content: String,
        mediaUri: String? = null,
        mediaType: String? = null,
        metadataJson: String? = null
    ): ChatMessageEntity {
        return syncEngine.enqueueChatMessage(
            profileId = profileId,
            content = content,
            sender = ChatMessageEntity.SENDER_USER,
            mediaUri = mediaUri,
            mediaType = mediaType,
            metadataJson = metadataJson
        )
    }

    suspend fun saveAssistantMessage(
        profileId: String,
        content: String,
        metadataJson: String? = null
    ): ChatMessageEntity {
        val message = ChatMessageEntity(
            id = UUID.randomUUID().toString(),
            profileId = profileId,
            sender = ChatMessageEntity.SENDER_ASTER,
            text = content,
            createdAt = System.currentTimeMillis(),
            syncStatus = ChatMessageEntity.STATUS_SYNCED,
            metadataJson = metadataJson
        )
        chatMessageDao.insertMessage(message)
        return message
    }
}
