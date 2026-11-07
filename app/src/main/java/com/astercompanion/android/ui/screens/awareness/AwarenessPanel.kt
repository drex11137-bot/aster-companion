package com.astercompanion.android.ui.screens.awareness

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.animateColorAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.outlined.Mic
import androidx.compose.material.icons.outlined.MicOff
import androidx.compose.material.icons.outlined.Pause
import androidx.compose.material.icons.outlined.PlayArrow
import androidx.compose.material.icons.outlined.Security
import androidx.compose.material.icons.outlined.Speed
import androidx.compose.material.icons.outlined.Stop
import androidx.compose.material.icons.outlined.Visibility
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.astercompanion.android.model.ScreenEvent
import com.astercompanion.android.ui.components.AvatarWithGlow
import com.astercompanion.android.ui.theme.AsterAmber
import com.astercompanion.android.ui.theme.AsterBackground
import com.astercompanion.android.ui.theme.AsterCompanionTheme
import com.astercompanion.android.ui.theme.AsterErrorRed
import com.astercompanion.android.ui.theme.AsterOnlineGreen
import com.astercompanion.android.ui.theme.AsterSurface
import com.astercompanion.android.ui.theme.AsterSurfaceBorder
import com.astercompanion.android.ui.theme.AsterSurfaceElevated
import com.astercompanion.android.ui.theme.AsterTextMuted
import com.astercompanion.android.ui.theme.AsterTextPrimary
import com.astercompanion.android.ui.theme.AsterTextSecondary
import com.astercompanion.android.ui.theme.AsterWarningYellow
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

@Composable
fun AwarenessPanel(
    onDismiss: () -> Unit = {},
    viewModel: AwarenessViewModel = viewModel(),
    modifier: Modifier = Modifier
) {
    val state by viewModel.uiState.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(state.feedbackToast) {
        state.feedbackToast?.let { msg ->
            snackbarHostState.showSnackbar(msg)
            viewModel.dismissFeedback()
        }
    }

    AwarenessPanelContent(
        state = state,
        onTogglePause = viewModel::togglePause,
        onToggleStop = viewModel::toggleStop,
        onToggleMute = viewModel::toggleMute,
        onDismiss = onDismiss,
        snackbarHostState = snackbarHostState,
        modifier = modifier
    )
}

@Composable
fun AwarenessPanelContent(
    state: AwarenessUiState,
    onTogglePause: () -> Unit = {},
    onToggleStop: () -> Unit = {},
    onToggleMute: () -> Unit = {},
    onDismiss: () -> Unit = {},
    snackbarHostState: SnackbarHostState = remember { SnackbarHostState() },
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .fillMaxSize()
            .background(AsterBackground)
            .statusBarsPadding()
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 20.dp, vertical = 16.dp)
        ) {
            // Header: Title & Close Button
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    AvatarWithGlow(
                        size = 40.dp,
                        showOnlineDot = true,
                        showGlow = false
                    )
                    Spacer(modifier = Modifier.width(12.dp))
                    Column {
                        Text(
                            text = "Continuous Awareness",
                            color = AsterTextPrimary,
                            fontSize = 20.sp,
                            fontWeight = FontWeight.Bold
                        )
                        Text(
                            text = "Active Profile: ${state.activeProfileName}",
                            color = AsterAmber,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.Medium
                        )
                    }
                }

                IconButton(onClick = onDismiss) {
                    Icon(
                        imageVector = Icons.Default.Close,
                        contentDescription = "Close panel",
                        tint = AsterTextSecondary
                    )
                }
            }

            Spacer(modifier = Modifier.height(20.dp))

            // Real-time FPS Telemetry 3-Card Grid
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                FpsMetricCard(
                    title = "Capture FPS",
                    value = String.format(Locale.US, "%.1f", state.captureFps),
                    subtitle = "Screen ingest",
                    tint = AsterOnlineGreen,
                    modifier = Modifier.weight(1f)
                )

                FpsMetricCard(
                    title = "Upload FPS",
                    value = String.format(Locale.US, "%.1f", state.uploadFps),
                    subtitle = "Secure buffer",
                    tint = AsterAmber,
                    modifier = Modifier.weight(1f)
                )

                FpsMetricCard(
                    title = "Analysis FPS",
                    value = String.format(Locale.US, "%.1f", state.analysisFps),
                    subtitle = "Multimodal AI",
                    tint = Color(0xFF9880FF),
                    modifier = Modifier.weight(1f)
                )
            }

            Spacer(modifier = Modifier.height(18.dp))

            // Interactive Controls Row: Pause / Stop / Mute
            Surface(
                shape = RoundedCornerShape(20.dp),
                color = AsterSurface,
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp, vertical = 14.dp),
                    horizontalArrangement = Arrangement.SpaceAround,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    // Pause Control
                    ControlActionButton(
                        icon = if (state.isPaused) Icons.Outlined.PlayArrow else Icons.Outlined.Pause,
                        label = if (state.isPaused) "Resume" else "Pause",
                        isActive = state.isPaused,
                        activeColor = AsterWarningYellow,
                        onClick = onTogglePause
                    )

                    // Stop Control
                    ControlActionButton(
                        icon = Icons.Outlined.Stop,
                        label = if (state.isStopped) "Restart" else "Stop",
                        isActive = state.isStopped,
                        activeColor = AsterErrorRed,
                        onClick = onToggleStop
                    )

                    // Mute Control
                    ControlActionButton(
                        icon = if (state.isMuted) Icons.Outlined.MicOff else Icons.Outlined.Mic,
                        label = if (state.isMuted) "Unmute" else "Mute",
                        isActive = state.isMuted,
                        activeColor = AsterAmber,
                        onClick = onToggleMute
                    )
                }
            }

            Spacer(modifier = Modifier.height(18.dp))

            // Privacy Guarantee Box
            Surface(
                shape = RoundedCornerShape(16.dp),
                color = AsterSurfaceElevated,
                border = androidx.compose.foundation.BorderStroke(1.dp, AsterSurfaceBorder),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier.padding(14.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = Icons.Outlined.Security,
                        contentDescription = null,
                        tint = AsterAmber,
                        modifier = Modifier.size(24.dp)
                    )
                    Spacer(modifier = Modifier.width(12.dp))
                    Column {
                        Text(
                            text = "Zero Cloud Retention Architecture",
                            color = AsterTextPrimary,
                            fontSize = 13.sp,
                            fontWeight = FontWeight.SemiBold
                        )
                        Spacer(modifier = Modifier.height(2.dp))
                        Text(
                            text = "Sequence #${state.monotonicSequenceNumber} • Gaps: ${state.totalGapsDetected} • Raw pixels processed in ephemeral RAM only.",
                            color = AsterTextSecondary,
                            fontSize = 11.sp,
                            lineHeight = 15.sp
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(20.dp))

            // Recent Screen Events Stream
            Text(
                text = "Recent Scene Ingest Events",
                color = AsterTextPrimary,
                fontSize = 16.sp,
                fontWeight = FontWeight.SemiBold
            )

            Spacer(modifier = Modifier.height(10.dp))

            LazyColumn(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(8.dp),
                contentPadding = PaddingValues(bottom = 24.dp)
            ) {
                items(state.recentEvents, key = { it.id }) { event ->
                    ScreenEventItemRow(event = event)
                }
            }
        }

        SnackbarHost(
            hostState = snackbarHostState,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = 16.dp)
        )
    }
}

