package com.astercompanion.android.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val DarkColorScheme = darkColorScheme(
    primary = AsterAmber,
    onPrimary = AsterBackground,
    primaryContainer = AsterAmberContainer,
    onPrimaryContainer = AsterAmberBright,
    secondary = AsterVioletUserBubble,
    onSecondary = AsterTextPrimary,
    secondaryContainer = AsterVioletDark,
    onSecondaryContainer = AsterVioletLight,
    background = AsterBackground,
    onBackground = AsterTextPrimary,
    surface = AsterSurface,
    onSurface = AsterTextPrimary,
    surfaceVariant = AsterSurfaceElevated,
    onSurfaceVariant = AsterTextSecondary,
    outline = AsterSurfaceBorder,
    outlineVariant = AsterSurfaceBorder
)

@Composable
fun AsterCompanionTheme(
    @Suppress("UNUSED_PARAMETER") darkTheme: Boolean = isSystemInDarkTheme(),
    content: @Composable () -> Unit
) {
    // Aster Companion is dark-first by architectural mandate (Dark Graphite #121110)
    val colorScheme = DarkColorScheme

    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as? Activity)?.window
            if (window != null) {
                @Suppress("DEPRECATION")
                window.statusBarColor = AsterBackground.toArgb()
                @Suppress("DEPRECATION")
                window.navigationBarColor = AsterBackground.toArgb()
                val windowInsetsController = WindowCompat.getInsetsController(window, view)
                // Dark background requires light status/nav bar icons
                windowInsetsController.isAppearanceLightStatusBars = false
                windowInsetsController.isAppearanceLightNavigationBars = false
            }
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = AsterTypography,
        content = content
    )
}
