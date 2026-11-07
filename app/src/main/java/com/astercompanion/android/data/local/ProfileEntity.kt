package com.astercompanion.android.data.local

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Ignore
import androidx.room.PrimaryKey
import com.astercompanion.android.model.CompanionProfile

/**
 * Entity representing a companion profile (PRD v1.1 §9.1, §9.5).
 * Enforces maximum of 2 companion profiles per account.
 * Only 1 profile can be active on this device at any time.
 */
@Entity(tableName = "companion_profiles")
data class ProfileEntity(
    @PrimaryKey
    @ColumnInfo(name = "id")
    val id: String,

    @ColumnInfo(name = "name")
    val name: String = "Aster",

    @ColumnInfo(name = "avatarUrl")
    val avatarUrl: String = "",

    @ColumnInfo(name = "hairColor")
    val hairColor: String = "Auburn",

    @ColumnInfo(name = "eyeColor")
    val eyeColor: String = "Hazel",

    @ColumnInfo(name = "style")
    val style: String = "Natural",

    @ColumnInfo(name = "voice")
    val voice: String = "Warm voice",

    @ColumnInfo(name = "isActiveOnDevice")
    val isActiveOnDevice: Boolean = true,

    @ColumnInfo(name = "isOnline")
    val isOnline: Boolean = true,

    @ColumnInfo(name = "greeting")
    val greeting: String = "Good evening",

    @ColumnInfo(name = "tagline")
    val tagline: String = "A calmer, brighter you — one step at a time.",

    @ColumnInfo(name = "avatar_config")
    val avatarConfig: String = DEFAULT_AVATAR_CONFIG,

    @ColumnInfo(name = "personality")
    val personality: String = DEFAULT_PERSONALITY_CONFIG,

    @ColumnInfo(name = "created_at")
    val createdAt: Long = System.currentTimeMillis(),

    @ColumnInfo(name = "updatedAt")
    val updatedAt: Long = System.currentTimeMillis()
) {
    val isActive: Boolean get() = isActiveOnDevice

    @Ignore
    constructor(
        id: String,
        name: String,
        voice: String,
        isActive: Boolean
    ) : this(
        id = id,
        name = name,
        avatarUrl = "",
        hairColor = "Auburn",
        eyeColor = "Hazel",
        style = "Natural",
        voice = voice,
        isActiveOnDevice = isActive,
        isOnline = true,
        greeting = "Good evening",
        tagline = "A calmer, brighter you — one step at a time.",
        avatarConfig = DEFAULT_AVATAR_CONFIG,
        personality = DEFAULT_PERSONALITY_CONFIG,
        createdAt = System.currentTimeMillis(),
        updatedAt = System.currentTimeMillis()
    )

    @Ignore
    constructor(
        id: String,
        name: String
    ) : this(
        id = id,
        name = name,
        voice = "Warm voice",
        isActive = true
    )

    fun toDomain(): CompanionProfile = CompanionProfile(
        id = id,
        name = name,
        avatarUrl = avatarUrl,
        hairColor = hairColor,
        eyeColor = eyeColor,
        style = style,
        voice = voice,
        isActiveOnDevice = isActiveOnDevice,
        isOnline = isOnline,
        greeting = greeting,
        tagline = tagline,
        updatedAt = updatedAt
    )

    companion object {
        const val MAX_PROFILES_PER_ACCOUNT = 2

        const val DEFAULT_AVATAR_CONFIG = """{
            "presentation": "feminine",
            "apparentAge": "mid-20s",
            "hairColor": "Auburn",
            "eyeColor": "Hazel",
            "style": "Natural"
        }"""

        const val DEFAULT_PERSONALITY_CONFIG = """{
            "warmth": 0.85,
            "humor": 0.60,
            "formality": 0.30,
            "responseLength": "balanced",
            "initiative": 0.70,
            "interruptibility": 0.90
        }"""

        fun fromDomain(domain: CompanionProfile): ProfileEntity = ProfileEntity(
            id = domain.id,
            name = domain.name,
            avatarUrl = domain.avatarUrl,
            hairColor = domain.hairColor,
            eyeColor = domain.eyeColor,
            style = domain.style,
            voice = domain.voice,
            isActiveOnDevice = domain.isActiveOnDevice,
            isOnline = domain.isOnline,
            greeting = domain.greeting,
            tagline = domain.tagline,
            updatedAt = domain.updatedAt
        )

        fun createDefault(id: String = "profile_1", name: String = "Aster", isActive: Boolean = true): ProfileEntity {
            return ProfileEntity(
                id = id,
                name = name,
                avatarConfig = DEFAULT_AVATAR_CONFIG,
                personality = DEFAULT_PERSONALITY_CONFIG,
                voice = "Warm voice",
                isActiveOnDevice = isActive
            )
        }
    }
}
