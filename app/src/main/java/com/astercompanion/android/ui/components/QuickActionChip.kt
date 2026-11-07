package com.astercompanion.android.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.CalendarToday
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
 * Model for a quick action chip.
 */
data class QuickActionItem(
    val id: String,
    val label: String,
    val icon: ImageVector
)

/**
 * Standard quick actions matching screenshot 79ffed4b-1317-46e6-98db-6eb6c96f60d6.png:
 * - "📅 Add reminder"
 * - "📄 Summarize"
 */
object DefaultQuickActions {
    val REMINDER = QuickActionItem("reminder", "Add reminder", Icons.Outlined.CalendarToday)
    val SUMMARIZE = QuickActionItem("summarize", "Summarize", Icons.Outlined.Description)

    val list = listOf(REMINDER, SUMMARIZE)
}

/**
 * QuickActionChip
 *
 * Implements the quick action suggestions shown above the chat input composer
 * in screenshot 79ffed4b-1317-46e6-98db-6eb6c96f60d6.png.
 */
@Composable
fun QuickActionChip(
    modifier: Modifier = Modifier,
    label: String,
    icon: ImageVector,
    backgroundColor: Color = AsterColors.SurfaceElevated,
    borderColor: Color = AsterColors.BorderSubtle,
    textColor: Color = AsterColors.TextPrimary,
    iconTint: Color = AsterColors.TextPrimary,
    onClick: () -> Unit
) {
    val pillShape = RoundedCornerShape(50)

    Box(
        modifier = modifier
            .clip(pillShape)
            .background(backgroundColor, pillShape)
            .border(1.dp, borderColor, pillShape)
            .clickable(onClick = onClick)
            .padding(horizontal = 14.dp, vertical = 8.dp),
        contentAlignment = Alignment.Center
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = iconTint,
                modifier = Modifier.size(16.dp)
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = label,
                color = textColor,
                fontSize = 13.sp,
                fontWeight = FontWeight.Medium,
                letterSpacing = 0.1.sp
            )
        }
    }
}

/**
 * Horizontal row of QuickActionChips as seen above the chat message composer.
 */
@Composable
fun QuickActionChipsRow(
    modifier: Modifier = Modifier,
    actions: List<QuickActionItem> = DefaultQuickActions.list,
    onActionClick: (QuickActionItem) -> Unit = {}
) {
    Row(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(10.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        actions.forEach { action ->
            QuickActionChip(
                label = action.label,
                icon = action.icon,
                onClick = { onActionClick(action) }
            )
        }
    }
}

// ==========================================
// Jetpack Compose Previews
// ==========================================

@Preview(name = "Quick Action Chips Row - Screenshot Match", showBackground = true, backgroundColor = 0xFF121110)
@Composable
fun PreviewQuickActionChips() {
    AsterTheme {
        Box(modifier = Modifier.padding(16.dp)) {
            QuickActionChipsRow()
        }
    }
}
