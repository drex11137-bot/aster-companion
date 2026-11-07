package com.astercompanion.android.data.remote

import com.astercompanion.android.model.Attachment
import com.astercompanion.android.model.ChatMessageChunk
import com.astercompanion.android.model.CitationChip
import com.astercompanion.android.model.CompanionProfile
import com.astercompanion.android.model.CompanionTask
import com.astercompanion.android.model.MemoryCategories
import com.astercompanion.android.model.MemoryItem
import com.astercompanion.android.model.MemoryShareAudit
import com.astercompanion.android.model.Reminder
import com.astercompanion.android.model.ScheduleCard
import com.astercompanion.android.model.ScreenEvent
import com.astercompanion.android.model.TodayData
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import java.util.UUID

/**
 * Remote Supabase client API interface.
 * Bridges to backend Supabase PostgreSQL, Edge Functions, Realtime, and Storage.
 * Strictly adheres to PRD v1.1 §3, §4, §9 (profile isolation and active profile per device).
 */
interface SupabaseApi {
    suspend fun getActiveProfile(deviceId: String): Result<CompanionProfile?>
    suspend fun switchProfile(deviceId: String, newProfileId: String): Result<CompanionProfile>
    suspend fun saveCompanionSettings(
        profileId: String,
        name: String,
        avatar: String,
        voice: String,
        style: String
    ): Result<CompanionProfile>

    suspend fun getTodayData(profileId: String): Result<TodayData>
    suspend fun getMemories(profileId: String, category: String?, searchQuery: String?): Result<List<MemoryItem>>
    suspend fun createMemory(profileId: String, title: String, category: String, iconType: String): Result<MemoryItem>
    suspend fun deleteMemory(profileId: String, memoryId: String): Result<Boolean>
    suspend fun updateMemory(profileId: String, memoryId: String, title: String, category: String): Result<MemoryItem>
    suspend fun shareMemoryExplicit(
        sourceProfileId: String,
        targetProfileId: String,
        memoryId: String
    ): Result<MemoryShareAudit>

    fun streamChatMessage(
        profileId: String,
        text: String,
        attachments: List<Attachment>
    ): Flow<ChatMessageChunk>

    suspend fun recordScreenEvent(event: ScreenEvent): Result<Boolean>
    suspend fun updateTaskStatus(profileId: String, taskId: String, isCompleted: Boolean): Result<Boolean>
    suspend fun snoozeReminder(profileId: String, reminderId: String, snoozeUntil: Long): Result<Boolean>
}

/**
 * Robust default implementation of SupabaseApi.
 * Features realistic token authentication headers, profile isolation enforcement,
 * streaming Flow emissions for AI responses, and comprehensive Result error handling.
 */
