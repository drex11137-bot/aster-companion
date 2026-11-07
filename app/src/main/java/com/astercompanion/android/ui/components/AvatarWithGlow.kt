package com.astercompanion.android.ui.components

import androidx.annotation.DrawableRes
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.interaction.MutableInteractionSource
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.offset
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Person
import androidx.compose.material3.Icon
import androidx.compose.material3.ripple
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.painter.Painter
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import com.astercompanion.android.ui.theme.AsterAmber
import com.astercompanion.android.ui.theme.AsterAmberBright
import com.astercompanion.android.ui.theme.AsterBackground
import com.astercompanion.android.ui.theme.AsterColors
import com.astercompanion.android.ui.theme.AsterCompanionTheme
import com.astercompanion.android.ui.theme.AsterOnlineGreen
import com.astercompanion.android.ui.theme.AsterSurfaceElevated

/**
 * AvatarWithGlow
 *
 * Implements the circular avatar with an ambient warm amber halo/bloom effect
 * (`#E59843` / `#F5A623`), customizable radius, and optional status dot (`#4CD964` online green).
 *
 * Strictly matches screenshots:
 * - 79ffed4b-1317-46e6-98db-6eb6c96f60d6.png (Top bar avatar with online green status dot)
 * - 56539447-5086-44aa-b0ad-b98fa9cb6a8d.png (Today screen avatar with amber halo bloom)
 * - a98599e6-e707-4cb8-a85f-85293d19df71.png (Large companion studio central avatar with glowing amber aura)
 */
