package com.astercompanion.android.data.local

import androidx.room.ColumnInfo
import androidx.room.Entity

/**
 * Tracks last acknowledged sequence number from server per device and profile (PRD v1.1 §6.3).
 * Composite primary key: (deviceId, profileId).
 */
@Entity(
    tableName = "sync_checkpoints",
    primaryKeys = ["device_id", "profile_id"]
)
data class SyncCheckpointEntity(
    @ColumnInfo(name = "device_id")
    val deviceId: String,

    @ColumnInfo(name = "profile_id")
    val profileId: String,

    @ColumnInfo(name = "last_acknowledged_sequence_number")
    val lastAcknowledgedSequenceNumber: Long,

    @ColumnInfo(name = "last_server_timestamp")
    val lastServerTimestamp: Long = 0L,

    @ColumnInfo(name = "updated_at")
    val updatedAt: Long = System.currentTimeMillis()
)
