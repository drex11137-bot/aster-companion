package com.astercompanion.android.model

/**
 * Models for the Memories system in Aster Companion.
 * Adheres strictly to PRD v1.1 §14 & §9.4 and UI reference screenshot (56d6d982-5337-4170-80e5-1e156d239b38.png).
 */

object MemoryCategories {
    const val ALL = "All"
    const val PEOPLE = "People"
    const val PREFERENCES = "Preferences"
    const val PLANS = "Plans"

    val FILTER_CATEGORIES = listOf(ALL, PEOPLE, PREFERENCES, PLANS)
    val EDITABLE_CATEGORIES = listOf(PEOPLE, PREFERENCES, PLANS)
}

data class MemoryItem(
    val id: String,
    val profileId: String,
    val title: String,
    val category: String,
    val iconType: String = ICON_SUN,
    val addedAgoLabel: String = "Added recently",
    val createdAt: Long = System.currentTimeMillis(),
    val updatedAt: Long = System.currentTimeMillis(),
    val isSharedWithOtherProfile: Boolean = false,
    val sharedToProfileId: String? = null,
    val sharedAt: Long? = null
) {
    companion object {
        const val ICON_SUN = "sun"
        const val ICON_PERSON = "person"
        const val ICON_PLUS = "plus"
        const val ICON_RUN = "run"
        const val ICON_BOOKMARK = "bookmark"
    }
}

/**
 * Audit record for explicit cross-profile sharing per PRD §9.4.
 * Never allows implicit sharing: records source, target, timestamp, and explicit user confirmation.
 */
data class MemoryShareAudit(
    val id: String,
    val memoryId: String,
    val memoryTitle: String,
    val sourceProfileId: String,
    val targetProfileId: String,
    val timestamp: Long = System.currentTimeMillis(),
    val confirmedByUser: Boolean = true
)
