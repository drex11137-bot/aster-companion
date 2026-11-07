package com.astercompanion.android.data.local

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * Durable outbox event queue entity (PRD v1.1 §6.3, §14).
 * Tracks monotonic sequence number, device ID, SHA-256 checksum, status, and retries.
 */
@Entity(
    tableName = "outbox_events",
    indices = [
        Index(value = ["device_id", "sequence_number"], unique = true),
        Index(value = ["status"]),
        Index(value = ["profile_id"])
    ]
)
data class OutboxEventEntity(
    @PrimaryKey
    @ColumnInfo(name = "id")
    val id: String,

    @ColumnInfo(name = "sequence_number")
    val sequenceNumber: Long,

    @ColumnInfo(name = "device_id")
    val deviceId: String,

    @ColumnInfo(name = "profile_id")
    val profileId: String,

    @ColumnInfo(name = "event_type")
    val eventType: String, // e.g. "CHAT_MESSAGE", "SCREEN_FRAME", "AUDIO_EVENT", "MEMORY_MUTATION"

    @ColumnInfo(name = "checksum")
    val checksum: String, // SHA-256 hash of payload_json

    @ColumnInfo(name = "payload_json")
    val payloadJson: String,

    @ColumnInfo(name = "status")
    val status: String = STATUS_PENDING,

    @ColumnInfo(name = "retry_count")
    val retryCount: Int = 0,

    @ColumnInfo(name = "last_attempt_at")
    val lastAttemptAt: Long? = null,

    @ColumnInfo(name = "error_message")
    val errorMessage: String? = null,

    @ColumnInfo(name = "created_at")
    val createdAt: Long = System.currentTimeMillis()
) {
    companion object {
        const val STATUS_PENDING = "PENDING"
        const val STATUS_IN_FLIGHT = "IN_FLIGHT"
        const val STATUS_ACKNOWLEDGED = "ACKNOWLEDGED"
        const val STATUS_FAILED = "FAILED"

        const val TYPE_CHAT_MESSAGE = "CHAT_MESSAGE"
        const val TYPE_SCREEN_FRAME = "SCREEN_FRAME"
        const val TYPE_AUDIO_EVENT = "AUDIO_EVENT"
        const val TYPE_MEMORY_MUTATION = "MEMORY_MUTATION"
        const val TYPE_PROFILE_MUTATION = "PROFILE_MUTATION"
        const val TYPE_ACTION_REQUEST = "ACTION_REQUEST"
    }
}