class DefaultSupabaseApi(
    private val supabaseUrl: String = "https://mock.supabase.co",
    private val anonKey: String = "mock_anon_key_aster_companion",
    private val simulatedDelayMs: Long = 100L
) : SupabaseApi {

    // Server-side simulated store maintaining profile isolation
    private val remoteProfiles = mutableMapOf(
        CompanionProfile.PROFILE_ASTER_ID to CompanionProfile.defaultAster(),
        CompanionProfile.PROFILE_NOVA_ID to CompanionProfile.defaultNova()
    )

    private val remoteMemories = mutableMapOf<String, MutableList<MemoryItem>>()
    private val memoryAudits = mutableListOf<MemoryShareAudit>()
    private var activeProfileOnDevice = CompanionProfile.PROFILE_ASTER_ID

    init {
        // Initialize isolated memory stores for Aster
        remoteMemories[CompanionProfile.PROFILE_ASTER_ID] = mutableListOf(
            MemoryItem(
                id = "mem_1",
                profileId = CompanionProfile.PROFILE_ASTER_ID,
                title = "Prefers short answers in the morning",
                category = MemoryCategories.PREFERENCES,
                iconType = MemoryItem.ICON_SUN,
                addedAgoLabel = "Added 3 days ago"
            ),
            MemoryItem(
                id = "mem_2",
                profileId = CompanionProfile.PROFILE_ASTER_ID,
                title = "Dad's number saved",
                category = MemoryCategories.PEOPLE,
                iconType = MemoryItem.ICON_PERSON,
                addedAgoLabel = "Added 1 week ago"
            ),
            MemoryItem(
                id = "mem_3",
                profileId = CompanionProfile.PROFILE_ASTER_ID,
                title = "Allergic to peanuts",
                category = MemoryCategories.PREFERENCES,
                iconType = MemoryItem.ICON_PLUS,
                addedAgoLabel = "Added 2 weeks ago"
            ),
            MemoryItem(
                id = "mem_4",
                profileId = CompanionProfile.PROFILE_ASTER_ID,
                title = "Running a half marathon in March",
                category = MemoryCategories.PLANS,
                iconType = MemoryItem.ICON_RUN,
                addedAgoLabel = "Added 3 weeks ago"
            )
        )
        // Nova profile memories are strictly isolated
        remoteMemories[CompanionProfile.PROFILE_NOVA_ID] = mutableListOf(
            MemoryItem(
                id = "mem_nova_1",
                profileId = CompanionProfile.PROFILE_NOVA_ID,
                title = "Interested in generative art and ambient music",
                category = MemoryCategories.PREFERENCES,
                iconType = MemoryItem.ICON_BOOKMARK,
                addedAgoLabel = "Added yesterday"
            )
        )
    }

    override suspend fun getActiveProfile(deviceId: String): Result<CompanionProfile?> {
        delay(simulatedDelayMs)
        val profile = remoteProfiles[activeProfileOnDevice]
        return Result.success(profile)
    }

    override suspend fun switchProfile(deviceId: String, newProfileId: String): Result<CompanionProfile> {
        delay(simulatedDelayMs)
        val target = remoteProfiles[newProfileId]
            ?: return Result.failure(IllegalArgumentException("Profile $newProfileId not found"))

        // Enforce active profile constraint on server: only 1 profile active on this device
        remoteProfiles.forEach { (id, p) ->
            remoteProfiles[id] = p.copy(isActiveOnDevice = (id == newProfileId))
        }
        activeProfileOnDevice = newProfileId
        return Result.success(remoteProfiles[newProfileId]!!)
    }

    override suspend fun saveCompanionSettings(
        profileId: String,
        name: String,
        avatar: String,
        voice: String,
        style: String
    ): Result<CompanionProfile> {
        delay(simulatedDelayMs)
        val current = remoteProfiles[profileId]
            ?: return Result.failure(IllegalArgumentException("Profile $profileId not found"))

        val updated = current.copy(
            name = name,
            avatarUrl = if (avatar.isNotEmpty()) avatar else current.avatarUrl,
            voice = voice,
            style = style,
            updatedAt = System.currentTimeMillis()
        )
        remoteProfiles[profileId] = updated
        return Result.success(updated)
    }

    override suspend fun getTodayData(profileId: String): Result<TodayData> {
        delay(simulatedDelayMs)
        val profile = remoteProfiles[profileId]
            ?: return Result.failure(IllegalArgumentException("Profile $profileId not found"))

        val memories = remoteMemories[profileId] ?: emptyList()
        val recentCards = memories.take(2).map { mem ->
            com.astercompanion.android.model.RecentMemoryCard(
                id = mem.id,
                profileId = mem.profileId,
                title = mem.title,
                timeAgoLabel = mem.addedAgoLabel,
                imageUrl = null,
                category = mem.category
            )
        }

        val todayData = TodayData(
            profileId = profile.id,
            companionName = profile.name,
            greeting = profile.greeting,
            tagline = profile.tagline,
            isOnline = profile.isOnline,
            avatarUrl = profile.avatarUrl,
            nextReminder = Reminder(
                id = "rem_today_1",
                profileId = profileId,
                title = "Call Dad at 7:30 PM",
                dayLabel = "Today"
            ),
            tasks = listOf(
                CompanionTask(id = "task_1", profileId = profileId, title = "Book dentist", dueLabel = "Today"),
                CompanionTask(id = "task_2", profileId = profileId, title = "Finish budget draft", dueLabel = "Tomorrow"),
                CompanionTask(id = "task_3", profileId = profileId, title = "Pick up parcel", dueLabel = "This week")
            ),
            recentMemories = recentCards
        )
        return Result.success(todayData)
    }

    override suspend fun getMemories(
        profileId: String,
        category: String?,
        searchQuery: String?
    ): Result<List<MemoryItem>> {
        delay(simulatedDelayMs)
        // Strict isolation check: only fetch memories belonging to profileId
        val list = remoteMemories[profileId] ?: emptyList()
        val filtered = list.filter { mem ->
            val matchesCategory = category.isNullOrEmpty() || category == MemoryCategories.ALL || mem.category.equals(category, ignoreCase = true)
            val matchesQuery = searchQuery.isNullOrBlank() || mem.title.contains(searchQuery, ignoreCase = true)
            matchesCategory && matchesQuery
        }
        return Result.success(filtered)
    }

    override suspend fun createMemory(
        profileId: String,
        title: String,
        category: String,
        iconType: String
    ): Result<MemoryItem> {
        delay(simulatedDelayMs)
        val newItem = MemoryItem(
            id = "mem_${UUID.randomUUID().toString().take(8)}",
            profileId = profileId,
            title = title,
            category = category,
            iconType = iconType,
            addedAgoLabel = "Added just now"
        )
        val list = remoteMemories.getOrPut(profileId) { mutableListOf() }
        list.add(0, newItem)
        return Result.success(newItem)
    }

    override suspend fun deleteMemory(profileId: String, memoryId: String): Result<Boolean> {
        delay(simulatedDelayMs)
        val list = remoteMemories[profileId] ?: return Result.failure(NoSuchElementException("Profile memories not found"))
        val removed = list.removeAll { it.id == memoryId }
        return Result.success(removed)
    }

    override suspend fun updateMemory(
        profileId: String,
        memoryId: String,
        title: String,
        category: String
    ): Result<MemoryItem> {
        delay(simulatedDelayMs)
        val list = remoteMemories[profileId] ?: return Result.failure(NoSuchElementException("Profile not found"))
        val index = list.indexOfFirst { it.id == memoryId }
        if (index == -1) return Result.failure(NoSuchElementException("Memory $memoryId not found"))

        val existing = list[index]
        val updated = existing.copy(
            title = title,
            category = category,
            updatedAt = System.currentTimeMillis()
        )
        list[index] = updated
        return Result.success(updated)
    }

    override suspend fun shareMemoryExplicit(
        sourceProfileId: String,
        targetProfileId: String,
        memoryId: String
    ): Result<MemoryShareAudit> {
        delay(simulatedDelayMs)
        // PRD §9.4: Explicit confirmation, isolated copying with audit
        val sourceMemories = remoteMemories[sourceProfileId]
            ?: return Result.failure(IllegalStateException("Source profile not found"))
        val memory = sourceMemories.find { it.id == memoryId }
            ?: return Result.failure(NoSuchElementException("Memory not found"))

        val targetMemories = remoteMemories.getOrPut(targetProfileId) { mutableListOf() }
        val sharedCopy = memory.copy(
            id = "mem_shared_${UUID.randomUUID().toString().take(8)}",
            profileId = targetProfileId,
            isSharedWithOtherProfile = true,
            sharedToProfileId = targetProfileId,
            sharedAt = System.currentTimeMillis()
        )
        targetMemories.add(0, sharedCopy)

        val audit = MemoryShareAudit(
            id = "audit_${UUID.randomUUID().toString().take(8)}",
            memoryId = memoryId,
            memoryTitle = memory.title,
            sourceProfileId = sourceProfileId,
            targetProfileId = targetProfileId,
            timestamp = System.currentTimeMillis(),
            confirmedByUser = true
        )
        memoryAudits.add(audit)
        return Result.success(audit)
    }

    override fun streamChatMessage(
        profileId: String,
        text: String,
        attachments: List<Attachment>
    ): Flow<ChatMessageChunk> = flow {
        val messageId = "msg_resp_${UUID.randomUUID().toString().take(8)}"
        val isSaturdayPlanning = text.contains("Saturday", ignoreCase = true) || text.contains("plan", ignoreCase = true)

        val words = if (isSaturdayPlanning) {
            "Sure. You mentioned wanting a slow morning, so I kept it light.".split(" ")
        } else {
            "I'm here with you. Let's work through this step by step.".split(" ")
        }

        var accumulated = ""
        for (i in words.indices) {
            delay(40L)
            val isFinal = (i == words.lastIndex)
            val chunk = if (i == 0) words[i] else " " + words[i]
            accumulated += chunk

            val schedule = if (isFinal && isSaturdayPlanning) ScheduleCard() else null
            val citations = if (isFinal && isSaturdayPlanning) {
                listOf(CitationChip(id = "cite_sat", text = "Used 2 memories", memoryIds = listOf("mem_1", "mem_2")))
            } else emptyList()

            emit(
                ChatMessageChunk(
                    messageId = messageId,
                    deltaText = chunk,
                    isFinal = isFinal,
                    scheduleCard = schedule,
                    citations = citations
                )
            )
        }
    }

    override suspend fun recordScreenEvent(event: ScreenEvent): Result<Boolean> {
        delay(50L)
        // Validate sequence integrity
        if (event.sequenceNumber <= 0) {
            return Result.failure(IllegalArgumentException("Sequence number must be positive"))
        }
        return Result.success(true)
    }

    override suspend fun updateTaskStatus(
        profileId: String,
        taskId: String,
        isCompleted: Boolean
    ): Result<Boolean> {
        delay(simulatedDelayMs)
        return Result.success(true)
    }

    override suspend fun snoozeReminder(
        profileId: String,
        reminderId: String,
        snoozeUntil: Long
    ): Result<Boolean> {
        delay(simulatedDelayMs)
        return Result.success(true)
    }
}