@Composable
private fun FpsMetricCard(
    title: String,
    value: String,
    subtitle: String,
    tint: Color,
    modifier: Modifier = Modifier
) {
    Surface(
        shape = RoundedCornerShape(18.dp),
        color = AsterSurface,
        modifier = modifier
    ) {
        Column(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 14.dp),
            horizontalAlignment = Alignment.Start
        ) {
            Text(
                text = title,
                color = AsterTextSecondary,
                fontSize = 11.sp,
                fontWeight = FontWeight.Medium
            )
            Spacer(modifier = Modifier.height(4.dp))
            Row(verticalAlignment = Alignment.Bottom) {
                Text(
                    text = value,
                    color = tint,
                    fontSize = 20.sp,
                    fontWeight = FontWeight.Bold
                )
                Spacer(modifier = Modifier.width(2.dp))
                Text(
                    text = "fps",
                    color = AsterTextMuted,
                    fontSize = 11.sp,
                    modifier = Modifier.padding(bottom = 2.dp)
                )
            }
            Spacer(modifier = Modifier.height(2.dp))
            Text(
                text = subtitle,
                color = AsterTextMuted,
                fontSize = 10.sp
            )
        }
    }
}

@Composable
private fun ControlActionButton(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    label: String,
    isActive: Boolean,
    activeColor: Color,
    onClick: () -> Unit
) {
    val bgColor by animateColorAsState(
        targetValue = if (isActive) activeColor.copy(alpha = 0.2f) else AsterSurfaceElevated,
        label = "controlBg"
    )
    val iconColor by animateColorAsState(
        targetValue = if (isActive) activeColor else AsterTextPrimary,
        label = "controlIcon"
    )

    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = Modifier.clickable(onClick = onClick)
    ) {
        Box(
            modifier = Modifier
                .size(46.dp)
                .clip(CircleShape)
                .background(bgColor)
                .border(
                    width = 1.dp,
                    color = if (isActive) activeColor else AsterSurfaceBorder,
                    shape = CircleShape
                ),
            contentAlignment = Alignment.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = label,
                tint = iconColor,
                modifier = Modifier.size(22.dp)
            )
        }

        Spacer(modifier = Modifier.height(6.dp))

        Text(
            text = label,
            color = if (isActive) activeColor else AsterTextSecondary,
            fontSize = 12.sp,
            fontWeight = FontWeight.Medium
        )
    }
}

@Composable
private fun ScreenEventItemRow(
    event: ScreenEvent,
    modifier: Modifier = Modifier
) {
    Surface(
        shape = RoundedCornerShape(14.dp),
        color = AsterSurface,
        modifier = modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 14.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier
                    .size(8.dp)
                    .clip(CircleShape)
                    .background(AsterAmber)
            )

            Spacer(modifier = Modifier.width(12.dp))

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = event.summary,
                    color = AsterTextPrimary,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Medium
                )
                Spacer(modifier = Modifier.height(2.dp))
                Text(
                    text = "${event.eventType} • Seq #${event.sequenceNumber}",
                    color = AsterTextMuted,
                    fontSize = 11.sp
                )
            }

            val timeString = SimpleDateFormat("h:mm:ss a", Locale.getDefault()).format(Date(event.timestamp))
            Text(
                text = timeString,
                color = AsterTextSecondary,
                fontSize = 11.sp
            )
        }
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF121110)
@Composable
fun AwarenessPanelPreview() {
    AsterCompanionTheme {
        AwarenessPanelContent(state = AwarenessUiState())
    }
}
