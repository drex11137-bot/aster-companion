package com.astercompanion.android.ui.screens.chat

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.imePadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.rememberLazyListState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.Send
import androidx.compose.material.icons.filled.MoreVert
import androidx.compose.material.icons.outlined.CalendarMonth
import androidx.compose.material.icons.outlined.Description
import androidx.compose.material.icons.outlined.Mic
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material.icons.outlined.Visibility
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.ui.graphics.Color
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.astercompanion.android.model.ChatMessage
import com.astercompanion.android.model.MessageSender
import com.astercompanion.android.ui.components.AvatarWithGlow
import com.astercompanion.android.ui.components.ScheduleTimelineCard
import com.astercompanion.android.ui.theme.AsterAmber
import com.astercompanion.android.ui.theme.AsterBackground
import com.astercompanion.android.ui.theme.AsterCompanionTheme
import com.astercompanion.android.ui.theme.AsterSurface
import com.astercompanion.android.ui.theme.AsterSurfaceBorder
import com.astercompanion.android.ui.theme.AsterSurfaceElevated
import com.astercompanion.android.ui.theme.AsterTextMuted
import com.astercompanion.android.ui.theme.AsterTextPrimary
import com.astercompanion.android.ui.theme.AsterTextSecondary
import com.astercompanion.android.ui.theme.AsterVioletText
import com.astercompanion.android.ui.theme.AsterVioletUserBubble
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun ChatScreen(
    onNavigateToVoiceCall: () -> Unit = {},
    onNavigateToAwareness: () -> Unit = {},
    viewModel: ChatViewModel = viewModel(),
    modifier: Modifier = Modifier
) {
    val state by viewModel.uiState.collectAsState()

    ChatScreenContent(
        state = state,
        onInputTextChanged = viewModel::onInputTextChanged,
        onSendMessage = viewModel::sendMessage,
        onQuickActionClick = viewModel::onQuickActionClick,
        onCitationClick = viewModel::onCitationClick,
        onDismissCitationDialog = viewModel::dismissCitationDialog,
        onNavigateToVoiceCall = onNavigateToVoiceCall,
        onNavigateToAwareness = onNavigateToAwareness,
        modifier = modifier
    )
}

@Composable
fun ChatScreenContent(
    state: ChatUiState,
    onInputTextChanged: (String) -> Unit = {},
    onSendMessage: () -> Unit = {},
    onQuickActionClick: (String) -> Unit = {},
    onCitationClick: (List<String>) -> Unit = {},
    onDismissCitationDialog: () -> Unit = {},
    onNavigateToVoiceCall: () -> Unit = {},
    onNavigateToAwareness: () -> Unit = {},
    modifier: Modifier = Modifier
) {
    val listState = rememberLazyListState()
    var showMenu by remember { mutableStateOf(false) }

    LaunchedEffect(state.messages.size, state.isStreaming) {
        if (state.messages.isNotEmpty()) {
            listState.animateScrollToItem(state.messages.size - 1)
        }
    }

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(AsterBackground)
            .statusBarsPadding()
            .imePadding()
    ) {
        Column(modifier = Modifier.fillMaxSize()) {
            // Top App Bar matching Screenshot (79ffed4b)
            ChatTopAppBar(
                companionName = state.companionName,
                isOnline = state.isOnline,
                onAwarenessClick = onNavigateToAwareness,
                onMenuClick = { showMenu = true }
            )

            // Chat Message History
            LazyColumn(
                state = listState,
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
                    .padding(horizontal = 16.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp),
                contentPadding = PaddingValues(top = 8.dp, bottom = 12.dp)
            ) {
                // Centered timestamp header: "Today 8:20 PM"
                item {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = "Today 8:20 PM",
                            color = AsterTextMuted,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Normal
                        )
                    }
                }

                items(state.messages, key = { it.id }) { message ->
                    ChatMessageItem(
                        message = message,
                        onCitationClick = { onCitationClick(message.memoryCitations) }
                    )
                }

                if (state.isStreaming) {
                    item {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.padding(start = 48.dp, top = 2.dp)
                        ) {
                            Text(
                                text = "Aster is thinking...",
                                color = AsterTextSecondary,
                                fontSize = 12.sp,
                                fontStyle = androidx.compose.ui.text.font.FontStyle.Italic
                            )
                        }
                    }
                }
            }

            // Quick action chips above composer
            QuickActionsBar(
                quickActions = state.quickActions,
                onQuickActionClick = onQuickActionClick
            )

            // Bottom Input Composer
            ChatInputComposer(
                inputText = state.inputText,
                onInputTextChanged = onInputTextChanged,
                onSendMessage = onSendMessage,
                onVoiceCallClick = onNavigateToVoiceCall
            )
        }

        // Citations Dialog
        state.activeCitationDialog?.let { citations ->
            AlertDialog(
                onDismissRequest = onDismissCitationDialog,
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(
                            imageVector = Icons.Outlined.Description,
                            contentDescription = null,
                            tint = AsterAmber,
                            modifier = Modifier.size(20.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "Used Memories (${citations.size})",
                            color = AsterTextPrimary,
                            fontSize = 18.sp,
                            fontWeight = FontWeight.SemiBold
                        )
                    }
                },
                text = {
                    Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                        Text(
                            text = "Aster retrieved these verified personal memories to tailor this response:",
                            color = AsterTextSecondary,
                            fontSize = 13.sp
                        )
                        citations.forEach { citation ->
                            Surface(
                                shape = RoundedCornerShape(10.dp),
                                color = AsterSurfaceElevated,
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Text(
                                    text = "• $citation",
                                    color = AsterTextPrimary,
                                    fontSize = 14.sp,
                                    modifier = Modifier.padding(12.dp)
                                )
                            }
                        }
                    }
                },
                confirmButton = {
                    TextButton(onClick = onDismissCitationDialog) {
                        Text("Done", color = AsterAmber, fontWeight = FontWeight.SemiBold)
                    }
                },
                containerColor = AsterSurface
            )
        }
    }
}

