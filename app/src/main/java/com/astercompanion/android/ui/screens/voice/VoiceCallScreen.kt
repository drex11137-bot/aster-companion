package com.astercompanion.android.ui.screens.voice

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.VolumeUp
import androidx.compose.material.icons.filled.CallEnd
import androidx.compose.material.icons.outlined.GraphicEq
import androidx.compose.material.icons.outlined.Mic
import androidx.compose.material.icons.outlined.MicOff
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
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
import com.astercompanion.android.ui.theme.AsterVioletUserBubble
import java.util.Locale

@Composable
fun VoiceCallScreen(
    onCallEnded: () -> Unit,
    viewModel: VoiceCallViewModel = viewModel(),
    modifier: Modifier = Modifier
) {
    val state by viewModel.uiState.collectAsState()

    VoiceCallContent(
        state = state,
        onBargeIn = viewModel::triggerBargeIn,
        onToggleMute = viewModel::toggleMute,
        onToggleSpeaker = viewModel::toggleSpeaker,
        onEndCall = { viewModel.endCall(onCallEnded) },
        modifier = modifier
    )
}

@Composable
fun VoiceCallContent(
    state: VoiceCallUiState,
    onBargeIn: () -> Unit = {},
    onToggleMute: () -> Unit = {},
    onToggleSpeaker: () -> Unit = {},
    onEndCall: () -> Unit = {},
    modifier: Modifier = Modifier
) {
    val minutes = state.callDurationSeconds / 60
    val seconds = state.callDurationSeconds % 60
    val formattedDuration = String.format(Locale.US, "%02d:%02d", minutes, seconds)

    val infiniteTransition = rememberInfiniteTransition(label = "audio_visualizer")
    val pulseScale by infiniteTransition.animateFloat(
        initialValue = 1.0f,
        targetValue = 1.25f,
        animationSpec = infiniteRepeatable(
            animation = tween(1200, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulse_scale"
    )

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(AsterBackground)
            .statusBarsPadding()
            .padding(horizontal = 24.dp, vertical = 20.dp)
    ) {
        Column(
            modifier = Modifier.fillMaxSize(),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Header Info
            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text = state.companionName,
                color = AsterTextPrimary,
                fontSize = 24.sp,
                fontWeight = FontWeight.Bold
            )

            Spacer(modifier = Modifier.height(6.dp))

            Row(verticalAlignment = Alignment.CenterVertically) {
                Box(
                    modifier = Modifier
                        .size(8.dp)
                        .clip(CircleShape)
                        .background(AsterOnlineGreen)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = "$formattedDuration • Ultra-low Latency Voice",
                    color = AsterTextSecondary,
                    fontSize = 13.sp
                )
            }

            Spacer(modifier = Modifier.weight(1f))

            // Animated Ambient Audio Visualizer
            Box(
                modifier = Modifier
                    .size(280.dp),
                contentAlignment = Alignment.Center
            ) {
                // Expanding outer ring 2
                Box(
                    modifier = Modifier
                        .size(260.dp * (1.0f + state.audioAmplitude * 0.25f * pulseScale))
                        .drawBehind {
                            drawCircle(
                                brush = Brush.radialGradient(
                                    colors = listOf(
                                        AsterAmber.copy(alpha = 0.15f * state.audioAmplitude),
                                        Color.Transparent
                                    )
                                )
                            )
                        }
                )

                // Expanding outer ring 1
                Box(
                    modifier = Modifier
                        .size(200.dp * (1.0f + state.audioAmplitude * 0.2f))
                        .drawBehind {
                            drawCircle(
                                brush = Brush.radialGradient(
                                    colors = listOf(
                                        AsterAmber.copy(alpha = 0.35f * state.audioAmplitude),
                                        AsterAmber.copy(alpha = 0.1f * state.audioAmplitude),
                                        Color.Transparent
                                    )
                                )
                            )
                        }
                )

                // Central Avatar
                AvatarWithGlow(
                    size = 120.dp,
                    showOnlineDot = true,
                    showGlow = true,
                    isPulsing = state.speakerState == CallSpeakerState.COMPANION_SPEAKING
                )
            }

            Spacer(modifier = Modifier.height(18.dp))

            // Speaker Status Badge
            Surface(
                shape = RoundedCornerShape(16.dp),
                color = when (state.speakerState) {
                    CallSpeakerState.BARGE_IN_DETECTED -> AsterVioletUserBubble.copy(alpha = 0.25f)
                    CallSpeakerState.COMPANION_SPEAKING -> AsterAmber.copy(alpha = 0.15f)
                    CallSpeakerState.LISTENING -> AsterSurfaceElevated
                },
                border = androidx.compose.foundation.BorderStroke(
                    1.dp,
                    when (state.speakerState) {
                        CallSpeakerState.BARGE_IN_DETECTED -> AsterVioletUserBubble
                        CallSpeakerState.COMPANION_SPEAKING -> AsterAmber
                        CallSpeakerState.LISTENING -> AsterSurfaceBorder
                    }
                )
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 14.dp, vertical = 6.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Icon(
                        imageVector = Icons.Outlined.GraphicEq,
                        contentDescription = null,
                        tint = when (state.speakerState) {
                            CallSpeakerState.BARGE_IN_DETECTED -> AsterVioletUserBubble
                            CallSpeakerState.COMPANION_SPEAKING -> AsterAmber
                            CallSpeakerState.LISTENING -> AsterTextSecondary
                        },
                        modifier = Modifier.size(16.dp)
                    )
                    Spacer(modifier = Modifier.width(6.dp))
                    Text(
                        text = when (state.speakerState) {
                            CallSpeakerState.BARGE_IN_DETECTED -> "Barge-in active • Aster yielding"
                            CallSpeakerState.COMPANION_SPEAKING -> "Aster speaking"
                            CallSpeakerState.LISTENING -> "Listening to you..."
                        },
                        color = AsterTextPrimary,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Medium
                    )
                }
            }

            Spacer(modifier = Modifier.weight(1f))

            // Live Streaming Transcript Box
            Surface(
                shape = RoundedCornerShape(20.dp),
                color = AsterSurface,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 8.dp)
            ) {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(18.dp)
                ) {
                    if (state.userSpeechBuffer.isNotEmpty()) {
                        Text(
                            text = "You: ${state.userSpeechBuffer}",
                            color = AsterVioletUserBubble,
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Medium
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                    }

                    Text(
                        text = state.liveTranscript,
                        color = AsterTextPrimary,
                        fontSize = 15.sp,
                        lineHeight = 21.sp,
                        textAlign = TextAlign.Start
                    )
                }
            }

            Spacer(modifier = Modifier.height(28.dp))

            // Bottom Call Controls Row: Mute, Barge-in, Speaker, End Call
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 20.dp),
                horizontalArrangement = Arrangement.SpaceEvenly,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Mute Mic Button
                CallControlButton(
                    icon = if (state.isMicMuted) Icons.Outlined.MicOff else Icons.Outlined.Mic,
                    label = if (state.isMicMuted) "Unmute" else "Mute",
                    isActive = state.isMicMuted,
                    activeColor = AsterAmber,
                    onClick = onToggleMute
                )

                // Barge-in Button
                CallControlButton(
                    icon = Icons.Outlined.GraphicEq,
                    label = "Barge-in",
                    isActive = state.speakerState == CallSpeakerState.BARGE_IN_DETECTED,
                    activeColor = AsterVioletUserBubble,
                    onClick = onBargeIn
                )

                // Speaker Button
                CallControlButton(
                    icon = Icons.AutoMirrored.Outlined.VolumeUp,
                    label = "Speaker",
                    isActive = state.isSpeakerOn,
                    activeColor = AsterOnlineGreen,
                    onClick = onToggleSpeaker
                )

                // End Call (Red Circular Button)
                Box(
                    modifier = Modifier
                        .size(56.dp)
                        .clip(CircleShape)
                        .background(AsterErrorRed)
                        .clickable(onClick = onEndCall),
                    contentAlignment = Alignment.Center
                ) {
                    Icon(
                        imageVector = Icons.Default.CallEnd,
                        contentDescription = "End Call",
                        tint = Color.White,
                        modifier = Modifier.size(28.dp)
                    )
                }
            }
        }
    }
}

@Composable
private fun CallControlButton(
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    label: String,
    isActive: Boolean,
    activeColor: Color,
    onClick: () -> Unit
) {
    val bgColor by animateColorAsState(
        targetValue = if (isActive) activeColor.copy(alpha = 0.2f) else AsterSurfaceElevated,
        label = "callBtnBg"
    )
    val iconColor by animateColorAsState(
        targetValue = if (isActive) activeColor else AsterTextPrimary,
        label = "callBtnIcon"
    )

    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = Modifier.clickable(onClick = onClick)
    ) {
        Box(
            modifier = Modifier
                .size(52.dp)
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
                modifier = Modifier.size(24.dp)
            )
        }

        Spacer(modifier = Modifier.height(4.dp))

        Text(
            text = label,
            color = if (isActive) activeColor else AsterTextSecondary,
            fontSize = 11.sp,
            fontWeight = FontWeight.Medium
        )
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF121110)
@Composable
fun VoiceCallScreenPreview() {
    AsterCompanionTheme {
        VoiceCallContent(state = VoiceCallUiState())
    }
}
