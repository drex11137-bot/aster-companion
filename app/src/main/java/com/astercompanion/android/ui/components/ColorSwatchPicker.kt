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
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
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
 * Data model for a color swatch option.
 */
data class SwatchOption(
    val label: String,
    val color: Color
)

/**
 * Standard Hair & Eye color palettes strictly matching screenshot a98599e6-e707-4cb8-a85f-85293d19df71.png:
 * - Hair: Auburn, Black, Brown, Blonde, Silver
 * - Eyes: Hazel, Brown, Blue, Green, Grey
 */
object DefaultSwatches {
    val HairSwatches = listOf(
        SwatchOption(CompanionProfile.HAIR_AUBURN, AsterColors.HairAuburn),
        SwatchOption(CompanionProfile.HAIR_BLACK, AsterColors.HairBlack),
        SwatchOption(CompanionProfile.HAIR_BROWN, AsterColors.HairBrown),
        SwatchOption(CompanionProfile.HAIR_BLONDE, AsterColors.HairBlonde),
        SwatchOption(CompanionProfile.HAIR_SILVER, AsterColors.HairSilver)
    )

    val EyeSwatches = listOf(
        SwatchOption(CompanionProfile.EYE_HAZEL, AsterColors.EyeHazel),
        SwatchOption(CompanionProfile.EYE_BROWN, AsterColors.EyeBrown),
        SwatchOption(CompanionProfile.EYE_BLUE, AsterColors.EyeBlue),
        SwatchOption(CompanionProfile.EYE_GREEN, AsterColors.EyeGreen),
        SwatchOption(CompanionProfile.EYE_GREY, AsterColors.EyeGrey)
    )
}

/**
 * ColorSwatchItem
 *
 * Implements a single circular color swatch with an animated outer selection ring
 * and text label underneath.
 */
@Composable
fun ColorSwatchItem(
    modifier: Modifier = Modifier,
    swatch: SwatchOption,
    isSelected: Boolean,
    onClick: () -> Unit
) {
    val selectionRingColor by animateColorAsState(
        targetValue = if (isSelected) AsterColors.AmberPrimary else Color.Transparent,
        label = "swatchRingColor"
    )
    val labelColor by animateColorAsState(
        targetValue = if (isSelected) AsterColors.AmberPrimary else AsterColors.TextSecondary,
        label = "swatchLabelColor"
    )

    Column(
        modifier = modifier
            .clickable(onClick = onClick),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        // Swatch container with optional selection ring
        Box(
            modifier = Modifier
                .size(44.dp)
                .then(
                    if (isSelected) {
                        Modifier.border(2.dp, selectionRingColor, CircleShape)
                    } else {
                        Modifier
                    }
                ),
            contentAlignment = Alignment.Center
        ) {
            // Inner color circle
            Box(
                modifier = Modifier
                    .size(if (isSelected) 34.dp else 38.dp)
                    .clip(CircleShape)
                    .background(swatch.color, CircleShape)
                    // Very subtle hairline border for dark colors like Black to remain visible
                    .border(0.5.dp, AsterColors.BorderSubtle, CircleShape)
            )
        }

        Spacer(modifier = Modifier.height(6.dp))

        // Label below swatch
        Text(
            text = swatch.label,
            color = labelColor,
            fontSize = 12.sp,
            fontWeight = if (isSelected) FontWeight.Medium else FontWeight.Normal
        )
    }
}

/**
 * ColorSwatchPicker
 *
 * Implements a full swatch picker section (e.g. Hair or Eyes) matching
 * screenshot a98599e6-e707-4cb8-a85f-85293d19df71.png.
 */
@Composable
fun ColorSwatchPicker(
    modifier: Modifier = Modifier,
    title: String,
    swatches: List<SwatchOption>,
    selectedLabel: String,
    onSwatchSelected: (SwatchOption) -> Unit
) {
    Column(modifier = modifier.fillMaxWidth()) {
        Text(
            text = title,
            color = AsterColors.TextPrimary,
            fontSize = 14.sp,
            fontWeight = FontWeight.Medium
        )

        Spacer(modifier = Modifier.height(12.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            swatches.forEach { swatch ->
                ColorSwatchItem(
                    swatch = swatch,
                    isSelected = swatch.label.equals(selectedLabel, ignoreCase = true),
                    onClick = { onSwatchSelected(swatch) }
                )
            }
        }
    }
}

// ==========================================
// Jetpack Compose Previews
// ==========================================

@Preview(name = "Hair and Eye Swatch Pickers - Screenshot Match", showBackground = true, backgroundColor = 0xFF121110)
@Composable
fun PreviewColorSwatchPickers() {
    AsterTheme {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp)
        ) {
            ColorSwatchPicker(
                title = "Hair",
                swatches = DefaultSwatches.HairSwatches,
                selectedLabel = "Auburn",
                onSwatchSelected = {}
            )

            Spacer(modifier = Modifier.height(24.dp))

            ColorSwatchPicker(
                title = "Eyes",
                swatches = DefaultSwatches.EyeSwatches,
                selectedLabel = "Hazel",
                onSwatchSelected = {}
            )
        }
    }
}
