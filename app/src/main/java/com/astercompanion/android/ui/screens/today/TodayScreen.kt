package com.astercompanion.android.ui.screens.today

import androidx.compose.animation.animateColorAsState
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.outlined.CalendarMonth
import androidx.compose.material.icons.outlined.ChevronRight
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.astercompanion.android.model.CompanionTask
import com.astercompanion.android.model.RecentMemoryCard
import com.astercompanion.android.model.Reminder
import com.astercompanion.android.ui.components.AvatarWithGlow
import com.astercompanion.android.ui.theme.AsterAmber
import com.astercompanion.android.ui.theme.AsterBackground
import com.astercompanion.android.ui.theme.AsterCompanionTheme
import com.astercompanion.android.ui.theme.AsterOnlineGreen
import com.astercompanion.android.ui.theme.AsterSurface
import com.astercompanion.android.ui.theme.AsterSurfaceBorder
import com.astercompanion.android.ui.theme.AsterTextMuted
import com.astercompanion.android.ui.theme.AsterTextPrimary
import com.astercompanion.android.ui.theme.AsterTextSecondary
import com.astercompanion.android.ui.theme.AsterVioletText

@Composable
fun TodayScreen(
    onNavigateToMemories: () -> Unit = {},
    onNavigateToChat: () -> Unit = {},
    onNavigateToSettings: () -> Unit = {},
    viewModel: TodayViewModel = viewModel(),
    modifier: Modifier = Modifier
) {
    val state by viewModel.uiState.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(state.isSnoozedFeedback) {
        state.isSnoozedFeedback?.let { msg ->
            snackbarHostState.showSnackbar(msg)
            viewModel.dismissFeedback()
        }
    }

    TodayScreenContent(
        state = state,
        onSnoozeReminder = viewModel::snoozeReminder,
        onToggleTask = viewModel::toggleTask,
        onNavigateToMemories = onNavigateToMemories,
        onNavigateToChat = onNavigateToChat,
        onNavigateToSettings = onNavigateToSettings,
        snackbarHostState = snackbarHostState,
        modifier = modifier
    )
}

@Composable
fun TodayScreenContent(
    state: TodayUiState,
    onSnoozeReminder: () -> Unit = {},
    onToggleTask: (String) -> Unit = {},
    onNavigateToMemories: () -> Unit = {},
    onNavigateToChat: () -> Unit = {},
    onNavigateToSettings: () -> Unit = {},
    snackbarHostState: SnackbarHostState = remember { SnackbarHostState() },
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(AsterBackground)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(scrollState)
                .statusBarsPadding()
                .padding(horizontal = 20.dp, vertical = 16.dp)
        ) {
            // Header: Avatar with Glow, Greeting, Status, Settings Icon
            Row(
                modifier = Modifier.fillMaxWidth(),
                verticalAlignment = Alignment.CenterVertically
            ) {
                AvatarWithGlow(
                    size = 56.dp,
                    showOnlineDot = true,
                    showGlow = true,
                    onClick = onNavigateToChat
                )

                Spacer(modifier = Modifier.width(16.dp))

                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = state.greeting,
                        color = AsterTextPrimary,
                        fontSize = 22.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = (-0.3).sp
                    )

                    Spacer(modifier = Modifier.height(2.dp))

                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .size(8.dp)
                                .clip(CircleShape)
                                .background(if (state.isOnline) AsterOnlineGreen else AsterTextMuted)
                        )
                        Spacer(modifier = Modifier.width(6.dp))
                        Text(
                            text = "${state.companionName} is online",
                            color = AsterTextSecondary,
                            fontSize = 13.sp
                        )
                    }
                }

                IconButton(
                    onClick = onNavigateToSettings,
                    modifier = Modifier.size(40.dp)
                ) {
                    Icon(
                        imageVector = Icons.Outlined.Settings,
                        contentDescription = "Settings",
                        tint = AsterTextSecondary
                    )
                }
            }

            Spacer(modifier = Modifier.height(18.dp))

            // Subtitle Tagline
            Text(
                text = state.tagline,
                color = AsterTextSecondary,
                fontSize = 14.sp,
                lineHeight = 20.sp
            )

            Spacer(modifier = Modifier.height(22.dp))

            // Section 1: Next Reminder Card
            state.nextReminder?.let { reminder ->
                NextReminderCard(
                    reminder = reminder,
                    onSnooze = onSnoozeReminder
                )
            }

            Spacer(modifier = Modifier.height(28.dp))

            // Section 2: Your Tasks
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Your tasks",
                    color = AsterTextPrimary,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.SemiBold
                )

                Row(
                    modifier = Modifier.clickable { onNavigateToChat() },
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "See all",
                        color = AsterVioletText,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Medium
                    )
                    Spacer(modifier = Modifier.width(2.dp))
                    Icon(
                        imageVector = Icons.Outlined.ChevronRight,
                        contentDescription = "See all tasks",
                        tint = AsterVioletText,
                        modifier = Modifier.size(16.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            TasksListCard(
                tasks = state.tasks,
                onToggleTask = onToggleTask
            )

            Spacer(modifier = Modifier.height(28.dp))

            // Section 3: Recent Memories
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Recent memories",
                    color = AsterTextPrimary,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.SemiBold
                )

                Row(
                    modifier = Modifier.clickable { onNavigateToMemories() },
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "See all",
                        color = AsterVioletText,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Medium
                    )
                    Spacer(modifier = Modifier.width(2.dp))
                    Icon(
                        imageVector = Icons.Outlined.ChevronRight,
                        contentDescription = "See all memories",
                        tint = AsterVioletText,
                        modifier = Modifier.size(16.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            RecentMemoriesHorizontalRow(
                memories = state.recentMemories,
                onMemoryClick = { onNavigateToMemories() }
            )

            Spacer(modifier = Modifier.height(80.dp))
        }

        SnackbarHost(
            hostState = snackbarHostState,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = 80.dp)
        )
    }
}

