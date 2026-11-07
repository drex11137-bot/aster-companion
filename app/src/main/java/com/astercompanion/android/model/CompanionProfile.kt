package com.astercompanion.android.model

/**
 * Model representing a Companion Profile in Aster Companion.
 * Adheres to PRD v1.1 §9:
 * - Maximum two companion profiles per account ("Aster" and "Nova").
 * - Each profile maintains strict data isolation (memories, chat history, preferences).
 * - Enforces active profile constraint: only 1 profile can be active on this device at any time.
 */
data class CompanionProfile(
    val id: String,
    val name: String,
    val avatarUrl: String = "",
    val hairColor: String = HAIR_AUBURN,
    val eyeColor: String = EYE_HAZEL,
    val style: String = STYLE_NATURAL,
    val voice: String = VOICE_WARM,
    val isActiveOnDevice: Boolean = false,
    val isOnline: Boolean = true,
    val greeting: String = "Good evening, Maya",
    val tagline: String = "A calmer, brighter you — one step at a time.",
    val updatedAt: Long = System.currentTimeMillis()
) {
    companion object {
        const val PROFILE_ASTER_ID = "profile_aster"
        const val PROFILE_NOVA_ID = "profile_nova"

        // Hair colors from Design System & Studio Reference (Screenshot a98599e6)
        const val HAIR_AUBURN = "Auburn"
        const val HAIR_BLACK = "Black"
        const val HAIR_BROWN = "Brown"
        const val HAIR_BLONDE = "Blonde"
        const val HAIR_SILVER = "Silver"
        val ALL_HAIR_COLORS = listOf(HAIR_AUBURN, HAIR_BLACK, HAIR_BROWN, HAIR_BLONDE, HAIR_SILVER)

        // Eye colors from Design System & Studio Reference (Screenshot a98599e6)
        const val EYE_HAZEL = "Hazel"
        const val EYE_BROWN = "Brown"
        const val EYE_BLUE = "Blue"
        const val EYE_GREEN = "Green"
        const val EYE_GREY = "Grey"
        val ALL_EYE_COLORS = listOf(EYE_HAZEL, EYE_BROWN, EYE_BLUE, EYE_GREEN, EYE_GREY)

        // Styles from Design System & Studio Reference (Screenshot a98599e6)
        const val STYLE_NATURAL = "Natural"
        const val STYLE_CASUAL = "Casual"
        const val STYLE_PROFESSIONAL = "Professional"
        const val STYLE_CREATIVE = "Creative"
        val ALL_STYLES = listOf(STYLE_NATURAL, STYLE_CASUAL, STYLE_PROFESSIONAL, STYLE_CREATIVE)

        // Voices from Design System & Studio Reference (Screenshot a98599e6)
        const val VOICE_WARM = "Warm voice"
        const val VOICE_CALM = "Calm"
        const val VOICE_ENERGETIC = "Energetic"
        const val VOICE_PLAYFUL = "Playful"
        val ALL_VOICES = listOf(VOICE_WARM, VOICE_CALM, VOICE_ENERGETIC, VOICE_PLAYFUL)

        fun defaultAster(): CompanionProfile = CompanionProfile(
            id = PROFILE_ASTER_ID,
            name = "Aster",
            avatarUrl = "avatar_aster_default.png",
            hairColor = HAIR_AUBURN,
            eyeColor = EYE_HAZEL,
            style = STYLE_NATURAL,
            voice = VOICE_WARM,
            isActiveOnDevice = true,
            isOnline = true,
            greeting = "Good evening, Maya",
            tagline = "A calmer, brighter you — one step at a time."
        )

        fun defaultNova(): CompanionProfile = CompanionProfile(
            id = PROFILE_NOVA_ID,
            name = "Nova",
            avatarUrl = "avatar_nova_default.png",
            hairColor = HAIR_BLACK,
            eyeColor = EYE_BLUE,
            style = STYLE_CREATIVE,
            voice = VOICE_PLAYFUL,
            isActiveOnDevice = false,
            isOnline = true,
            greeting = "Hello, Maya",
            tagline = "Creative energy for inspired thinking."
        )
    }
}
