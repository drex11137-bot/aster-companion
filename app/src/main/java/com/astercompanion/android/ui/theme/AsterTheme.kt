package com.astercompanion.android.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

/**
 * Design system color tokens for Aster Companion.
 * Strictly adhering to PRD v1.1 §8 and UI reference PNG screenshots:
 * - 79ffed4b-1317-46e6-98db-6eb6c96f60d6.png (Chat & Schedule timeline)
 * - 56d6d982-5337-4170-80e5-1e156d239b38.png (Memories card list)
 * - 56539447-5086-44aa-b0ad-b98fa9cb6a8d.png (Today screen & tasks)
 * - a98599e6-e707-4cb8-a85f-85293d19df71.png (Companion studio & swatches)
 */
object AsterColors {
    // Background and surfaces
    val Background = Color(0xFF121110)
    val SurfaceCard = Color(0xFF1C1A18)
    val SurfaceElevated = Color(0xFF25211C)
    val SurfaceContainer = Color(0xFF2A231C)
    val BorderSubtle = Color(0xFF352E27)
    val BorderActive = Color(0xFFE59843)

    // Warm amber bloom and accents
    val AmberPrimary = Color(0xFFE59843)
    val AmberBright = Color(0xFFF5A623)
    val AmberGlowOuter = Color(0xFFF5A623)
    val AmberGlowInner = Color(0xFFE59843)
    val AmberContainer = Color(0xFF2E2214)

    // Status colors
    val OnlineGreen = Color(0xFF4CD964)
    val OfflineGrey = Color(0xFF8E8A83)

    // Typography ink tokens
    val TextPrimary = Color(0xFFF5F2EB)
    val TextSecondary = Color(0xFF8E8A83)
    val TextMuted = Color(0xFF6E6A63)
    val TextOnAmber = Color(0xFF1C1A18)

    // Icon colors
    val IconMuted = Color(0xFFA8A39D)
    val IconAmber = Color(0xFFE59843)

    // Hair swatch colors (Screenshot a98599e6)
    val HairAuburn = Color(0xFF8B4513)
    val HairBlack = Color(0xFF1F1F1F)
    val HairBrown = Color(0xFF4A2E1B)
    val HairBlonde = Color(0xFFD4B07B)
    val HairSilver = Color(0xFF8C9099)

    // Eye swatch colors (Screenshot a98599e6)
    val EyeHazel = Color(0xFF7A5826)
    val EyeBrown = Color(0xFF3B2219)
    val EyeBlue = Color(0xFF5B84A8)
    val EyeGreen = Color(0xFF5C6B47)
    val EyeGrey = Color(0xFF7B8189)
}

private val DarkColorScheme = darkColorScheme(
    primary = AsterColors.AmberPrimary,
    onPrimary = AsterColors.TextOnAmber,
    primaryContainer = AsterColors.AmberContainer,
    onPrimaryContainer = AsterColors.AmberBright,
    background = AsterColors.Background,
    onBackground = AsterColors.TextPrimary,
    surface = AsterColors.SurfaceCard,
    onSurface = AsterColors.TextPrimary,
    surfaceVariant = AsterColors.SurfaceElevated,
    onSurfaceVariant = AsterColors.TextSecondary,
    outline = AsterColors.BorderSubtle,
    outlineVariant = AsterColors.BorderSubtle
)

@Composable
fun AsterTheme(
    @Suppress("UNUSED_PARAMETER") darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = DarkColorScheme,
        content = content
    )
}
