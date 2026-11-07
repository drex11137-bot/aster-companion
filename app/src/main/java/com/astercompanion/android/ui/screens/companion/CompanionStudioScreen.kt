package com.astercompanion.android.ui.screens.companion

import androidx.compose.animation.animateColorAsState
import androidx.compose.foundation.Image
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
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Edit
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.drawBehind
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.astercompanion.android.model.CompanionProfile
import com.astercompanion.android.ui.theme.AsterAmber
import com.astercompanion.android.ui.theme.AsterBackground
import com.astercompanion.android.ui.theme.AsterCompanionTheme
import com.astercompanion.android.ui.theme.AsterSurface
import com.astercompanion.android.ui.theme.AsterSurfaceBorder
import com.astercompanion.android.ui.theme.AsterSurfaceElevated
import com.astercompanion.android.ui.theme.AsterTextPrimary
import com.astercompanion.android.ui.theme.AsterTextSecondary
import com.astercompanion.android.ui.theme.EyeBlue
import com.astercompanion.android.ui.theme.EyeBrown
import com.astercompanion.android.ui.theme.EyeGreen
import com.astercompanion.android.ui.theme.EyeGrey
import com.astercompanion.android.ui.theme.EyeHazel
import com.astercompanion.android.ui.theme.HairAuburn
import com.astercompanion.android.ui.theme.HairBlack
import com.astercompanion.android.ui.theme.HairBlonde
import com.astercompanion.android.ui.theme.HairBrown
import com.astercompanion.android.ui.theme.HairSilver

@Composable
fun CompanionStudioScreen(
    onNavigateToSettings: () -> Unit = {},
    viewModel: CompanionStudioViewModel = viewModel(),
    modifier: Modifier = Modifier
) {
    val state by viewModel.uiState.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(state.saveFeedbackMessage) {
        state.saveFeedbackMessage?.let { msg ->
            snackbarHostState.showSnackbar(msg)
            viewModel.dismissFeedback()
        }
    }

    CompanionStudioContent(
        state = state,
        onProfileSelected = viewModel::selectProfile,
        onStartEditName = viewModel::onStartEditName,
        onNameChange = viewModel::onNameChange,
        onConfirmNameEdit = viewModel::onConfirmNameEdit,
        onDismissNameEdit = viewModel::onDismissNameEdit,
        onSelectHairColor = viewModel::selectHairColor,
        onSelectEyeColor = viewModel::selectEyeColor,
        onSelectStyle = viewModel::selectStyle,
        onSelectVoice = viewModel::selectVoice,
        onSaveCompanion = viewModel::saveCompanion,
        onNavigateToSettings = onNavigateToSettings,
        snackbarHostState = snackbarHostState,
        modifier = modifier
    )
}

