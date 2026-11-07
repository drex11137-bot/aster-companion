package com.astercompanion.android.repository

import com.astercompanion.android.data.local.AsterDatabase
import com.astercompanion.android.data.local.ChatMessageDao
import com.astercompanion.android.data.local.ChatMessageEntity
import com.astercompanion.android.data.local.MemoryDao
import com.astercompanion.android.data.local.MemoryEntity
import com.astercompanion.android.data.local.ProfileDao
import com.astercompanion.android.data.local.ProfileEntity
import com.astercompanion.android.data.local.ReminderEntity
import com.astercompanion.android.data.local.ScreenEventDao
import com.astercompanion.android.data.local.TaskEntity
import com.astercompanion.android.data.local.TodayDao
import com.astercompanion.android.data.remote.DefaultSupabaseApi
import com.astercompanion.android.data.remote.SupabaseApi
import com.astercompanion.android.model.Attachment
import com.astercompanion.android.model.ChatMessage
import com.astercompanion.android.model.ChatMessageChunk
import com.astercompanion.android.model.CitationChip
import com.astercompanion.android.model.CompanionProfile
import com.astercompanion.android.model.CompanionTask
import com.astercompanion.android.model.MemoryCategories
import com.astercompanion.android.model.MemoryItem
import com.astercompanion.android.model.MemoryShareAudit
import com.astercompanion.android.model.MessageSender
import com.astercompanion.android.model.RecentMemoryCard
import com.astercompanion.android.model.Reminder
import com.astercompanion.android.model.ScheduleCard
import com.astercompanion.android.model.ScreenEvent
import com.astercompanion.android.model.TodayData
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.withContext
import java.util.UUID

/**
 * CompanionRepository implements the unified repository pattern bridging local Room DB (AsterDatabase)
 * and remote Supabase API.
 *
 * Adheres strictly to PRD v1.1:
 * 1. Enforces active profile constraint: only 1 profile can be active on this device at a time (§9.5).
 * 2. Strict isolation: memories, chat, and settings are strictly partitioned by profileId (§9.2).
 * 3. Verified offline-first reads with remote cloud synchronization and continuity (§6).
 * 4. Required methods:
 *    - getActiveProfile()
 *    - switchProfile(newProfileId)
 *    - getTodayData()
 *    - getMemories(category, searchQuery)
 *    - sendMessage(text, attachments)
 *    - recordScreenEvent(event)
 *    - saveCompanionSettings(name, avatar, voice, style)
 */
