package com.astercompanion.android.data.local

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey
import com.astercompanion.android.model.ChatMessage
import com.astercompanion.android.model.CitationChip
import com.astercompanion.android.model.MessageSender
import com.astercompanion.android.model.ScheduleCard

/**
 * Local chat message entity with sync status (PRD v1.1 §6.2, §6.5).
 * Distinct sync statuses: SYNCED, PENDING_SEND, FAILED.
 */
@Entity(
    tableName = "chat_messages",
    indices = [
        Index(value = ["profileId"]),
        Index(value = ["profileId", "createdAt"])
    ]
)
data class ChatMessageEntity(
    @PrimaryKey
    @ColumnInfo(name = "id")
    val id: String,

    @ColumnInfo(name = "profileId")
    val profileId: String,

    @ColumnInfo(name = "sender")
    val sender: String, // "USER", "ASTER", or "COMPANION"

    @ColumnInfo(name = "text")
    val text: String,

    @ColumnInfo(name = "timestampLabel")
    val timestampLabel: String = "",

    @ColumnInfo(name = "isStreaming")
    val isStreaming: Boolean = false,

    @ColumnInfo(name = "isDelivered")
    val isDelivered: Boolean = true,

    @ColumnInfo(name = "hasScheduleCard")
    val hasScheduleCard: Boolean = false,

    @ColumnInfo(name = "citationsSummary")
    val citationsSummary: String? = null,

    @ColumnInfo(name = "sync_status")
    val syncStatus: String = STATUS_PENDING_SEND,

    @ColumnInfo(name = "media_uri")
    val mediaUri: String? = null,

    @ColumnInfo(name = "media_type")
    val mediaType: String? = null,

    @ColumnInfo(name = "metadata_json")
    val metadataJson: String? = null,

    @ColumnInfo(name = "createdAt")
    val createdAt: Long = System.currentTimeMillis()
) {
    val content: String get() = text
    val timestamp: Long get() = createdAt

    @androidx.room.Ignore
    constructor(
        id: String,
        profileId: String,
        sender: String,
        content: String,
        timestamp: Long,
        syncStatus: String = STATUS_PENDING_SEND,
        mediaUri: String? = null,
        mediaType: String? = null,
        metadataJson: String? = null
    ) : this(
        id = id,
        profileId = profileId,
        sender = sender,
        text = content,
        timestampLabel = "",
        isStreaming = false,
        isDelivered = (syncStatus == STATUS_SYNCED),
        hasScheduleCard = false,
        citationsSummary = null,
        syncStatus = syncStatus,
        mediaUri = mediaUri,
        mediaType = mediaType,
        metadataJson = metadataJson,
        createdAt = timestamp
    )

    fun toDomain(): ChatMessage {
        val messageSender = try {
            MessageSender.valueOf(sender)
        } catch (_: Exception) {
            MessageSender.COMPANION
        }
        val schedule = if (hasScheduleCard) {
            ScheduleCard(
                id = "sched_$id",
                dateTitle = "Saturday, Nov 15",
                subtitle = "A calm and balanced day",
                items = ScheduleCard.defaultSaturdaySchedule()
            )
        } else null

        val citationList = if (!citationsSummary.isNullOrEmpty()) {
            listOf(CitationChip(id = "cite_$id", text = citationsSummary, memoryIds = listOf("mem_1", "mem_2")))
        } else emptyList()

        return ChatMessage(
            id = id,
            profileId = profileId,
            sender = messageSender,
            text = text,
            timestampLabel = timestampLabel,
            isStreaming = isStreaming,
            isDelivered = isDelivered,
            scheduleCard = schedule,
            citations = citationList,
            attachments = emptyList(),
            createdAt = createdAt
        )
    }

    companion object {
        const val SENDER_USER = "USER"
        const val SENDER_ASTER = "ASTER"
        const val SENDER_COMPANION = "COMPANION"

        const val STATUS_SYNCED = "SYNCED"
        const val STATUS_PENDING_SEND = "PENDING_SEND"
        const val STATUS_FAILED = "FAILED"

        fun fromDomain(domain: ChatMessage): ChatMessageEntity = ChatMessageEntity(
            id = domain.id,
            profileId = domain.profileId,
            sender = domain.sender.name,
            text = domain.text,
            timestampLabel = domain.timestampLabel,
            isStreaming = domain.isStreaming,
            isDelivered = domain.isDelivered,
            hasScheduleCard = domain.scheduleCard != null,
            citationsSummary = domain.citations.firstOrNull()?.text,
            createdAt = domain.createdAt,
            syncStatus = if (domain.isDelivered) STATUS_SYNCED else STATUS_PENDING_SEND
        )
    }
}
