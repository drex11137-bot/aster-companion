package com.astercompanion.android.data.local

import androidx.room.Dao
import androidx.room.Delete
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction
import androidx.room.Update
import kotlinx.coroutines.flow.Flow

/**
 * Local Room DAO for Companion Profiles (PRD v1.1 §9).
 * Enforces maximum of 2 companion profiles per account and single active profile constraint.
 */
@Dao
interface ProfileDao {

    @Query("SELECT * FROM companion_profiles ORDER BY created_at ASC")
    fun getProfiles(): Flow<List<ProfileEntity>>

    @Query("SELECT * FROM companion_profiles ORDER BY created_at ASC")
    fun getAllProfiles(): Flow<List<ProfileEntity>> = getProfiles()

    @Query("SELECT * FROM companion_profiles ORDER BY created_at ASC")
    fun getAllProfilesSync(): List<ProfileEntity>

    @Query("SELECT * FROM companion_profiles WHERE id = :id LIMIT 1")
    suspend fun getProfileById(id: String): ProfileEntity?

    @Query("SELECT * FROM companion_profiles WHERE id = :id LIMIT 1")
    fun observeProfileById(id: String): Flow<ProfileEntity?>

    @Query("SELECT * FROM companion_profiles WHERE isActiveOnDevice = 1 LIMIT 1")
    fun getActiveProfile(): Flow<ProfileEntity?>

    @Query("SELECT * FROM companion_profiles WHERE isActiveOnDevice = 1 LIMIT 1")
    suspend fun getActiveProfileSync(): ProfileEntity?