@Composable
private fun NextReminderCard(
    reminder: Reminder,
    onSnooze: () -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        color = AsterSurface
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 18.dp, vertical = 20.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Calendar icon outline in warm amber
            Icon(
                imageVector = Icons.Outlined.CalendarMonth,
                contentDescription = "Reminder Calendar",
                tint = AsterAmber,
                modifier = Modifier.size(28.dp)
            )

            Spacer(modifier = Modifier.width(16.dp))

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = "Next reminder",
                    color = AsterTextSecondary,
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Normal
                )

                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = reminder.title,
                    color = AsterTextPrimary,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.SemiBold
                )

                Spacer(modifier = Modifier.height(2.dp))

                Text(
                    text = if (reminder.isSnoozed) "${reminder.dayLabel} • Snoozed" else reminder.dayLabel,
                    color = if (reminder.isSnoozed) AsterAmber else AsterTextSecondary,
                    fontSize = 13.sp
                )
            }

            Spacer(modifier = Modifier.width(12.dp))

            // Amber rounded pill button: "Snooze"
            Button(
                onClick = onSnooze,
                shape = RoundedCornerShape(24.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (reminder.isSnoozed) AsterSurfaceBorder else AsterAmber,
                    contentColor = if (reminder.isSnoozed) AsterTextPrimary else AsterBackground
                ),
                contentPadding = PaddingValues(horizontal = 18.dp, vertical = 8.dp)
            ) {
                Text(
                    text = if (reminder.isSnoozed) "Resumed" else "Snooze",
                    fontSize = 14.sp,
                    fontWeight = FontWeight.SemiBold
                )
            }
        }
    }
}

@Composable
private fun TasksListCard(
    tasks: List<CompanionTask>,
    onToggleTask: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(20.dp),
        color = AsterSurface
    ) {
        Column(modifier = Modifier.fillMaxWidth()) {
            tasks.forEachIndexed { index, task ->
                TaskRowItem(
                    task = task,
                    onToggle = { onToggleTask(task.id) }
                )

                if (index < tasks.lastIndex) {
                    HorizontalDivider(
                        color = AsterSurfaceBorder.copy(alpha = 0.4f),
                        thickness = 0.5.dp,
                        modifier = Modifier.padding(horizontal = 16.dp)
                    )
                }
            }
        }
    }
}