@Composable
private fun ChatTopAppBar(
    companionName: String,
    isOnline: Boolean,
    onAwarenessClick: () -> Unit,
    onMenuClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        AvatarWithGlow(
            size = 44.dp,
            showOnlineDot = true,
            showGlow = true
        )

        Spacer(modifier = Modifier.width(14.dp))

        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = companionName,
                color = AsterTextPrimary,
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = if (isOnline) "Online" else "Offline",
                color = AsterTextSecondary,
                fontSize = 13.sp
            )
        }

        // Live Awareness telemetry shortcut
        IconButton(onClick = onAwarenessClick) {
            Icon(
                imageVector = Icons.Outlined.Visibility,
                contentDescription = "Awareness Panel",
                tint = AsterAmber
            )
        }

        IconButton(onClick = { /* Search */ }) {
            Icon(
                imageVector = Icons.Outlined.Search,
                contentDescription = "Search chat",
                tint = AsterTextSecondary
            )
        }

        IconButton(onClick = onMenuClick) {
            Icon(
                imageVector = Icons.Default.MoreVert,
                contentDescription = "More options",
                tint = AsterTextSecondary
            )
        }
    }
}

@Composable
private fun ChatMessageItem(
    message: ChatMessage,
    onCitationClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val isUser = message.sender == MessageSender.USER

    if (isUser) {
        // User Message Bubble: Restrained Violet (#7966F3) on the right
        Column(
            modifier = modifier.fillMaxWidth(),
            horizontalAlignment = Alignment.End
        ) {
            Surface(
                shape = RoundedCornerShape(20.dp, 20.dp, 4.dp, 20.dp),
                color = AsterVioletUserBubble,
                modifier = Modifier.padding(start = 48.dp)
            ) {
                Text(
                    text = message.content,
                    color = Color.White,
                    fontSize = 15.sp,
                    lineHeight = 21.sp,
                    modifier = Modifier.padding(horizontal = 18.dp, vertical = 12.dp)
                )
            }

            Spacer(modifier = Modifier.height(4.dp))

            // Subtext: Timestamp & delivery checkmarks
            val timeString = SimpleDateFormat("h:mm a", Locale.getDefault()).format(Date(message.timestamp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(
                    text = "$timeString  ✓✓",
                    color = AsterVioletText.copy(alpha = 0.8f),
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Medium
                )
            }
        }
    } else {
        // Companion Message: Left side with avatar
        Row(
            modifier = modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.Start,
            verticalAlignment = Alignment.Top
        ) {
            AvatarWithGlow(
                size = 36.dp,
                showOnlineDot = false,
                showGlow = false
            )

            Spacer(modifier = Modifier.width(10.dp))

            Column(modifier = Modifier.weight(1f)) {
                // Text bubble
                if (message.content.isNotEmpty()) {
                    Surface(
                        shape = RoundedCornerShape(20.dp, 20.dp, 20.dp, 4.dp),
                        color = AsterSurface
                    ) {
                        Text(
                            text = message.content,
                            color = AsterTextPrimary,
                            fontSize = 15.sp,
                            lineHeight = 22.sp,
                            modifier = Modifier.padding(horizontal = 18.dp, vertical = 14.dp)
                        )
                    }
                }

                // Interactive Schedule Card (Saturday schedule timeline)
                message.scheduleCard?.let { card ->
                    Spacer(modifier = Modifier.height(10.dp))
                    ScheduleTimelineCard(
                        dateTitle = card.dateTitle,
                        subtitle = card.subtitle
                    )
                }

                // Citation pill chip: "Used 2 memories"
                if (message.memoryCitations.isNotEmpty()) {
                    Spacer(modifier = Modifier.height(10.dp))
                    Surface(
                        shape = RoundedCornerShape(16.dp),
                        color = AsterSurfaceElevated,
                        modifier = Modifier.clickable(onClick = onCitationClick)
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                imageVector = Icons.Outlined.Description,
                                contentDescription = null,
                                tint = AsterTextSecondary,
                                modifier = Modifier.size(15.dp)
                            )
                            Spacer(modifier = Modifier.width(6.dp))
                            Text(
                                text = "Used ${message.memoryCitations.size} memories",
                                color = AsterTextSecondary,
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Medium
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(4.dp))

                val timeString = SimpleDateFormat("h:mm a", Locale.getDefault()).format(Date(message.timestamp))
                Text(
                    text = timeString,
                    color = AsterTextMuted,
                    fontSize = 11.sp,
                    modifier = Modifier.padding(start = 4.dp)
                )
            }
        }
    }
}

@Composable
private fun QuickActionsBar(
    quickActions: List<String>,
    onQuickActionClick: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    LazyRow(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp),
        horizontalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        items(quickActions) { action ->
            Surface(
                shape = RoundedCornerShape(20.dp),
                color = AsterSurfaceElevated,
                border = androidx.compose.foundation.BorderStroke(1.dp, AsterSurfaceBorder),
                modifier = Modifier.clickable { onQuickActionClick(action) }
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 14.dp, vertical = 8.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    val icon = when (action) {
                        "Add reminder" -> Icons.Outlined.CalendarMonth
                        "Summarize" -> Icons.Outlined.Description
                        else -> Icons.Outlined.Description
                    }
                    Icon(
                        imageVector = icon,
                        contentDescription = null,
                        tint = AsterTextSecondary,
                        modifier = Modifier.size(16.dp)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = action,
                        color = AsterTextPrimary,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Medium
                    )
                }
            }
        }
    }
}

