package com.astercompanion.android.model

/**
 * Models for the Today screen in Aster Companion.
 * Adheres strictly to PRD v1.1 and UI reference screenshot (56539447-5086-44aa-b0ad-b98fa9cb6a8d.png).
 */

data class Reminder(
    val id: String,
    val profileId: String,
    val title: String,
    val dayLabel: String,
    val isSnoozed: Boolean = false,
    val snoozeUntil: Long? = null,
    val createdAt: Long = System.currentTimeMillis()
)

data class CompanionTask(
    val id: String,
    val profileId: String,
    val title: String,
    val dueLabel: String,
    val isCompleted: Boolean = false,
    val completedAt: Long? = null,
    val createdAt: Long = System.currentTimeMillis()
)

data class RecentMemoryCard(
    val id: String,
    val profileId: String,
    val title: String,
    val timeAgoLabel: String,
    val imageUrl: String? = null,
    val category: String = "Preferences",
    val createdAt: Long = System.currentTimeMillis()
)

data class TodayData(
    val profileId: String,
    val companionName: String,
    val greeting: String,
    val tagline: String,
    val isOnline: Boolean,
    val avatarUrl: String,
    val nextReminder: Reminder?,
    val tasks: List<CompanionTask>,
    val recentMemories: List<RecentMemoryCard>
)
