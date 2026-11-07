package com.astercompanion.android.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Description
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.astercompanion.android.ui.theme.AsterColors
import com.astercompanion.android.ui.theme.AsterTheme

/**
 * CitationChip
 *
 * Implements the memory citation pill chip shown under Aster's responses
 * in screenshot 79ffed4b-1317-46e6-98db-6eb6c96f60d6.png ("📄 Used 2 memories").
 *
 * Allows users to inspect exactly which memories were used for context grounding.
 */
@Composable
fun CitationChip(
    modifier: Modifier = Modifier,
    text: String = "Used 2 memories",
    icon: ImageVector = Icons.Outlined.Description,
    backgroundColor: Color = AsterColors.SurfaceElevated,
    borderColor: Color = AsterColors.BorderSubtle,
    textColor: Color = AsterColors.TextSecondary,
    iconTint: Color = AsterColors.IconMuted,
    onClick: (() -> Unit)? = null
) {
    val pillShape = RoundedCornerShape(50)

    Box(
        modifier = modifier
            .clip(pillShape)
            .background(backgroundColor, pillShape)
            .border(1.dp, borderColor, pillShape)
            .then(
                if (onClick != null) {
                    Modifier.clickable(onClick = onClick)
                } else {
                    Modifier
                }
            )
            .padding(horizontal = 12.dp, vertical = 6.dp),
        contentAlignment = Alignment.Center
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = iconTint,
                modifier = Modifier.size(14.dp)
            )
            Spacer(modifier = Modifier.width(6.dp))
            Text(
                text = text,
                color = textColor,
                fontSize = 12.sp,
                fontWeight = FontWeight.Medium,
                letterSpacing = 0.1.sp
            )
        }
    }
}

/**
 * Convenience overload accepting memory count.
 */
@Composable
fun CitationChip(
    memoryCount: Int,
    modifier: Modifier = Modifier,
    onClick: (() -> Unit)? = null
) {
    val label = if (memoryCount == 1) "Used 1 memory" else "Used $memoryCount memories"
    CitationChip(
        modifier = modifier,
        text = label,
        onClick = onClick
    )
}

// ==========================================
// Jetpack Compose Previews
// ==========================================

@Preview(name = "Citation Chip - Screenshot Match", showBackground = true, backgroundColor = 0xFF121110)
@Composable
fun PreviewCitationChip() {
    AsterTheme {
        Box(modifier = Modifier.padding(16.dp)) {
            CitationChip(memoryCount = 2)
        }
    }
}
