package com.astercompanion.android.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Update
import kotlinx.coroutines.flow.Flow

/**
 * Data Access Object for durable outbox queue (PRD v1.1 §6.3, §14).
 * Handles monotonic sequence progression, state transitions, and batch operations.
 */
@Dao
interface OutboxDao {

    @Query("SELECT MAX(sequence_number) FROM outbox_events WHERE device_id = :deviceId")
    suspend fun getMaxSequenceNumber(deviceId: String): Long?

    @Query("SELECT * FROM outbox_events WHERE status = 'PENDING' ORDER BY sequence_number ASC LIMIT :limit")
    suspend fun getPendingEvents(limit: Int = 50): List<OutboxEventEntity>

    @Query("SELECT * FROM outbox_events WHERE profile_id = :profileId AND status = 'PENDING' ORDER BY sequence_number ASC LIMIT :limit")
    suspend fun getPendingEventsForProfile(profileId: String, limit: Int = 50): List<OutboxEventEntity>

    @Query("SELECT * FROM outbox_events WHERE status = 'IN_FLIGHT' ORDER BY sequence_number ASC")
    suspend fun getInFlightEvents(): List<OutboxEventEntity>

    @Query("SELECT * FROM outbox_events WHERE id = :id LIMIT 1")
    suspend fun getEventById(id: String): OutboxEventEntity?

    @Query("SELECT * FROM outbox_events WHERE device_id = :deviceId AND sequence_number = :sequenceNumber LIMIT 1")
    suspend fun getEventBySequenceNumber(deviceId: String, sequenceNumber: Long): OutboxEventEntity?

    @Query("SELECT * FROM outbox_events WHERE device_id = :deviceId ORDER BY sequence_number ASC")
    suspend fun getAllEventsForDevice(deviceId: String): List<OutboxEventEntity>

    @Insert(onConflict = OnConflictStrategy.ABORT)
    suspend fun insertEvent(event: OutboxEventEntity)

    @Insert(onConflict = OnConflictStrategy.ABORT)
    suspend fun insertEvents(events: List<OutboxEventEntity>)

    @Update
    suspend fun updateEvent(event: OutboxEventEntity)

    @Query("UPDATE outbox_events SET status = 'IN_FLIGHT', last_attempt_at = :attemptAt WHERE id IN (:ids)")
    suspend fun markInFlight(ids: List<String>, attemptAt: Long = System.currentTimeMillis())

    @Query("UPDATE outbox_events SET status = 'ACKNOWLEDGED', error_message = NULL WHERE id IN (:ids)")
    suspend fun markAcknowledged(ids: List<String>)

    @Query("UPDATE outbox_events SET status = 'ACKNOWLEDGED', error_message = NULL WHERE device_id = :deviceId AND sequence_number <= :sequenceNumber")
    suspend fun acknowledgeUpToSequence(deviceId: String, sequenceNumber: Long)

    @Query("UPDATE outbox_events SET status = :status, retry_count = retry_count + 1, last_attempt_at = :attemptAt, error_message = :errorMessage WHERE id = :id")
    suspend fun recordAttemptFailure(id: String, status: String, attemptAt: Long, errorMessage: String?)

    @Query("UPDATE outbox_events SET status = 'PENDING' WHERE status = 'IN_FLIGHT' AND last_attempt_at < :staleThreshold")
    suspend fun resetStaleInFlightEvents(staleThreshold: Long)

    @Query("SELECT COUNT(*) FROM outbox_events WHERE status = 'PENDING' OR status = 'IN_FLIGHT'")
    fun getPendingCountFlow(): Flow<Int>

    @Query("SELECT COUNT(*) FROM outbox_events WHERE status = 'PENDING' OR status = 'IN_FLIGHT'")
    suspend fun getPendingCount(): Int

    @Query("DELETE FROM outbox_events WHERE status = 'ACKNOWLEDGED' AND created_at < :olderThan")
    suspend fun pruneAcknowledgedEvents(olderThan: Long): Int

    @Query("DELETE FROM outbox_events WHERE device_id = :deviceId")
    suspend fun clearDeviceEvents(deviceId: String)
}
