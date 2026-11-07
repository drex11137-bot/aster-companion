package com.astercompanion.android.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Add
import androidx.compose.material.icons.outlined.BookmarkBorder
import androidx.compose.material.icons.automirrored.outlined.DirectionsRun
import androidx.compose.material.icons.outlined.Add
import androidx.compose.material.icons.outlined.BookmarkBorder
import androidx.compose.material.icons.outlined.DeleteOutline
import androidx.compose.material.icons.outlined.Edit
import androidx.compose.material.icons.outlined.PersonOutline
import androidx.compose.material.icons.outlined.WbSunny
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.astercompanion.android.model.MemoryItem
import com.astercompanion.android.ui.theme.AsterColors
import com.astercompanion.android.ui.theme.AsterTheme

/**
 * Maps memory icon type string identifiers to their respective vector icons.
 */
fun resolveMemoryIcon(iconType: String): ImageVector {
    return when (iconType.lowercase()) {
        MemoryItem.ICON_SUN, "morning" -> Icons.Outlined.WbSunny
        MemoryItem.ICON_PERSON, "people", "contact" -> Icons.Outlined.PersonOutline
        MemoryItem.ICON_PLUS, "health", "medical" -> Icons.Outlined.Add
        MemoryItem.ICON_RUN, "plans", "fitness", "sport" -> Icons.AutoMirrored.Outlined.DirectionsRun
        MemoryItem.ICON_BOOKMARK -> Icons.Outlined.BookmarkBorder
        else -> Icons.Outlined.WbSunny
    }
}

/**
 * MemoryCardItem
 *
 * Implements the card component strictly matching screenshot 56d6d982-5337-4170-80e5-1e156d239b38.png:
 * - Surface card `#1C1A18`, rounded corners (`16.dp`).
 * - Left circular category icon badge (sun, person, plus/medical, runner) with warm amber tint `#E59843`.
 * - Title (e.g. "Prefers short answers in the morning", "Dad's number saved", "Allergic to peanuts").
 * - Added timestamp (e.g. "Added 3 days ago", "Added 1 week ago").
 * - Action buttons on the right: Pencil (edit) and Trash can (delete).
 */
@Composable
fun MemoryCardItem(
    modifier: Modifier = Modifier,
    title: String,
    addedAgoLabel: String,
    iconType: String = MemoryItem.ICON_SUN,
    customIcon: ImageVector? = null,
    cardBackgroundColor: Color = AsterColors.SurfaceCard,
    onEditClick: () -> Unit = {},
    onDeleteClick: () -> Unit = {},
    onClick: (() -> Unit)? = null
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .then(
                if (onClick != null) {
                    Modifier.clickable(onClick = onClick)
                } else {
                    Modifier
                }
            ),
        shape = RoundedCornerShape(16.dp),
        color = cardBackgroundColor
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 14.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Left circular category icon badge
            val iconVector = customIcon ?: resolveMemoryIcon(iconType)
            Box(
                modifier = Modifier
                    .size(44.dp)
                    .background(AsterColors.SurfaceContainer, CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Icon(
                    imageVector = iconVector,
                    contentDescription = iconType,
                    tint = AsterColors.AmberPrimary,
                    modifier = Modifier.size(22.dp)
                )
            }

            Spacer(modifier = Modifier.width(14.dp))

            // Center Content: Title and Added timestamp
            Column(
                modifier = Modifier.weight(1f)
            ) {
                Text(
                    text = title,
                    color = AsterColors.TextPrimary,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.SemiBold,
                    lineHeight = 20.sp,
                    maxLines = 2,
                    overflow = TextOverflow.Ellipsis
                )
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    text = addedAgoLabel,
                    color = AsterColors.TextSecondary,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Normal
                )
            }

            Spacer(modifier = Modifier.width(8.dp))

            // Action buttons: Pencil (Edit) and Trash can (Delete)
            Row(
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(
                    onClick = onEditClick,
                    modifier = Modifier.size(40.dp)
                ) {
                    Icon(
                        imageVector = Icons.Outlined.Edit,
                        contentDescription = "Edit memory: $title",
                        tint = AsterColors.IconMuted,
                        modifier = Modifier.size(20.dp)
                    )
                }

                IconButton(
                    onClick = onDeleteClick,
                    modifier = Modifier.size(40.dp)
                ) {
                    Icon(
                        imageVector = Icons.Outlined.DeleteOutline,
                        contentDescription = "Delete memory: $title",
                        tint = AsterColors.IconMuted,
                        modifier = Modifier.size(20.dp)
                    )
                }
            }
        }
    }
}

/**
 * Overload accepting domain model [MemoryItem].
 */
@Composable
fun MemoryCardItem(
    item: MemoryItem,
    modifier: Modifier = Modifier,
    onEditClick: (MemoryItem) -> Unit = {},
    onDeleteClick: (MemoryItem) -> Unit = {},
    onClick: ((MemoryItem) -> Unit)? = null
) {
    MemoryCardItem(
        modifier = modifier,
        title = item.title,
        addedAgoLabel = item.addedAgoLabel,
        iconType = item.iconType,
        onEditClick = { onEditClick(item) },
        onDeleteClick = { onDeleteClick(item) },
        onClick = if (onClick != null) { { onClick(item) } } else null
    )
}

// ==========================================
// Jetpack Compose Previews
// ==========================================

@Preview(name = "Memories List - Screenshot Match", showBackground = true, backgroundColor = 0xFF121110)
@Composable
fun PreviewMemoryCardItemList() {
    AsterTheme {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            MemoryCardItem(
                title = "Prefers short answers in the morning",
                addedAgoLabel = "Added 3 days ago",
                iconType = MemoryItem.ICON_SUN
            )
            Spacer(modifier = Modifier.height(10.dp))
            MemoryCardItem(
                title = "Dad's number saved",
                addedAgoLabel = "Added 1 week ago",
                iconType = MemoryItem.ICON_PERSON
            )
            Spacer(modifier = Modifier.height(10.dp))
            MemoryCardItem(
                title = "Allergic to peanuts",
                addedAgoLabel = "Added 2 weeks ago",
                iconType = MemoryItem.ICON_PLUS
            )
            Spacer(modifier = Modifier.height(10.dp))
            MemoryCardItem(
                title = "Running a half marathon in March",
                addedAgoLabel = "Added 3 weeks ago",
                iconType = MemoryItem.ICON_RUN
            )
        }
    }
}
