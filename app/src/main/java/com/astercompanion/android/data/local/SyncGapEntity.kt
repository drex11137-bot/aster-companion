package com.astercompanion.android.data.local

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * Entity recording unrecoverable sequence gaps (PRD v1.1 §6.3, §6.4).
 * Ensures that if sequence numbers skip, the system records the gap explicitly
 * rather than fabricating false continuity.
 */
@Entity(
    tableName = "sync_gaps",
    indices = [
        Index(value = ["device_id", "from_sequence", "to_sequence"]),
        Index(value = ["profile_id"])
    ]
)
data class SyncGapEntity(
    @PrimaryKey
    @ColumnInfo(name = "id")
    val id: String,

    @ColumnInfo(name = "device_id")
    val deviceId: String,

    @ColumnInfo(name = "profile_id")
    val profileId: String,

    @ColumnInfo(name = "from_sequence")
    val fromSequence: Long,

    @ColumnInfo(name = "to_sequence")
    val toSequence: Long,

    @ColumnInfo(name = "missing_count")
    val missingCount: Long,

    @ColumnInfo(name = "detected_at")
    val detectedAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "reason")
    val reason: String = "SEQUENCE_SKIP_DETECTED",

    @ColumnInfo(name = "is_acknowledged")
    val isAcknowledged: Boolean = false
)
