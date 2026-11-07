package com.astercompanion.android.ui.components

import androidx.compose.animation.animateColorAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.astercompanion.android.model.CompanionProfile
import com.astercompanion.android.ui.theme.AsterColors
import com.astercompanion.android.ui.theme.AsterTheme

/**
 * Visual presentation style for [OptionFilterChip].
 */
enum class OptionChipStyle {
    /**
     * Outlined style used in Companion Studio (Screenshot a98599e6):
     * Selected state uses amber border outline and warm text.
     */
    Outlined,

    /**
     * Filled style used in Memory Categories (Screenshot 56d6d982):
     * Selected state uses solid amber background and dark text.
     */
    Filled
}

/**
 * OptionFilterChip
 *
 * Implements pill chips for Style & Voice in Companion Studio (Screenshot a98599e6)
 * and category filtering in Memories (Screenshot 56d6d982).
 */
@Composable
fun OptionFilterChip(
    modifier: Modifier = Modifier,
    label: String,
    isSelected: Boolean,
    style: OptionChipStyle = OptionChipStyle.Outlined,
    onClick: () -> Unit
) {
    val pillShape = RoundedCornerShape(50)

    val targetBgColor = when (style) {
        OptionChipStyle.Outlined -> AsterColors.SurfaceCard
        OptionChipStyle.Filled -> if (isSelected) AsterColors.AmberPrimary else AsterColors.SurfaceCard
    }

    val targetBorderColor = when (style) {
        OptionChipStyle.Outlined -> if (isSelected) AsterColors.AmberPrimary else AsterColors.BorderSubtle
        OptionChipStyle.Filled -> if (isSelected) AsterColors.AmberPrimary else AsterColors.BorderSubtle
    }

    val targetTextColor = when (style) {
        OptionChipStyle.Outlined -> if (isSelected) AsterColors.AmberPrimary else AsterColors.TextPrimary
        OptionChipStyle.Filled -> if (isSelected) AsterColors.TextOnAmber else AsterColors.TextPrimary
    }

    val animatedBgColor by animateColorAsState(targetValue = targetBgColor, label = "chipBgColor")
    val animatedBorderColor by animateColorAsState(targetValue = targetBorderColor, label = "chipBorderColor")
    val animatedTextColor by animateColorAsState(targetValue = targetTextColor, label = "chipTextColor")

    Box(
        modifier = modifier
            .clip(pillShape)
            .background(animatedBgColor, pillShape)
            .border(
                width = if (isSelected && style == OptionChipStyle.Outlined) 1.5.dp else 1.dp,
                color = animatedBorderColor,
                shape = pillShape
            )
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 9.dp),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = label,
            color = animatedTextColor,
            fontSize = 13.sp,
            fontWeight = if (isSelected) FontWeight.SemiBold else FontWeight.Normal,
            letterSpacing = 0.1.sp
        )
    }
}

/**
 * OptionFilterSection
 *
 * Section with title label (e.g. "Style", "Voice") and horizontal row of chips.
 */
@Composable
fun OptionFilterSection(
    modifier: Modifier = Modifier,
    title: String,
    options: List<String>,
    selectedOption: String,
    style: OptionChipStyle = OptionChipStyle.Outlined,
    onOptionSelected: (String) -> Unit
) {
    Column(modifier = modifier.fillMaxWidth()) {
        Text(
            text = title,
            color = AsterColors.TextPrimary,
            fontSize = 14.sp,
            fontWeight = FontWeight.Medium
        )

        Spacer(modifier = Modifier.height(10.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            options.forEach { option ->
                OptionFilterChip(
                    label = option,
                    isSelected = option.equals(selectedOption, ignoreCase = true),
                    style = style,
                    onClick = { onOptionSelected(option) }
                )
            }
        }
    }
}

// ==========================================
// Jetpack Compose Previews
// ==========================================

@Preview(name = "Style and Voice Option Chips - Screenshot a98599e6", showBackground = true, backgroundColor = 0xFF121110)
@Composable
fun PreviewOptionFilterSectionStudio() {
    AsterTheme {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp)
        ) {
            OptionFilterSection(
                title = "Style",
                options = CompanionProfile.ALL_STYLES,
                selectedOption = CompanionProfile.STYLE_NATURAL,
                style = OptionChipStyle.Outlined,
                onOptionSelected = {}
            )

            Spacer(modifier = Modifier.height(20.dp))

            OptionFilterSection(
                title = "Voice",
                options = CompanionProfile.ALL_VOICES,
                selectedOption = CompanionProfile.VOICE_WARM,
                style = OptionChipStyle.Outlined,
                onOptionSelected = {}
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Memory categories in Filled style (Screenshot 56d6d982)
            OptionFilterSection(
                title = "Memory Filter (Filled Style)",
                options = listOf("All", "People", "Preferences", "Plans"),
                selectedOption = "All",
                style = OptionChipStyle.Filled,
                onOptionSelected = {}
            )
        }
    }
}