@Composable
fun CompanionStudioContent(
    state: CompanionStudioUiState,
    onProfileSelected: (String) -> Unit = {},
    onStartEditName: () -> Unit = {},
    onNameChange: (String) -> Unit = {},
    onConfirmNameEdit: () -> Unit = {},
    onDismissNameEdit: () -> Unit = {},
    onSelectHairColor: (String) -> Unit = {},
    onSelectEyeColor: (String) -> Unit = {},
    onSelectStyle: (String) -> Unit = {},
    onSelectVoice: (String) -> Unit = {},
    onSaveCompanion: () -> Unit = {},
    onNavigateToSettings: () -> Unit = {},
    snackbarHostState: SnackbarHostState = remember { SnackbarHostState() },
    modifier: Modifier = Modifier
) {
    val scrollState = rememberScrollState()
    val current = state.currentProfile
    val context = LocalContext.current

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(AsterBackground)
            .statusBarsPadding()
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(scrollState)
                .padding(horizontal = 20.dp, vertical = 16.dp)
        ) {
            // Header Row: Title, Subtitle, Settings Icon
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.Top
            ) {
                Column {
                    Text(
                        text = "Your companion",
                        color = AsterTextPrimary,
                        fontSize = 24.sp,
                        fontWeight = FontWeight.Bold
                    )
                    Spacer(modifier = Modifier.height(2.dp))
                    Text(
                        text = "Make it yours",
                        color = AsterTextSecondary,
                        fontSize = 14.sp
                    )
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

            Spacer(modifier = Modifier.height(24.dp))

            // Central Avatar Preview with Warm Amber Glow
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(220.dp),
                contentAlignment = Alignment.Center
            ) {
                // Ambient Radial Amber Glow behind avatar head
                Box(
                    modifier = Modifier
                        .size(220.dp)
                        .drawBehind {
                            drawCircle(
                                brush = Brush.radialGradient(
                                    colors = listOf(
                                        AsterAmber.copy(alpha = 0.5f),
                                        AsterAmber.copy(alpha = 0.2f),
                                        Color.Transparent
                                    )
                                )
                            )
                        }
                )

                // Large Circular Avatar Image
                val avatarResName = if (state.selectedProfileId == CompanionProfile.PROFILE_ASTER_ID) {
                    "aster_avatar"
                } else {
                    "nova_avatar"
                }
                val drawableId = context.resources.getIdentifier(avatarResName, "drawable", context.packageName)

                if (drawableId != 0) {
                    Image(
                        painter = painterResource(id = drawableId),
                        contentDescription = "Companion Avatar Preview",
                        contentScale = ContentScale.Crop,
                        modifier = Modifier
                            .size(150.dp)
                            .clip(CircleShape)
                    )
                } else {
                    Box(
                        modifier = Modifier
                            .size(150.dp)
                            .clip(CircleShape)
                            .background(Color(0xFF332517)),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = current.name.take(1),
                            color = AsterAmber,
                            fontSize = 48.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(18.dp))

            // Profile Switcher Pills (Aster vs Nova)
            ProfileSwitcherPill(
                selectedProfileId = state.selectedProfileId,
                onSelectProfile = onProfileSelected
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Name Field
            Text(
                text = "Name",
                color = AsterTextSecondary,
                fontSize = 13.sp,
                fontWeight = FontWeight.Medium
            )

            Spacer(modifier = Modifier.height(8.dp))

            Surface(
                shape = RoundedCornerShape(16.dp),
                color = AsterSurfaceElevated,
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp)
                    .clickable(onClick = onStartEditName)
            ) {
                Row(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = 16.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = current.name,
                        color = AsterTextPrimary,
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Medium
                    )

                    Icon(
                        imageVector = Icons.Outlined.Edit,
                        contentDescription = "Edit name",
                        tint = AsterTextSecondary,
                        modifier = Modifier.size(18.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Section: Appearance
            Text(
                text = "Appearance",
                color = AsterTextPrimary,
                fontSize = 16.sp,
                fontWeight = FontWeight.SemiBold
            )

            Spacer(modifier = Modifier.height(14.dp))

            // Subsection: Hair
            Text(
                text = "Hair",
                color = AsterTextSecondary,
                fontSize = 13.sp
            )

            Spacer(modifier = Modifier.height(10.dp))

            ColorSwatchesRow(
                swatches = listOf(
                    "Auburn" to HairAuburn,
                    "Black" to HairBlack,
                    "Brown" to HairBrown,
                    "Blonde" to HairBlonde,
                    "Silver" to HairSilver
                ),
                selectedName = current.hairColor,
                onSelect = onSelectHairColor
            )

            Spacer(modifier = Modifier.height(18.dp))

            // Subsection: Eyes
            Text(
                text = "Eyes",
                color = AsterTextSecondary,
                fontSize = 13.sp
            )

            Spacer(modifier = Modifier.height(10.dp))

            ColorSwatchesRow(
                swatches = listOf(
                    "Hazel" to EyeHazel,
                    "Brown" to EyeBrown,
                    "Blue" to EyeBlue,
                    "Green" to EyeGreen,
                    "Grey" to EyeGrey
                ),
                selectedName = current.eyeColor,
                onSelect = onSelectEyeColor
            )

            Spacer(modifier = Modifier.height(20.dp))

            // Subsection: Style
            Text(
                text = "Style",
                color = AsterTextSecondary,
                fontSize = 13.sp
            )

            Spacer(modifier = Modifier.height(10.dp))

            OptionChipsRow(
                options = CompanionProfile.ALL_STYLES,
                selectedOption = current.style,
                onSelect = onSelectStyle
            )

            Spacer(modifier = Modifier.height(20.dp))

            // Subsection: Voice
            Text(
                text = "Voice",
                color = AsterTextSecondary,
                fontSize = 13.sp
            )

            Spacer(modifier = Modifier.height(10.dp))

            OptionChipsRow(
                options = CompanionProfile.ALL_VOICES,
                selectedOption = current.voice,
                onSelect = onSelectVoice
            )

            Spacer(modifier = Modifier.height(30.dp))

            // Save Button
            Button(
                onClick = onSaveCompanion,
                shape = RoundedCornerShape(26.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = AsterAmber,
                    contentColor = AsterBackground
                ),
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp)
            ) {
                Text(
                    text = "Save companion",
                    fontSize = 16.sp,
                    fontWeight = FontWeight.SemiBold
                )
            }

            Spacer(modifier = Modifier.height(80.dp))
        }

        SnackbarHost(
            hostState = snackbarHostState,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = 80.dp)
        )

        // Rename Dialog
        if (state.isEditingName) {
            AlertDialog(
                onDismissRequest = onDismissNameEdit,
                title = {
                    Text(
                        text = "Edit Companion Name",
                        color = AsterTextPrimary,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold
                    )
                },
                text = {
                    OutlinedTextField(
                        value = state.editedName,
                        onValueChange = onNameChange,
                        label = { Text("Name") },
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = AsterAmber,
                            unfocusedBorderColor = AsterSurfaceBorder,
                            focusedTextColor = AsterTextPrimary,
                            unfocusedTextColor = AsterTextPrimary
                        ),
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                },
                confirmButton = {
                    Button(
                        onClick = onConfirmNameEdit,
                        colors = ButtonDefaults.buttonColors(containerColor = AsterAmber)
                    ) {
                        Text("Save", color = AsterBackground, fontWeight = FontWeight.SemiBold)
                    }
                },
                dismissButton = {
                    TextButton(onClick = onDismissNameEdit) {
                        Text("Cancel", color = AsterTextSecondary)
                    }
                },
                containerColor = AsterSurface
            )
        }
    }
}

@Composable
private fun ProfileSwitcherPill(
    selectedProfileId: String,
    onSelectProfile: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .height(48.dp),
        shape = RoundedCornerShape(24.dp),
        color = AsterSurfaceBorder.copy(alpha = 0.35f),
        border = androidx.compose.foundation.BorderStroke(1.dp, AsterSurfaceBorder)
    ) {
        Row(modifier = Modifier.fillMaxSize()) {
            val isAster = selectedProfileId == CompanionProfile.PROFILE_ASTER_ID

            // Aster Tab
            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxSize()
                    .clip(RoundedCornerShape(24.dp))
                    .background(if (isAster) Color(0xFF2E2214) else Color.Transparent)
                    .border(
                        width = if (isAster) 1.5.dp else 0.dp,
                        color = if (isAster) AsterAmber else Color.Transparent,
                        shape = RoundedCornerShape(24.dp)
                    )
                    .clickable { onSelectProfile(CompanionProfile.PROFILE_ASTER_ID) },
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "Aster",
                    color = if (isAster) AsterAmber else AsterTextSecondary,
                    fontSize = 15.sp,
                    fontWeight = if (isAster) FontWeight.SemiBold else FontWeight.Medium
                )
            }

            // Nova Tab
            Box(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxSize()
                    .clip(RoundedCornerShape(24.dp))
                    .background(if (!isAster) Color(0xFF2E2214) else Color.Transparent)
                    .border(
                        width = if (!isAster) 1.5.dp else 0.dp,
                        color = if (!isAster) AsterAmber else Color.Transparent,
                        shape = RoundedCornerShape(24.dp)
                    )
                    .clickable { onSelectProfile(CompanionProfile.PROFILE_NOVA_ID) },
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "Nova",
                    color = if (!isAster) AsterAmber else AsterTextSecondary,
                    fontSize = 15.sp,
                    fontWeight = if (!isAster) FontWeight.SemiBold else FontWeight.Medium
                )
            }
        }
    }
}

