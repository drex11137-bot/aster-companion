package com.astercompanion.android.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

/**
 * Data Access Object for recording and monitoring unrecoverable sync gaps (PRD v1.1 §6.3, §6.4).
 */
@Dao
interface SyncGapDao {

    @Query("SELECT * FROM sync_gaps WHERE device_id = :deviceId ORDER BY from_sequence ASC")
    fun getGapsForDevice(deviceId: String): Flow<List<SyncGapEntity>>

    @Query("SELECT * FROM sync_gaps WHERE device_id = :deviceId AND profile_id = :profileId ORDER BY from_sequence ASC")
    suspend fun getGapsForProfileSync(deviceId: String, profileId: String): List<SyncGapEntity>

    @Query("SELECT * FROM sync_gaps WHERE device_id = :deviceId AND is_acknowledged = 0 ORDER BY from_sequence ASC")
    suspend fun getUnacknowledgedGaps(deviceId: String): List<SyncGapEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertGap(gap: SyncGapEntity)

    @Query("UPDATE sync_gaps SET is_acknowledged = 1 WHERE id = :gapId")
    suspend fun acknowledgeGap(gapId: String)

    @Query("DELETE FROM sync_gaps WHERE device_id = :deviceId")
    suspend fun deleteGapsForDevice(deviceId: String)
}