@Composable
fun AvatarWithGlow(
    modifier: Modifier = Modifier,
    size: Dp = 48.dp,
    avatarSize: Dp = size,
    glowRadius: Dp = if (avatarSize > 80.dp) avatarSize * 0.35f else avatarSize * 0.28f,
    showGlow: Boolean = true,
    isPulsing: Boolean = false,
    showOnlineDot: Boolean = false,
    showStatusDot: Boolean = showOnlineDot,
    isOnline: Boolean = true,
    glowColor: Color = AsterAmber,
    glowSecondaryColor: Color = AsterAmberBright,
    glowAlpha: Float = 0.65f,
    statusDotColor: Color = AsterOnlineGreen,
    imagePainter: Painter? = null,
    @DrawableRes imageResId: Int? = null,
    contentDescription: String? = "Aster Avatar",
    onClick: (() -> Unit)? = null
) {
    val effectiveGlowRadius = if (showGlow) glowRadius else 0.dp
    val totalBoxSize = avatarSize + (effectiveGlowRadius * 2)

    val infiniteTransition = rememberInfiniteTransition(label = "pulse_trans")
    val pulseScale by infiniteTransition.animateFloat(
        initialValue = 1.0f,
        targetValue = if (isPulsing) 1.25f else 1.05f,
        animationSpec = infiniteRepeatable(
            animation = tween(1500, easing = FastOutSlowInEasing),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulse_scale"
    )

    Box(
        modifier = modifier.size(totalBoxSize),
        contentAlignment = Alignment.Center
    ) {
        // 1. Ambient Warm Amber Halo / Bloom effect
        if (showGlow && effectiveGlowRadius > 0.dp) {
            Canvas(modifier = Modifier.size(totalBoxSize * (if (isPulsing) pulseScale else 1f))) {
                val canvasWidth = drawContext.size.width
                val canvasHeight = drawContext.size.height
                val centerOffset = Offset(canvasWidth / 2f, canvasHeight / 2f)
                val avatarRadiusPx = avatarSize.toPx() / 2f
                val totalRadiusPx = avatarRadiusPx + effectiveGlowRadius.toPx()

                val glowBrush = Brush.radialGradient(
                    colorStops = arrayOf(
                        0.0f to Color.Transparent,
                        (avatarRadiusPx * 0.6f / totalRadiusPx) to glowSecondaryColor.copy(alpha = glowAlpha * 0.85f),
                        (avatarRadiusPx / totalRadiusPx) to glowColor.copy(alpha = glowAlpha * 0.95f),
                        ((avatarRadiusPx + effectiveGlowRadius.toPx() * 0.5f) / totalRadiusPx) to glowColor.copy(alpha = glowAlpha * 0.40f),
                        1.0f to Color.Transparent
                    ),
                    center = centerOffset,
                    radius = totalRadiusPx
                )

                drawCircle(
                    brush = glowBrush,
                    radius = totalRadiusPx,
                    center = centerOffset
                )
            }
        }

        // 2. Circular Avatar Surface & Image
        Box(
            modifier = Modifier
                .size(avatarSize)
                .clip(CircleShape)
                .background(AsterSurfaceElevated)
                .then(
                    if (onClick != null) {
                        Modifier.clickable(
                            onClick = onClick
                        )
                    } else {
                        Modifier
                    }
                ),
            contentAlignment = Alignment.Center
        ) {
            val context = LocalContext.current
            val resolvedResId = imageResId ?: run {
                val id = context.resources.getIdentifier("aster_avatar", "drawable", context.packageName)
                if (id != 0) id else null
            }

            when {
                imagePainter != null -> {
                    Image(
                        painter = imagePainter,
                        contentDescription = contentDescription,
                        modifier = Modifier.size(avatarSize),
                        contentScale = ContentScale.Crop
                    )
                }
                resolvedResId != null && resolvedResId != 0 -> {
                    Image(
                        painter = painterResource(id = resolvedResId),
                        contentDescription = contentDescription,
                        modifier = Modifier.size(avatarSize),
                        contentScale = ContentScale.Crop
                    )
                }
                else -> {
                    Box(
                        modifier = Modifier
                            .size(avatarSize)
                            .background(
                                Brush.verticalGradient(
                                    listOf(Color(0xFF38291E), Color(0xFF221A14))
                                )
                            ),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = Icons.Default.Person,
                            contentDescription = contentDescription,
                            tint = AsterAmber,
                            modifier = Modifier.size(avatarSize * 0.55f)
                        )
                    }
                }
            }
        }

        // 3. Optional Status Dot (Online Green `#4CD964` with dark protective separation border)
        if (showStatusDot) {
            val dotSize = (avatarSize * 0.24f).coerceIn(9.dp, 18.dp)
            val strokeWidth = (dotSize * 0.18f).coerceIn(1.5.dp, 3.dp)
            val resolvedStatusColor = if (isOnline) statusDotColor else Color(0xFF8E8A83)

            val offsetDistance = (avatarSize / 2) * 0.7071f // cos(45 deg)
            Box(
                modifier = Modifier
                    .offset {
                        IntOffset(
                            x = offsetDistance.roundToPx(),
                            y = offsetDistance.roundToPx()
                        )
                    }
                    .size(dotSize)
                    .background(resolvedStatusColor, CircleShape)
                    .border(strokeWidth, AsterBackground, CircleShape)
            )
        }
    }
}

@Preview(name = "Small Avatar with Glow & Status Dot", showBackground = true, backgroundColor = 0xFF121110)
@Composable
fun PreviewAvatarWithGlowSmall() {
    AsterCompanionTheme {
        Box(modifier = Modifier.padding(24.dp)) {
            AvatarWithGlow(
                size = 52.dp,
                showOnlineDot = true,
                isOnline = true
            )
        }
    }
}

@Preview(name = "Large Companion Studio Avatar Aura", showBackground = true, backgroundColor = 0xFF121110)
@Composable
fun PreviewAvatarWithGlowLargeStudio() {
    AsterCompanionTheme {
        Box(modifier = Modifier.padding(32.dp)) {
            AvatarWithGlow(
                size = 144.dp,
                glowAlpha = 0.75f,
                showOnlineDot = false
            )
        }
    }
}
