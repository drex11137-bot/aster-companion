package com.astercompanion.android.model

/**
 * Models for the multimodal Chat screen in Aster Companion.
 * Adheres strictly to PRD v1.1 §7, §10 and UI reference screenshot (79ffed4b-1317-46e6-98db-6eb6c96f60d6.png).
 */

enum class MessageSender {
    USER,
    COMPANION,
    SYSTEM
}

data class ScheduleItem(
    val id: String,
    val time: String,
    val title: String,
    val description: String,
    val iconType: String,
    val isCompleted: Boolean = false,
    val isExpanded: Boolean = false
) {
    companion object {
        const val ICON_COFFEE = "coffee"
        const val ICON_WORKOUT = "workout"
        const val ICON_LUNCH = "lunch"
        const val ICON_BOOK = "book"
        const val ICON_NIGHT = "night"
    }
}

data class ScheduleCard(
    val id: String = "sched_sat",
    val dateTitle: String = "Saturday, Nov 15",
    val subtitle: String = "A calm and balanced day",
    val items: List<ScheduleItem> = defaultSaturdaySchedule()
) {
    companion object {
        fun defaultSaturdaySchedule(): List<ScheduleItem> = listOf(
            ScheduleItem(
                id = "item_1",
                time = "9:00 AM",
                title = "Slow morning",
                description = "Coffee, a good book, no rush",
                iconType = ScheduleItem.ICON_COFFEE
            ),
            ScheduleItem(
                id = "item_2",
                time = "11:30 AM",
                title = "Gentle workout",
                description = "Yoga or a walk outside",
                iconType = ScheduleItem.ICON_WORKOUT
            ),
            ScheduleItem(
                id = "item_3",
                time = "1:00 PM",
                title = "Lunch",
                description = "Something fresh and local",
                iconType = ScheduleItem.ICON_LUNCH
            ),
            ScheduleItem(
                id = "item_4",
                time = "3:00 PM",
                title = "Personal time",
                description = "Read, journal, or a creative project",
                iconType = ScheduleItem.ICON_BOOK
            ),
            ScheduleItem(
                id = "item_5",
                time = "7:00 PM",
                title = "Wind down",
                description = "A quiet evening",
                iconType = ScheduleItem.ICON_NIGHT
            )
        )
    }
}

data class CitationChip(
    val id: String,
    val text: String = "Used 2 memories",
    val memoryIds: List<String> = emptyList(),
    val isExpanded: Boolean = false
)

enum class AttachmentType {
    IMAGE,
    VIDEO,
    FILE,
    AUDIO,
    SCREEN_CAPTURE
}

data class Attachment(
    val id: String,
    val type: AttachmentType,
    val name: String,
    val uri: String,
    val sizeBytes: Long = 0L
)

data class ChatMessage(
    val id: String,
    val profileId: String = "profile_aster",
    val sender: MessageSender,
    val text: String = "",
    val content: String = text,
    val timestampLabel: String = "8:20 PM",
    val timestamp: Long = System.currentTimeMillis(),
    val deliveryStatus: String = "sent",
    val isStreaming: Boolean = false,
    val isDelivered: Boolean = true,
    val scheduleCard: ScheduleCard? = null,
    val citations: List<CitationChip> = emptyList(),
    val memoryCitations: List<String> = emptyList(),
    val attachments: List<Attachment> = emptyList(),
    val createdAt: Long = timestamp
)

enum class AudioRecordingState {
    IDLE,
    RECORDING,
    PROCESSING,
    ERROR
}

data class SuggestionPill(
    val id: String,
    val label: String,
    val iconType: String
) {
    companion object {
        const val PILL_ADD_REMINDER = "Add reminder"
        const val PILL_SUMMARIZE = "Summarize"

        fun defaultPills(): List<SuggestionPill> = listOf(
            SuggestionPill(id = "pill_reminder", label = PILL_ADD_REMINDER, iconType = "reminder"),
            SuggestionPill(id = "pill_summarize", label = PILL_SUMMARIZE, iconType = "summarize")
        )
    }
}

data class ChatMessageChunk(
    val messageId: String,
    val deltaText: String,
    val isFinal: Boolean,
    val scheduleCard: ScheduleCard? = null,
    val citations: List<CitationChip> = emptyList()
)