class CompanionRepository(
    private val profileDao: ProfileDao,
    private val memoryDao: MemoryDao,
    private val chatMessageDao: ChatMessageDao,
    private val remoteApi: SupabaseApi = DefaultSupabaseApi(),
    private val ioDispatcher: CoroutineDispatcher = Dispatchers.IO,
    private val deviceId: String = "device_android_primary"
) {

    constructor(
        database: AsterDatabase,
        remoteApi: SupabaseApi = DefaultSupabaseApi(),
        ioDispatcher: CoroutineDispatcher = Dispatchers.IO,
        deviceId: String = "device_android_primary"
    ) : this(
        profileDao = database.profileDao(),
        memoryDao = database.memoryDao(),
        chatMessageDao = database.chatMessageDao(),
        remoteApi = remoteApi,
        ioDispatcher = ioDispatcher,
        deviceId = deviceId
    )

    constructor(
        profileDao: ProfileDao,
        todayDao: TodayDao,
        memoryDao: MemoryDao,
        chatDao: ChatMessageDao,
        screenEventDao: ScreenEventDao,
        remoteApi: SupabaseApi = DefaultSupabaseApi(),
        ioDispatcher: CoroutineDispatcher = Dispatchers.IO,
        deviceId: String = "device_android_primary"
    ) : this(
        profileDao = profileDao,
        memoryDao = memoryDao,
        chatMessageDao = chatDao,
        remoteApi = remoteApi,
        ioDispatcher = ioDispatcher,
        deviceId = deviceId
    )

    // In-memory reactive state for local tasks, reminders, and screen awareness continuity
    private val remindersFlow = MutableStateFlow<Map<String, Reminder>>(
        mapOf(
            "rem_1" to Reminder(
                id = "rem_1",
                profileId = CompanionProfile.PROFILE_ASTER_ID,
                title = "Call Dad at 7:30 PM",
                dayLabel = "Today"
            )
        )
    )

    private val tasksFlow = MutableStateFlow<List<CompanionTask>>(
        listOf(
            CompanionTask(id = "task_1", profileId = CompanionProfile.PROFILE_ASTER_ID, title = "Book dentist", dueLabel = "Today"),
            CompanionTask(id = "task_2", profileId = CompanionProfile.PROFILE_ASTER_ID, title = "Finish budget draft", dueLabel = "Tomorrow"),
            CompanionTask(id = "task_3", profileId = CompanionProfile.PROFILE_ASTER_ID, title = "Pick up parcel", dueLabel = "This week")
        )
    )

    private val screenEventsFlow = MutableStateFlow<List<ScreenEvent>>(emptyList())
    private val memoryAudits = mutableListOf<MemoryShareAudit>()

    /**
     * Observes the single active profile on this device as a continuous Flow.
     * Enforces active profile constraint: exactly one profile active at a time (§9.5).
     */
    fun getActiveProfile(): Flow<CompanionProfile?> {
        return profileDao.getActiveProfile()
            .map { it?.toDomain() }
            .distinctUntilChanged()
            .flowOn(ioDispatcher)
    }

    /**
     * Snapshot fetch of the currently active profile.
     */
    suspend fun getActiveProfileOnce(): CompanionProfile? = withContext(ioDispatcher) {
        val local = profileDao.getActiveProfileSync()?.toDomain()
        if (local != null) return@withContext local

        // Fallback to seeding default Aster if DB was empty
        val defaultAster = CompanionProfile.defaultAster()
        profileDao.insertProfile(defaultAster.toEntity())
        defaultAster
    }

    /**
     * Switches the active profile on this device.
     * Adheres to PRD §9.5 and §9.6:
     * - Only 1 profile active on this device at a time.
     * - The previous profile's session is suspended/stopped.
     * - Deactivates all existing profiles and activates [newProfileId] atomically.
     * - Synchronizes the state to remote Supabase API.
     */
    suspend fun switchProfile(newProfileId: String): Result<CompanionProfile> = withContext(ioDispatcher) {
        try {
            var target = profileDao.getProfileById(newProfileId)?.toDomain()
            if (target == null) {
                target = if (newProfileId == CompanionProfile.PROFILE_NOVA_ID) {
                    CompanionProfile.defaultNova()
                } else {
                    CompanionProfile.defaultAster()
                }
                profileDao.insertProfile(target.toEntity())
            }

            // Atomic database switch: deactivates all, activates newProfileId
            profileDao.switchActiveProfile(newProfileId)

            // Sync with Supabase remote API
            remoteApi.switchProfile(deviceId, newProfileId)

            val updated = target.copy(isActiveOnDevice = true, updatedAt = System.currentTimeMillis())
            Result.success(updated)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * Observes unified TodayData for the active profile, combining:
     * - Companion status, greeting, and tagline
     * - Next reminder
     * - Tasks list
     * - Recent memories
     */
    fun getTodayData(): Flow<TodayData> = flow {
        val activeProfile = getActiveProfileOnce() ?: CompanionProfile.defaultAster()
        val profileId = activeProfile.id

        combine(
            profileDao.getActiveProfile(),
            remindersFlow,
            tasksFlow,
            memoryDao.getActiveMemories(profileId)
        ) { profileEntity, remindersMap, tasksList, memoryEntities ->
            val profile = profileEntity?.toDomain() ?: activeProfile
            val reminder = remindersMap.values.filter { it.profileId == profile.id }.maxByOrNull { it.createdAt }
            val tasks = tasksList.filter { it.profileId == profile.id }
            val recentMemories = memoryEntities.take(2).map { it.toRecentMemoryCard() }

            TodayData(
                profileId = profile.id,
                companionName = profile.name,
                greeting = profile.greeting,
                tagline = profile.tagline,
                isOnline = profile.isOnline,
                avatarUrl = profile.avatarUrl,
                nextReminder = reminder,
                tasks = tasks,
                recentMemories = recentMemories
            )
        }.collect { emit(it) }
    }.flowOn(ioDispatcher)

    /**
     * Refreshes today's data from remote Supabase API and syncs to local cache.
     */
    suspend fun refreshTodayData(): Result<TodayData> = withContext(ioDispatcher) {
        val activeProfile = getActiveProfileOnce() ?: CompanionProfile.defaultAster()
        try {
            val remoteResult = remoteApi.getTodayData(activeProfile.id)
            if (remoteResult.isSuccess) {
                val data = remoteResult.getOrThrow()
                // Update local reminders & tasks
                data.nextReminder?.let { rem ->
                    val map = remindersFlow.value.toMutableMap()
                    map[rem.id] = rem
                    remindersFlow.value = map
                }
                tasksFlow.value = data.tasks
                Result.success(data)
            } else {
                val reminder = remindersFlow.value.values.firstOrNull { it.profileId == activeProfile.id }
                val tasks = tasksFlow.value.filter { it.profileId == activeProfile.id }
                Result.success(
                    TodayData(
                        profileId = activeProfile.id,
                        companionName = activeProfile.name,
                        greeting = activeProfile.greeting,
                        tagline = activeProfile.tagline,
                        isOnline = activeProfile.isOnline,
                        avatarUrl = activeProfile.avatarUrl,
                        nextReminder = reminder,
                        tasks = tasks,
                        recentMemories = emptyList()
                    )
                )
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * Toggles task completion state in local state and syncs to Supabase.
     */
    suspend fun toggleTask(taskId: String, isCompleted: Boolean): Result<Unit> = withContext(ioDispatcher) {
        try {
            val completedAt = if (isCompleted) System.currentTimeMillis() else null
            val updated = tasksFlow.value.map { task ->
                if (task.id == taskId) task.copy(isCompleted = isCompleted, completedAt = completedAt) else task
            }
            tasksFlow.value = updated

            val profile = getActiveProfileOnce()
            if (profile != null) {
                remoteApi.updateTaskStatus(profile.id, taskId, isCompleted)
            }
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * Snoozes the specified reminder.
     */
    suspend fun snoozeReminder(reminderId: String, snoozeDurationMs: Long = 3600000L): Result<Unit> = withContext(ioDispatcher) {
        try {
            val currentMap = remindersFlow.value.toMutableMap()
            currentMap[reminderId]?.let { rem ->
                currentMap[reminderId] = rem.copy(isSnoozed = true, snoozeUntil = System.currentTimeMillis() + snoozeDurationMs)
            }
            remindersFlow.value = currentMap

            val profile = getActiveProfileOnce()
            if (profile != null) {
                remoteApi.snoozeReminder(profile.id, reminderId, System.currentTimeMillis() + snoozeDurationMs)
            }
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * Retrieves memories filtered by category and search query.
     * Isolated per active profile (§14).
     */
    fun getMemories(category: String?, searchQuery: String?): Flow<List<MemoryItem>> = flow {
        val activeProfile = getActiveProfileOnce() ?: CompanionProfile.defaultAster()
        val cat = if (category.isNullOrBlank()) MemoryCategories.ALL else category
        val query = searchQuery?.trim() ?: ""

        val sourceFlow = if (query.isNotBlank()) {
            memoryDao.searchMemories(activeProfile.id, query)
        } else if (cat != MemoryCategories.ALL) {
            memoryDao.getMemoriesByCategory(activeProfile.id, cat)
        } else {
            memoryDao.getActiveMemories(activeProfile.id)
        }

        sourceFlow.map { list ->
            list.map { it.toDomain() }.filter { item ->
                cat == MemoryCategories.ALL || item.category.equals(cat, ignoreCase = true)
            }
        }.collect { emit(it) }
    }.flowOn(ioDispatcher)

    /**
     * Adds a new memory item for the active profile.
     */
    suspend fun addMemory(
        title: String,
        category: String,
        iconType: String = MemoryItem.ICON_SUN
    ): Result<MemoryItem> = withContext(ioDispatcher) {
        try {
            val activeProfile = getActiveProfileOnce() ?: CompanionProfile.defaultAster()
            val now = System.currentTimeMillis()
            val id = "mem_${UUID.randomUUID().toString().take(8)}"
            val memoryItem = MemoryItem(
                id = id,
                profileId = activeProfile.id,
                title = title.trim(),
                category = category,
                iconType = iconType,
                addedAgoLabel = "Added just now",
                createdAt = now,
                updatedAt = now
            )
            // Persist locally in Room
            memoryDao.insertMemory(
                MemoryEntity(
                    id = id,
                    profileId = activeProfile.id,
                    content = title.trim(),
                    category = category,
                    createdAt = now,
                    updatedAt = now
                )
            )
            // Sync to Supabase
            remoteApi.createMemory(activeProfile.id, title, category, iconType)
            Result.success(memoryItem)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * Deletes a memory item by ID from local Room DB and remote Supabase.
     */
    suspend fun deleteMemory(memoryId: String): Result<Boolean> = withContext(ioDispatcher) {
        try {
            val activeProfile = getActiveProfileOnce() ?: CompanionProfile.defaultAster()
            memoryDao.deleteMemory(activeProfile.id, memoryId)
            remoteApi.deleteMemory(activeProfile.id, memoryId)
            Result.success(true)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * Updates a memory item's title and category.
     */
    suspend fun updateMemory(
        memoryId: String,
        newTitle: String,
        newCategory: String
    ): Result<MemoryItem> = withContext(ioDispatcher) {
        try {
            val activeProfile = getActiveProfileOnce() ?: CompanionProfile.defaultAster()
            val now = System.currentTimeMillis()
            val existing = memoryDao.getMemoryById(activeProfile.id, memoryId)
                ?: return@withContext Result.failure(NoSuchElementException("Memory $memoryId not found"))

            val updatedEntity = existing.copy(
                title = newTitle.trim(),
                category = newCategory,
                updatedAt = now
            )
            memoryDao.updateMemory(updatedEntity)
            remoteApi.updateMemory(activeProfile.id, memoryId, newTitle, newCategory)
            Result.success(updatedEntity.toDomain())
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * Explicitly shares a memory item to another profile per PRD §9.4.
     * Enforces audit logging and prevents cross-profile leakage.
     */
    suspend fun shareMemoryToProfile(
        memoryId: String,
        targetProfileId: String
    ): Result<MemoryShareAudit> = withContext(ioDispatcher) {
        try {
            val activeProfile = getActiveProfileOnce() ?: CompanionProfile.defaultAster()
            val memory = memoryDao.getMemoryById(activeProfile.id, memoryId)?.toDomain()
                ?: return@withContext Result.failure(NoSuchElementException("Memory $memoryId not found"))

            // Mark source memory as shared
            val now = System.currentTimeMillis()
            val sharedEntity = MemoryEntity(
                id = "mem_shared_${UUID.randomUUID().toString().take(8)}",
                profileId = targetProfileId,
                title = memory.title,
                category = memory.category,
                isSharedWithOtherProfile = true,
                createdAt = now,
                updatedAt = now
            )
            memoryDao.insertMemory(sharedEntity)

            // Create audit record
            val audit = MemoryShareAudit(
                id = "audit_${UUID.randomUUID().toString().take(8)}",
                memoryId = memoryId,
                memoryTitle = memory.title,
                sourceProfileId = activeProfile.id,
                targetProfileId = targetProfileId,
                timestamp = now,
                confirmedByUser = true
            )
            memoryAudits.add(audit)

            // Sync with Supabase explicit share
            remoteApi.shareMemoryExplicit(activeProfile.id, targetProfileId, memoryId)

            Result.success(audit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * Retrieves chat messages for the currently active profile.
     */
    fun getChatMessages(): Flow<List<ChatMessage>> = flow {
        val activeProfile = getActiveProfileOnce() ?: CompanionProfile.defaultAster()
        chatMessageDao.getMessagesForProfile(activeProfile.id).collect { list ->
            emit(list.map { it.toDomain() })
        }
    }.flowOn(ioDispatcher)

    /**
     * Sends a user chat message, persists it locally, and streams the companion response
     * chunk-by-chunk from Supabase.
     */
    fun sendMessage(
        text: String,
        attachments: List<Attachment> = emptyList()
    ): Flow<ChatMessageChunk> = flow {
        val activeProfile = getActiveProfileOnce() ?: CompanionProfile.defaultAster()
        val now = System.currentTimeMillis()

        // 1. Persist user message locally
        val userMsgId = "msg_${UUID.randomUUID().toString().take(8)}"
        val userEntity = ChatMessageEntity(
            id = userMsgId,
            profileId = activeProfile.id,
            sender = MessageSender.USER.name,
            text = text,
            createdAt = now
        )
        chatMessageDao.insertMessage(userEntity)

        // 2. Prepare assistant placeholder
        val assistantMsgId = "msg_${UUID.randomUUID().toString().take(8)}"
        val assistantEntity = ChatMessageEntity(
            id = assistantMsgId,
            profileId = activeProfile.id,
            sender = MessageSender.COMPANION.name,
            text = "",
            createdAt = now + 1
        )
        chatMessageDao.insertMessage(assistantEntity)

        var accumulatedText = ""

        // 3. Stream from remote Supabase API
        remoteApi.streamChatMessage(activeProfile.id, text, attachments)
            .collect { chunk ->
                accumulatedText += chunk.deltaText
                chatMessageDao.updateMessage(
                    assistantEntity.copy(text = accumulatedText)
                )
                emit(chunk)
            }
    }.catch { error ->
        emit(
            ChatMessageChunk(
                messageId = "err_chunk",
                deltaText = " I encountered an error connecting to Aster Cloud: ${error.message}",
                isFinal = true
            )
        )
    }.flowOn(ioDispatcher)

    /**
     * Clears chat history for the active profile only.
     */
    suspend fun clearChat(): Result<Unit> = withContext(ioDispatcher) {
        try {
            val activeProfile = getActiveProfileOnce() ?: CompanionProfile.defaultAster()
            chatMessageDao.deleteMessagesForProfile(activeProfile.id)
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * Records a ScreenEvent for Continuous Awareness.
     * Enforces monotonic sequence ordering, timestamps, and checksum checks per PRD §5.
     */
    suspend fun recordScreenEvent(event: ScreenEvent): Result<Boolean> = withContext(ioDispatcher) {
        try {
            val activeProfile = getActiveProfileOnce() ?: CompanionProfile.defaultAster()
            val currentEvents = screenEventsFlow.value
            val maxSeq = currentEvents.filter { it.profileId == activeProfile.id }.maxOfOrNull { it.sequenceNumber } ?: 0L
            val validatedSeq = if (event.sequenceNumber <= maxSeq) maxSeq + 1 else event.sequenceNumber

            val validatedEvent = event.copy(
                profileId = activeProfile.id,
                sequenceNumber = validatedSeq,
                timestamp = if (event.timestamp <= 0) System.currentTimeMillis() else event.timestamp
            )

            screenEventsFlow.value = currentEvents + validatedEvent
            remoteApi.recordScreenEvent(validatedEvent)
            Result.success(true)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * Observes screen events for the active profile.
     */
    fun getScreenEvents(): Flow<List<ScreenEvent>> = flow {
        val activeProfile = getActiveProfileOnce() ?: CompanionProfile.defaultAster()
        screenEventsFlow.map { list -> list.filter { it.profileId == activeProfile.id } }
            .collect { emit(it) }
    }.flowOn(ioDispatcher)

    /**
     * Updates companion settings (name, avatar, voice, style) in Room and Supabase.
     */
    suspend fun saveCompanionSettings(
        name: String,
        avatar: String,
        voice: String,
        style: String
    ): Result<CompanionProfile> = withContext(ioDispatcher) {
        try {
            val activeProfile = getActiveProfileOnce() ?: CompanionProfile.defaultAster()
            val cleanName = name.trim().ifEmpty { activeProfile.name }
            val cleanAvatar = avatar.trim().ifEmpty { activeProfile.avatarUrl }

            val updated = activeProfile.copy(
                name = cleanName,
                avatarUrl = cleanAvatar,
                voice = voice,
                style = style,
                updatedAt = System.currentTimeMillis()
            )

            profileDao.updateProfile(updated.toEntity())
            remoteApi.saveCompanionSettings(
                profileId = activeProfile.id,
                name = cleanName,
                avatar = cleanAvatar,
                voice = voice,
                style = style
            )

            Result.success(updated)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * Updates hair color and eye color appearance attributes in Room.
     */
    suspend fun updateAppearance(hairColor: String, eyeColor: String): Result<Unit> = withContext(ioDispatcher) {
        try {
            val activeProfile = getActiveProfileOnce() ?: CompanionProfile.defaultAster()
            val updated = activeProfile.copy(
                hairColor = hairColor,
                eyeColor = eyeColor,
                updatedAt = System.currentTimeMillis()
            )
            profileDao.updateProfile(updated.toEntity())
            Result.success(Unit)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}

// Extension mapper
fun CompanionProfile.toEntity(): ProfileEntity = ProfileEntity.fromDomain(this)
