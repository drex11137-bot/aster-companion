package com.astercompanion.android.data.local

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey
import com.astercompanion.android.model.MemoryItem
import com.astercompanion.android.model.RecentMemoryCard

/**
 * Offline cached memory entity (PRD v1.1 §14).
 * Strictly isolated per companion profile (PRD §9.2).
 */
@Entity(
    tableName = "memories",
    indices = [
        Index(value = ["profileId"]),
        Index(value = ["profileId", "category"])
    ]
)
data class MemoryEntity(
    @PrimaryKey
    @ColumnInfo(name = "id")
    val id: String,

    @ColumnInfo(name = "profileId")
    val profileId: String,

    @ColumnInfo(name = "title")
    val title: String,

    @ColumnInfo(name = "category")
    val category: String,

    @ColumnInfo(name = "iconType")
    val iconType: String = "sun",

    @ColumnInfo(name = "addedAgoLabel")
    val addedAgoLabel: String = "Added recently",

    @ColumnInfo(name = "confidence")
    val confidence: Float = 1.0f,

    @ColumnInfo(name = "is_pinned")
    val isPinned: Boolean = false,

    @ColumnInfo(name = "is_forgotten")
    val isForgotten: Boolean = false,

    @ColumnInfo(name = "isSharedWithOtherProfile")
    val isSharedWithOtherProfile: Boolean = false,

    @ColumnInfo(name = "sharedToProfileId")
    val sharedToProfileId: String? = null,

    @ColumnInfo(name = "sharedAt")
    val sharedAt: Long? = null,

    @ColumnInfo(name = "source")
    val source: String = SOURCE_USER_EXPLICIT,

    @ColumnInfo(name = "createdAt")
    val createdAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "updatedAt")
    val updatedAt: Long = System.currentTimeMillis()
) {
    val content: String get() = title
    val isExplicitlyShared: Boolean get() = isSharedWithOtherProfile

    @androidx.room.Ignore
    constructor(
        id: String,
        profileId: String,
        content: String,
        category: String,
        confidence: Float = 1.0f,
        source: String = SOURCE_USER_EXPLICIT,
        isPinned: Boolean = false,
        isForgotten: Boolean = false,
        createdAt: Long = System.currentTimeMillis(),
        updatedAt: Long = System.currentTimeMillis()
    ) : this(
        id = id,
        profileId = profileId,
        title = content,
        category = category,
        iconType = "sun",
        addedAgoLabel = "Added recently",
        confidence = confidence,
        isPinned = isPinned,
        isForgotten = isForgotten,
        isSharedWithOtherProfile = false,
        sharedToProfileId = null,
        sharedAt = null,
        source = source,
        createdAt = createdAt,
        updatedAt = updatedAt
    )

    @androidx.room.Ignore
    constructor(
        id: String,
        profileId: String,
        title: String,
        category: String,
        iconType: String,
        addedAgoLabel: String,
        createdAt: Long,
        updatedAt: Long,
        isSharedWithOtherProfile: Boolean,
        sharedToProfileId: String?,
        sharedAt: Long?
    ) : this(
        id = id,
        profileId = profileId,
        title = title,
        category = category,
        iconType = iconType,
        addedAgoLabel = addedAgoLabel,
        confidence = 1.0f,
        isPinned = false,
        isForgotten = false,
        isSharedWithOtherProfile = isSharedWithOtherProfile,
        sharedToProfileId = sharedToProfileId,
        sharedAt = sharedAt,
        source = SOURCE_USER_EXPLICIT,
        createdAt = createdAt,
        updatedAt = updatedAt
    )

    fun toDomain(): MemoryItem = MemoryItem(
        id = id,
        profileId = profileId,
        title = title,
        category = category,
        iconType = iconType,
        addedAgoLabel = addedAgoLabel,
        createdAt = createdAt,
        updatedAt = updatedAt,
        isSharedWithOtherProfile = isSharedWithOtherProfile,
        sharedToProfileId = sharedToProfileId,
        sharedAt = sharedAt
    )

    fun toRecentMemoryCard(): RecentMemoryCard = RecentMemoryCard(
        id = id,
        profileId = profileId,
        title = title,
        timeAgoLabel = addedAgoLabel,
        imageUrl = null,
        category = category,
        createdAt = createdAt
    )

    companion object {
        const val CATEGORY_ALL = "All"
        const val CATEGORY_PEOPLE = "People"
        const val CATEGORY_PREFERENCES = "Preferences"
        const val CATEGORY_PLANS = "Plans"
        const val CATEGORY_CONVERSATIONAL = "CONVERSATIONAL"
        const val CATEGORY_PREFERENCE = "PREFERENCE"
        const val CATEGORY_BEHAVIORAL = "BEHAVIORAL"
        const val CATEGORY_ACTIVITY = "ACTIVITY"
        const val CATEGORY_RELATIONSHIP = "RELATIONSHIP"
        const val CATEGORY_PROCEDURAL = "PROCEDURAL"

        const val SOURCE_USER_EXPLICIT = "USER_EXPLICIT"
        const val SOURCE_CONVERSATION_INFERENCE = "CONVERSATION_INFERENCE"
        const val SOURCE_OBSERVED_BEHAVIOR = "OBSERVED_BEHAVIOR"

        fun fromDomain(domain: MemoryItem): MemoryEntity = MemoryEntity(
            id = domain.id,
            profileId = domain.profileId,
            title = domain.title,
            category = domain.category,
            iconType = domain.iconType,
            addedAgoLabel = domain.addedAgoLabel,
            createdAt = domain.createdAt,
            updatedAt = domain.updatedAt,
            isSharedWithOtherProfile = domain.isSharedWithOtherProfile,
            sharedToProfileId = domain.sharedToProfileId,
            sharedAt = domain.sharedAt
        )
    }
}
