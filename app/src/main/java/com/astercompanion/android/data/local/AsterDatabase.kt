package com.astercompanion.android.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

/**
 * Primary offline-first Room database for Aster Companion (PRD v1.1 §6 & §14).
 * Holds companion profiles, cached memories, chat history, durable outbox queue,
 * synchronization checkpoints, screen awareness events, and gap logs.
 */
@Database(
    entities = [
        ProfileEntity::class,
        MemoryEntity::class,
        ChatMessageEntity::class,
        OutboxEventEntity::class,
        SyncCheckpointEntity::class,
        SyncGapEntity::class,
        ReminderEntity::class,
        TaskEntity::class,
        MemoryAuditEntity::class,
        ScreenEventEntity::class
    ],
    version = 1,
    exportSchema = false
)
abstract class AsterDatabase : RoomDatabase() {

    abstract fun profileDao(): ProfileDao
    abstract fun memoryDao(): MemoryDao
    abstract fun chatDao(): ChatDao
    fun chatMessageDao(): ChatMessageDao = chatDao()
    abstract fun todayDao(): TodayDao
    abstract fun screenEventDao(): ScreenEventDao
    abstract fun outboxDao(): OutboxDao
    abstract fun syncCheckpointDao(): SyncCheckpointDao
    abstract fun syncGapDao(): SyncGapDao

    companion object {
        private const val DATABASE_NAME = "aster_companion.db"

        @Volatile
        private var INSTANCE: AsterDatabase? = null

        fun getInstance(context: Context): AsterDatabase {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: buildDatabase(context.applicationContext).also { INSTANCE = it }
            }
        }

        private fun buildDatabase(context: Context): AsterDatabase {
            return Room.databaseBuilder(
                context,
                AsterDatabase::class.java,
                DATABASE_NAME
            )
                .fallbackToDestructiveMigration()
                .build()
        }

        /**
         * Creates an in-memory database instance for testing.
         */
        fun createInMemory(context: Context): AsterDatabase {
            return Room.inMemoryDatabaseBuilder(
                context,
                AsterDatabase::class.java
            )
                .allowMainThreadQueries()
                .build()
        }
    }
}
