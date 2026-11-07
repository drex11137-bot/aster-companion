package com.astercompanion.android.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.MenuBook
import androidx.compose.material.icons.outlined.Bedtime
import androidx.compose.material.icons.outlined.Coffee
import androidx.compose.material.icons.outlined.FitnessCenter
import androidx.compose.material.icons.outlined.Restaurant
import androidx.compose.material3.Icon
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.astercompanion.android.ui.theme.AsterColors
import com.astercompanion.android.ui.theme.AsterTheme

/**
 * Data model for an individual milestone in the schedule timeline.
 */
data class ScheduleTimelineItem(
    val time: String,
    val title: String,
    val description: String,
    val icon: ImageVector
)

/**
 * Standard items exactly matching screenshot 79ffed4b-1317-46e6-98db-6eb6c96f60d6.png:
 * - 9:00 AM Slow morning (Coffee, a good book, no rush)
 * - 11:30 AM Gentle workout (Yoga or a walk outside)
 * - 1:00 PM Lunch (Something fresh and local)
 * - 3:00 PM Personal time (Read, journal, or a creative project)
 * - 7:00 PM Wind down (A quiet evening)
 */
object DefaultScheduleTimeline {
    val items = listOf(
        ScheduleTimelineItem(
            time = "9:00 AM",
            title = "Slow morning",
            description = "Coffee, a good book, no rush",
            icon = Icons.Outlined.Coffee
        ),
        ScheduleTimelineItem(
            time = "11:30 AM",
            title = "Gentle workout",
            description = "Yoga or a walk outside",
            icon = Icons.Outlined.FitnessCenter
        ),
        ScheduleTimelineItem(
            time = "1:00 PM",
            title = "Lunch",
            description = "Something fresh and local",
            icon = Icons.Outlined.Restaurant
        ),
        ScheduleTimelineItem(
            time = "3:00 PM",
            title = "Personal time",
            description = "Read, journal, or a creative project",
            icon = Icons.AutoMirrored.Outlined.MenuBook
        ),
        ScheduleTimelineItem(
            time = "7:00 PM",
            title = "Wind down",
            description = "A quiet evening",
            icon = Icons.Outlined.Bedtime
        )
    )
}

/**
 * ScheduleTimelineCard
 *
 * Implements the card component shown in screenshot 79ffed4b-1317-46e6-98db-6eb6c96f60d6.png.
 * Features:
 * - Surface card `#1C1A18` with rounded corners.
 * - Header: "Saturday, Nov 15", subtitle: "A calm and balanced day".
 * - Connected vertical timeline with continuous joining line and circular icon badges.
 * - Warm amber icon tints and typography hierarchy.
 */
@Composable
fun ScheduleTimelineCard(
    modifier: Modifier = Modifier,
    dateHeader: String = "Saturday, Nov 15",
    dateTitle: String = dateHeader,
    subtitle: String = "A calm and balanced day",
    items: List<ScheduleTimelineItem> = DefaultScheduleTimeline.items,
    cardBackgroundColor: Color = AsterColors.SurfaceCard
) {
    val displayDate = if (dateTitle != "Saturday, Nov 15") dateTitle else dateHeader
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        color = cardBackgroundColor
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 18.dp, vertical = 20.dp)
        ) {
            // Header: Day and Subtitle
            Text(
                text = displayDate,
                color = AsterColors.TextPrimary,
                fontSize = 17.sp,
                fontWeight = FontWeight.SemiBold,
                letterSpacing = (-0.2).sp
            )
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = subtitle,
                color = AsterColors.TextSecondary,
                fontSize = 13.sp,
                fontWeight = FontWeight.Normal
            )

            Spacer(modifier = Modifier.height(18.dp))

            // Connected Vertical Timeline
            val badgeSize = 38.dp
            val lineStrokeWidth = 2.dp
            val lineColor = AsterColors.BorderSubtle

            items.forEachIndexed { index, item ->
                val isFirst = index == 0
                val isLast = index == items.lastIndex

                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(IntrinsicSize.Min)
                ) {
                    // Left Column: Connected line + Circular Badge
                    Box(
                        modifier = Modifier
                            .width(badgeSize)
                            .fillMaxHeight(),
                        contentAlignment = Alignment.TopCenter
                    ) {
                        // Continuous timeline vertical connector
                        Canvas(
                            modifier = Modifier
                                .width(badgeSize)
                                .fillMaxHeight()
                        ) {
                            val centerX = size.width / 2f
                            val badgeRadius = badgeSize.toPx() / 2f

                            val yStart = if (isFirst) badgeRadius else 0f
                            val yEnd = if (isLast) badgeRadius else size.height

                            if (!isFirst || !isLast) {
                                drawLine(
                                    color = lineColor,
                                    start = Offset(centerX, yStart),
                                    end = Offset(centerX, yEnd),
                                    strokeWidth = lineStrokeWidth.toPx()
                                )
                            }
                        }

                        // Circular Icon Badge
                        Box(
                            modifier = Modifier
                                .size(badgeSize)
                                .background(AsterColors.SurfaceContainer, CircleShape),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                imageVector = item.icon,
                                contentDescription = item.title,
                                tint = AsterColors.AmberPrimary,
                                modifier = Modifier.size(18.dp)
                            )
                        }
                    }

                    Spacer(modifier = Modifier.width(14.dp))

                    // Right Column: Time, Title, and Description
                    Column(
                        modifier = Modifier
                            .weight(1f)
                            .padding(bottom = if (isLast) 0.dp else 20.dp)
                    ) {
                        Text(
                            text = item.time,
                            color = AsterColors.IconMuted,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Medium,
                            letterSpacing = 0.2.sp
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = item.title,
                            color = AsterColors.TextPrimary,
                            fontSize = 15.sp,
                            fontWeight = FontWeight.SemiBold
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = item.description,
                            color = AsterColors.TextSecondary,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Normal,
                            lineHeight = 18.sp
                        )
                    }
                }
            }
        }
    }
}

// ==========================================
// Jetpack Compose Previews
// ==========================================

@Preview(name = "Schedule Timeline Card - Pixel Perfect", showBackground = true, backgroundColor = 0xFF121110)
@Composable
fun PreviewScheduleTimelineCard() {
    AsterTheme {
        Box(modifier = Modifier.padding(16.dp)) {
            ScheduleTimelineCard()
        }
    }
}