@Composable
private fun TaskRowItem(
    task: CompanionTask,
    onToggle: () -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onToggle)
            .padding(horizontal = 18.dp, vertical = 16.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Custom rounded checkbox matching screenshot
        val boxBorderColor by animateColorAsState(
            targetValue = if (task.isCompleted) AsterAmber else AsterTextSecondary.copy(alpha = 0.7f),
            label = "checkboxBorder"
        )
        val boxBgColor by animateColorAsState(
            targetValue = if (task.isCompleted) AsterAmber else Color.Transparent,
            label = "checkboxBg"
        )

        Box(
            modifier = Modifier
                .size(24.dp)
                .clip(RoundedCornerShape(7.dp))
                .background(boxBgColor)
                .border(1.5.dp, boxBorderColor, RoundedCornerShape(7.dp)),
            contentAlignment = Alignment.Center
        ) {
            if (task.isCompleted) {
                Icon(
                    imageVector = Icons.Default.Check,
                    contentDescription = "Completed",
                    tint = AsterBackground,
                    modifier = Modifier.size(16.dp)
                )
            }
        }

        Spacer(modifier = Modifier.width(16.dp))

        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = task.title,
                color = if (task.isCompleted) AsterTextMuted else AsterTextPrimary,
                fontSize = 15.sp,
                fontWeight = FontWeight.Medium,
                textDecoration = if (task.isCompleted) TextDecoration.LineThrough else TextDecoration.None
            )

            Spacer(modifier = Modifier.height(2.dp))

            Text(
                text = task.dueLabel,
                color = AsterTextSecondary,
                fontSize = 13.sp
            )
        }

        Icon(
            imageVector = Icons.Outlined.ChevronRight,
            contentDescription = "Task details",
            tint = AsterTextSecondary.copy(alpha = 0.6f),
            modifier = Modifier.size(20.dp)
        )
    }
}

@Composable
private fun RecentMemoriesHorizontalRow(
    memories: List<RecentMemoryCard>,
    onMemoryClick: (RecentMemoryCard) -> Unit,
    modifier: Modifier = Modifier
) {
    val context = LocalContext.current

    LazyRow(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(14.dp),
        contentPadding = PaddingValues(end = 16.dp)
    ) {
        items(memories, key = { it.id }) { memory ->
            val drawableResId = memory.imageUrl?.let { resName ->
                context.resources.getIdentifier(resName, "drawable", context.packageName)
            } ?: 0

            Surface(
                modifier = Modifier
                    .width(215.dp)
                    .height(215.dp)
                    .clickable { onMemoryClick(memory) },
                shape = RoundedCornerShape(20.dp),
                color = AsterSurface
            ) {
                Box(modifier = Modifier.fillMaxSize()) {
                    if (drawableResId != 0) {
                        Image(
                            painter = painterResource(id = drawableResId),
                            contentDescription = memory.title,
                            contentScale = ContentScale.Crop,
                            modifier = Modifier.fillMaxSize()
                        )
                    } else {
                        // Elegant dark ambient card fallback
                        Box(
                            modifier = Modifier
                                .fillMaxSize()
                                .background(
                                    Brush.verticalGradient(
                                        listOf(Color(0xFF28231E), Color(0xFF191614))
                                    )
                                )
                        )
                    }

                    // Scrim gradient for legible text
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .background(
                                Brush.verticalGradient(
                                    colorStops = arrayOf(
                                        0.0f to Color.Transparent,
                                        0.45f to Color.Transparent,
                                        0.75f to Color.Black.copy(alpha = 0.7f),
                                        1.0f to Color.Black.copy(alpha = 0.95f)
                                    )
                                )
                            )
                    )

                    // Text overlay at bottom
                    Column(
                        modifier = Modifier
                            .align(Alignment.BottomStart)
                            .padding(14.dp)
                    ) {
                        Text(
                            text = memory.title,
                            color = AsterTextPrimary,
                            fontSize = 15.sp,
                            fontWeight = FontWeight.SemiBold,
                            lineHeight = 19.sp
                        )

                        Spacer(modifier = Modifier.height(4.dp))

                        Text(
                            text = memory.timeAgoLabel,
                            color = AsterTextSecondary,
                            fontSize = 12.sp
                        )
                    }
                }
            }
        }
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF121110)
@Composable
fun TodayScreenPreview() {
    AsterCompanionTheme {
        TodayScreenContent(state = TodayUiState())
    }
}
