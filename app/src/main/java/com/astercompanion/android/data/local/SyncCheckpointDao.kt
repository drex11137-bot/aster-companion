package com.astercompanion.android.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

/**
 * Data Access Object for tracking server synchronization checkpoints (PRD v1.1 §6.3).
 */
@Dao
interface SyncCheckpointDao {

    @Query("SELECT * FROM sync_checkpoints WHERE device_id = :deviceId AND profile_id = :profileId LIMIT 1")
    suspend fun getCheckpoint(deviceId: String, profileId: String): SyncCheckpointEntity?

    @Query("SELECT * FROM sync_checkpoints WHERE device_id = :deviceId AND profile_id = :profileId LIMIT 1")
    fun getCheckpointFlow(deviceId: String, profileId: String): Flow<SyncCheckpointEntity?>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertCheckpoint(checkpoint: SyncCheckpointEntity)

    @Query("""
        UPDATE sync_checkpoints 
        SET last_acknowledged_sequence_number = :seqNumber, 
            last_server_timestamp = :serverTimestamp, 
            updated_at = :updatedAt 
        WHERE device_id = :deviceId AND profile_id = :profileId
    """)
    suspend fun updateCheckpoint(
        deviceId: String,
        profileId: String,
        seqNumber: Long,
        serverTimestamp: Long,
        updatedAt: Long = System.currentTimeMillis()
    ): Int

    @Query("DELETE FROM sync_checkpoints WHERE device_id = :deviceId")
    suspend fun deleteCheckpointsForDevice(deviceId: String)
}