@Composable
private fun ChatInputComposer(
    inputText: String,
    onInputTextChanged: (String) -> Unit,
    onSendMessage: () -> Unit,
    onVoiceCallClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        // Rounded Pill Composer container
        Surface(
            shape = RoundedCornerShape(26.dp),
            color = AsterSurfaceElevated,
            modifier = Modifier
                .weight(1f)
                .height(52.dp)
        ) {
            Row(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(horizontal = 16.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                BasicTextField(
                    value = inputText,
                    onValueChange = onInputTextChanged,
                    modifier = Modifier.weight(1f),
                    textStyle = TextStyle(
                        color = AsterTextPrimary,
                        fontSize = 15.sp
                    ),
                    cursorBrush = SolidColor(AsterAmber),
                    decorationBox = { innerTextField ->
                        if (inputText.isEmpty()) {
                            Text(
                                text = "Message Aster",
                                color = AsterTextSecondary,
                                fontSize = 15.sp
                            )
                        }
                        innerTextField()
                    }
                )

                // Voice microphone icon inside pill
                IconButton(
                    onClick = onVoiceCallClick,
                    modifier = Modifier.size(36.dp)
                ) {
                    Icon(
                        imageVector = Icons.Outlined.Mic,
                        contentDescription = "Voice Call",
                        tint = AsterTextSecondary,
                        modifier = Modifier.size(22.dp)
                    )
                }
            }
        }

        Spacer(modifier = Modifier.width(10.dp))

        // Amber Circular Send Button
        Box(
            modifier = Modifier
                .size(48.dp)
                .clip(CircleShape)
                .background(AsterAmber)
                .clickable(onClick = onSendMessage),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = Icons.AutoMirrored.Filled.Send,
                contentDescription = "Send",
                tint = AsterBackground,
                modifier = Modifier.size(20.dp)
            )
        }
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF121110)
@Composable
fun ChatScreenPreview() {
    AsterCompanionTheme {
        ChatScreenContent(state = ChatUiState())
    }
}