@Composable
private fun ColorSwatchesRow(
    swatches: List<Pair<String, Color>>,
    selectedName: String,
    onSelect: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        swatches.forEach { (name, color) ->
            val isSelected = name.equals(selectedName, ignoreCase = true)

            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                modifier = Modifier.clickable { onSelect(name) }
            ) {
                Box(
                    modifier = Modifier
                        .size(46.dp)
                        .clip(CircleShape)
                        .border(
                            width = if (isSelected) 2.dp else 0.dp,
                            color = if (isSelected) AsterAmber else Color.Transparent,
                            shape = CircleShape
                        )
                        .padding(if (isSelected) 3.dp else 0.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .clip(CircleShape)
                            .background(color)
                    )
                }

                Spacer(modifier = Modifier.height(6.dp))

                Text(
                    text = name,
                    color = if (isSelected) AsterAmber else AsterTextSecondary,
                    fontSize = 12.sp,
                    fontWeight = if (isSelected) FontWeight.SemiBold else FontWeight.Normal
                )
            }
        }
    }
}

@Composable
private fun OptionChipsRow(
    options: List<String>,
    selectedOption: String,
    onSelect: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    LazyRow(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        items(options) { option ->
            val isSelected = option.equals(selectedOption, ignoreCase = true)

            Box(
                modifier = Modifier
                    .height(38.dp)
                    .clip(RoundedCornerShape(19.dp))
                    .background(if (isSelected) Color(0xFF2E2214) else AsterSurfaceElevated)
                    .border(
                        width = 1.dp,
                        color = if (isSelected) AsterAmber else AsterSurfaceBorder,
                        shape = RoundedCornerShape(19.dp)
                    )
                    .clickable { onSelect(option) }
                    .padding(horizontal = 18.dp),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = option,
                    color = if (isSelected) AsterAmber else AsterTextPrimary,
                    fontSize = 13.sp,
                    fontWeight = if (isSelected) FontWeight.SemiBold else FontWeight.Medium
                )
            }
        }
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF121110)
@Composable
fun CompanionStudioPreview() {
    AsterCompanionTheme {
        CompanionStudioContent(state = CompanionStudioUiState())
    }
}