    @Query("SELECT COUNT(*) FROM companion_profiles")
    suspend fun countProfiles(): Int

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertProfile(profile: ProfileEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertProfiles(profiles: List<ProfileEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertOrUpdate(profile: ProfileEntity) = insertProfile(profile)

    @Update
    suspend fun updateProfile(profile: ProfileEntity)

    @Update
    suspend fun update(profile: ProfileEntity) = updateProfile(profile)

    @Query("DELETE FROM companion_profiles WHERE id = :id")
    suspend fun deleteProfile(id: String)

    @Query("UPDATE companion_profiles SET isActiveOnDevice = 0, updatedAt = :timestamp")
    suspend fun deactivateAllProfiles(timestamp: Long = System.currentTimeMillis())

    @Query("UPDATE companion_profiles SET isActiveOnDevice = 1, updatedAt = :timestamp WHERE id = :profileId")
    suspend fun activateProfile(profileId: String, timestamp: Long = System.currentTimeMillis())

    @Transaction
    suspend fun switchActiveProfile(newProfileId: String, timestamp: Long = System.currentTimeMillis()) {
        deactivateAllProfiles(timestamp)
        activateProfile(newProfileId, timestamp)
    }

    @Query("UPDATE companion_profiles SET name = :name, avatarUrl = :avatar, voice = :voice, style = :style, updatedAt = :updatedAt WHERE id = :profileId")
    suspend fun updateSettings(
        profileId: String,
        name: String,
        avatar: String,
        voice: String,
        style: String,
        updatedAt: Long = System.currentTimeMillis()
    )

    @Query("UPDATE companion_profiles SET hairColor = :hairColor, eyeColor = :eyeColor, updatedAt = :updatedAt WHERE id = :profileId")
    suspend fun updateAppearance(
        profileId: String,
        hairColor: String,
        eyeColor: String,
        updatedAt: Long = System.currentTimeMillis()
    )
}

/**
 * Local Room DAO for offline cached memories (PRD v1.1 §14).
 * Strictly isolated per companion profile (PRD §9.2).
 */
@Dao
interface MemoryDao {

    @Query("SELECT * FROM memories WHERE profileId = :profileId AND is_forgotten = 0 ORDER BY is_pinned DESC, updatedAt DESC")
    fun getActiveMemories(profileId: String): Flow<List<MemoryEntity>>

    @Query("SELECT * FROM memories WHERE profileId = :profileId ORDER BY updatedAt DESC")
    fun getAllMemories(profileId: String): Flow<List<MemoryEntity>>

    @Query("SELECT * FROM memories WHERE profileId = :profileId AND is_pinned = 1 AND is_forgotten = 0 ORDER BY updatedAt DESC")
    fun getPinnedMemories(profileId: String): Flow<List<MemoryEntity>>

    @Query("SELECT * FROM memories WHERE profileId = :profileId AND category = :category AND is_forgotten = 0 ORDER BY is_pinned DESC, updatedAt DESC")
    fun getMemoriesByCategory(profileId: String, category: String): Flow<List<MemoryEntity>>

    @Query("SELECT * FROM memories WHERE profileId = :profileId AND is_forgotten = 0 AND title LIKE '%' || :query || '%' ORDER BY is_pinned DESC, updatedAt DESC")
    fun searchMemories(profileId: String, query: String): Flow<List<MemoryEntity>>

    @Query("""
        SELECT * FROM memories 
        WHERE profileId = :profileId 
          AND is_forgotten = 0 
          AND (:category = 'All' OR category = :category) 
          AND (:query = '' OR title LIKE '%' || :query || '%') 
        ORDER BY is_pinned DESC, updatedAt DESC
    """)
    fun getMemories(profileId: String, category: String = "All", query: String = ""): Flow<List<MemoryEntity>>

    @Query("SELECT * FROM memories WHERE profileId = :profileId AND id = :id LIMIT 1")
    suspend fun getMemoryById(profileId: String, id: String): MemoryEntity?

    @Query("SELECT * FROM memories WHERE id = :id LIMIT 1")
    suspend fun getMemoryByIdGlobal(id: String): MemoryEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMemory(memory: MemoryEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMemories(memories: List<MemoryEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertOrUpdate(memory: MemoryEntity) = insertMemory(memory)

    @Update
    suspend fun updateMemory(memory: MemoryEntity)

    @Query("UPDATE memories SET is_pinned = :isPinned, updatedAt = :timestamp WHERE profileId = :profileId AND id = :id")
    suspend fun setPinned(profileId: String, id: String, isPinned: Boolean, timestamp: Long = System.currentTimeMillis())

    @Query("UPDATE memories SET is_forgotten = :isForgotten, updatedAt = :timestamp WHERE profileId = :profileId AND id = :id")
    suspend fun setForgotten(profileId: String, id: String, isForgotten: Boolean, timestamp: Long = System.currentTimeMillis())

    @Query("DELETE FROM memories WHERE profileId = :profileId AND id = :id")
    suspend fun deleteMemory(profileId: String, id: String)

    @Delete
    suspend fun delete(memory: MemoryEntity)

    @Query("DELETE FROM memories WHERE id = :memoryId")
    suspend fun deleteById(memoryId: String)

    @Query("DELETE FROM memories WHERE profileId = :profileId")
    suspend fun deleteAllForProfile(profileId: String)

    @Query("SELECT COUNT(*) FROM memories WHERE profileId = :profileId AND is_forgotten = 0")
    suspend fun countActiveMemories(profileId: String): Int

    @Query("SELECT * FROM memories WHERE profileId = :profileId ORDER BY createdAt DESC LIMIT :limit")
    fun getRecentMemories(profileId: String, limit: Int = 4): Flow<List<MemoryEntity>>

    @Query("SELECT * FROM memories WHERE profileId = :profileId ORDER BY createdAt DESC")
    fun getMemoriesForProfile(profileId: String): Flow<List<MemoryEntity>> = getAllMemories(profileId)
}

/**
 * Local Room DAO for conversation history (PRD v1.1 §6.2, §6.5).
 */
@Dao
interface ChatMessageDao {

    @Query("SELECT * FROM chat_messages WHERE profileId = :profileId ORDER BY createdAt ASC")
    fun getMessagesForProfile(profileId: String): Flow<List<ChatMessageEntity>>

    @Query("SELECT * FROM chat_messages WHERE profileId = :profileId ORDER BY createdAt DESC LIMIT :limit")
    suspend fun getRecentMessages(profileId: String, limit: Int = 50): List<ChatMessageEntity>

    @Query("SELECT * FROM chat_messages WHERE profileId = :profileId AND sync_status = 'PENDING_SEND' ORDER BY createdAt ASC")
    suspend fun getPendingMessages(profileId: String): List<ChatMessageEntity>

    @Query("SELECT * FROM chat_messages WHERE sync_status = 'PENDING_SEND' ORDER BY createdAt ASC")
    suspend fun getAllPendingMessages(): List<ChatMessageEntity>

    @Query("SELECT * FROM chat_messages WHERE id = :id LIMIT 1")
    suspend fun getMessageById(id: String): ChatMessageEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMessage(message: ChatMessageEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertMessages(messages: List<ChatMessageEntity>)

    @Update
    suspend fun updateMessage(message: ChatMessageEntity)

    @Query("UPDATE chat_messages SET sync_status = :status WHERE id = :id")
    suspend fun updateSyncStatus(id: String, status: String)

    @Query("UPDATE chat_messages SET sync_status = :status WHERE id IN (:ids)")
    suspend fun updateSyncStatusBatch(ids: List<String>, status: String)

    @Query("DELETE FROM chat_messages WHERE profileId = :profileId AND id = :id")
    suspend fun deleteMessage(profileId: String, id: String)

    @Query("DELETE FROM chat_messages WHERE profileId = :profileId")
    suspend fun deleteMessagesForProfile(profileId: String)

    @Query("DELETE FROM chat_messages WHERE profileId = :profileId")
    suspend fun clearHistory(profileId: String) = deleteMessagesForProfile(profileId)

    @Query("SELECT COUNT(*) FROM chat_messages WHERE profileId = :profileId")
    suspend fun countMessagesForProfile(profileId: String): Int
}

typealias ChatDao = ChatMessageDao

/**
 * Local Room DAO for today's reminders and tasks (PRD v1.1 §8).
 */
@Dao
interface TodayDao {

    @Query("SELECT * FROM reminders WHERE profileId = :profileId ORDER BY createdAt DESC LIMIT 1")
    fun getNextReminder(profileId: String): Flow<ReminderEntity?>

    @Query("SELECT * FROM companion_tasks WHERE profileId = :profileId ORDER BY createdAt ASC")
    fun getTasks(profileId: String): Flow<List<TaskEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertReminder(reminder: ReminderEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertReminders(reminders: List<ReminderEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTask(task: TaskEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertTasks(tasks: List<TaskEntity>)

    @Update
    suspend fun updateTask(task: TaskEntity)
}

/**
 * Local Room DAO for screen events captured during awareness mode (PRD v1.1 §10).
 */
@Dao
interface ScreenEventDao {

    @Query("SELECT * FROM screen_events WHERE profileId = :profileId ORDER BY timestamp DESC LIMIT :limit")
    fun getRecentEvents(profileId: String, limit: Int = 20): Flow<List<ScreenEventEntity>>

    @Query("SELECT * FROM screen_events WHERE profileId = :profileId ORDER BY timestamp ASC")
    fun getAllEvents(profileId: String): Flow<List<ScreenEventEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertEvent(event: ScreenEventEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertEvents(events: List<ScreenEventEntity>)

    @Query("DELETE FROM screen_events WHERE profileId = :profileId")
    suspend fun clearEvents(profileId: String)

    @Query("SELECT MAX(sequenceNumber) FROM screen_events WHERE profileId = :profileId")
    suspend fun getMaxSequenceNumber(profileId: String): Long?
}
