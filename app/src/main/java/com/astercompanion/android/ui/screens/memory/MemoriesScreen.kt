package com.astercompanion.android.ui.screens.memory

import androidx.compose.animation.AnimatedVisibility
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
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.DirectionsRun
import androidx.compose.material.icons.outlined.Close
import androidx.compose.material.icons.outlined.Delete
import androidx.compose.material.icons.outlined.Edit
import androidx.compose.material.icons.outlined.LocalHospital
import androidx.compose.material.icons.outlined.Person
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material.icons.outlined.Share
import androidx.compose.material.icons.outlined.WbSunny
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ModalBottomSheet
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.rememberModalBottomSheetState
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.astercompanion.android.model.MemoryCategories
import com.astercompanion.android.model.MemoryItem
import com.astercompanion.android.ui.theme.AsterAmber
import com.astercompanion.android.ui.theme.AsterBackground
import com.astercompanion.android.ui.theme.AsterCompanionTheme
import com.astercompanion.android.ui.theme.AsterErrorRed
import com.astercompanion.android.ui.theme.AsterSurface
import com.astercompanion.android.ui.theme.AsterSurfaceBorder
import com.astercompanion.android.ui.theme.AsterSurfaceElevated
import com.astercompanion.android.ui.theme.AsterTextMuted
import com.astercompanion.android.ui.theme.AsterTextPrimary
import com.astercompanion.android.ui.theme.AsterTextSecondary

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MemoriesScreen(
    viewModel: MemoriesViewModel = viewModel(),
    modifier: Modifier = Modifier
) {
    val state by viewModel.uiState.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }

    LaunchedEffect(state.snackbarMessage) {
        state.snackbarMessage?.let { msg ->
            snackbarHostState.showSnackbar(msg)
            viewModel.dismissSnackbar()
        }
    }

    MemoriesScreenContent(
        state = state,
        onSearchQueryChanged = viewModel::onSearchQueryChanged,
        onCategorySelected = viewModel::onCategorySelected,
        onStartEdit = viewModel::onStartEdit,
        onSaveEdit = viewModel::onSaveEdit,
        onDismissEdit = viewModel::onDismissEdit,
        onStartDelete = viewModel::onStartDelete,
        onConfirmDelete = viewModel::onConfirmDelete,
        onDismissDelete = viewModel::onDismissDelete,
        onStartShare = viewModel::onStartShare,
        onConfirmShare = viewModel::onConfirmShare,
        onDismissShare = viewModel::onDismissShare,
        snackbarHostState = snackbarHostState,
        modifier = modifier
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MemoriesScreenContent(
    state: MemoriesUiState,
    onSearchQueryChanged: (String) -> Unit = {},
    onCategorySelected: (String) -> Unit = {},
    onStartEdit: (MemoryItem) -> Unit = {},
    onSaveEdit: (String, String, String) -> Unit = { _, _, _ -> },
    onDismissEdit: () -> Unit = {},
    onStartDelete: (MemoryItem) -> Unit = {},
    onConfirmDelete: () -> Unit = {},
    onDismissDelete: () -> Unit = {},
    onStartShare: (MemoryItem) -> Unit = {},
    onConfirmShare: (String, String) -> Unit = { _, _ -> },
    onDismissShare: () -> Unit = {},
    snackbarHostState: SnackbarHostState = remember { SnackbarHostState() },
    modifier: Modifier = Modifier
) {
    val filteredMemories = remember(state.memories, state.searchQuery, state.selectedCategory) {
        state.memories.filter { item ->
            val matchesCategory = if (state.selectedCategory == MemoryCategories.ALL) true
            else item.category.equals(state.selectedCategory, ignoreCase = true)

            val matchesQuery = if (state.searchQuery.isBlank()) true
            else item.title.contains(state.searchQuery, ignoreCase = true)

            matchesCategory && matchesQuery
        }
    }

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
            // Header: Title & Subtitle matching Screenshot (56d6d982)
            Text(
                text = "Memories",
                color = AsterTextPrimary,
                fontSize = 28.sp,
                fontWeight = FontWeight.Bold,
                letterSpacing = (-0.5).sp
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = "The little things that matter.",
                color = AsterTextSecondary,
                fontSize = 14.sp
            )

            Spacer(modifier = Modifier.height(20.dp))

            // Search Bar pill
            MemorySearchBar(
                query = state.searchQuery,
                onQueryChange = onSearchQueryChanged
            )

            Spacer(modifier = Modifier.height(18.dp))

            // Filter Chips (All, People, Preferences, Plans)
            MemoryFilterChipsRow(
                categories = MemoryCategories.FILTER_CATEGORIES,
                selectedCategory = state.selectedCategory,
                onCategorySelected = onCategorySelected
            )

            Spacer(modifier = Modifier.height(16.dp))

            // Memories List
            LazyColumn(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(12.dp),
                contentPadding = PaddingValues(bottom = 80.dp)
            ) {
                items(filteredMemories, key = { it.id }) { memory ->
                    MemoryCardItem(
                        memory = memory,
                        onEdit = { onStartEdit(memory) },
                        onDelete = { onStartDelete(memory) },
                        onShare = { onStartShare(memory) }
                    )
                }

                if (filteredMemories.isEmpty()) {
                    item {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 48.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = "No memories found",
                                color = AsterTextSecondary,
                                fontSize = 14.sp
                            )
                        }
                    }
                }
            }
        }

        SnackbarHost(
            hostState = snackbarHostState,
            modifier = Modifier
                .align(Alignment.BottomCenter)
                .padding(bottom = 80.dp)
        )

        // Edit Memory Dialog
        state.memoryToEdit?.let { memory ->
            EditMemoryDialog(
                memory = memory,
                onSave = { newTitle, newCategory ->
                    onSaveEdit(memory.id, newTitle, newCategory)
                },
                onDismiss = onDismissEdit
            )
        }

        // Delete Confirmation Dialog
        state.memoryToDelete?.let { memory ->
            AlertDialog(
                onDismissRequest = onDismissDelete,
                title = {
                    Text(
                        text = "Delete Memory?",
                        color = AsterTextPrimary,
                        fontSize = 18.sp,
                        fontWeight = FontWeight.Bold
                    )
                },
                text = {
                    Text(
                        text = "Are you sure you want to delete \"${memory.title.replace("\n", " ")}\"? This action cannot be undone.",
                        color = AsterTextSecondary,
                        fontSize = 14.sp
                    )
                },
                confirmButton = {
                    Button(
                        onClick = onConfirmDelete,
                        colors = ButtonDefaults.buttonColors(containerColor = AsterErrorRed)
                    ) {
                        Text("Delete", color = Color.White)
                    }
                },
                dismissButton = {
                    TextButton(onClick = onDismissDelete) {
                        Text("Cancel", color = AsterTextSecondary)
                    }
                },
                containerColor = AsterSurface
            )
        }

        // Explicit Sharing Modal per PRD §9.4 / §14
        state.memoryToShare?.let { memory ->
            ExplicitSharingModal(
                memory = memory,
                targetProfileName = state.sharingTargetProfile,
                onConfirmShare = {
                    onConfirmShare(memory.id, state.sharingTargetProfile)
                },
                onDismiss = onDismissShare
            )
        }
    }
}

@Composable
private fun MemorySearchBar(
    query: String,
    onQueryChange: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    Surface(
        modifier = modifier
            .fillMaxWidth()
            .height(50.dp),
        shape = RoundedCornerShape(25.dp),
        color = AsterSurfaceElevated
    ) {
        Row(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = Icons.Outlined.Search,
                contentDescription = "Search",
                tint = AsterTextSecondary,
                modifier = Modifier.size(20.dp)
            )

            Spacer(modifier = Modifier.width(12.dp))

            BasicTextField(
                value = query,
                onValueChange = onQueryChange,
                modifier = Modifier.weight(1f),
                textStyle = TextStyle(
                    color = AsterTextPrimary,
                    fontSize = 15.sp
                ),
                cursorBrush = SolidColor(AsterAmber),
                singleLine = true,
                decorationBox = { innerTextField ->
                    if (query.isEmpty()) {
                        Text(
                            text = "Search memories",
                            color = AsterTextSecondary,
                            fontSize = 15.sp
                        )
                    }
                    innerTextField()
                }
            )

            if (query.isNotEmpty()) {
                IconButton(
                    onClick = { onQueryChange("") },
                    modifier = Modifier.size(28.dp)
                ) {
                    Icon(
                        imageVector = Icons.Outlined.Close,
                        contentDescription = "Clear",
                        tint = AsterTextSecondary,
                        modifier = Modifier.size(16.dp)
                    )
                }
            }
        }
    }
}

@Composable
private fun MemoryFilterChipsRow(
    categories: List<String>,
    selectedCategory: String,
    onCategorySelected: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    LazyRow(
        modifier = modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        items(categories) { category ->
            val isSelected = category.equals(selectedCategory, ignoreCase = true)

            Box(
                modifier = Modifier
                    .height(38.dp)
                    .clip(RoundedCornerShape(19.dp))
                    .background(if (isSelected) AsterAmber else AsterSurface)
                    .border(
                        width = 1.dp,
                        color = if (isSelected) AsterAmber else AsterSurfaceBorder,
                        shape = RoundedCornerShape(19.dp)
                    )
                    .clickable { onCategorySelected(category) }
                    .padding(horizontal = 20.dp),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = category,
                    color = if (isSelected) AsterBackground else AsterTextPrimary,
                    fontSize = 14.sp,
                    fontWeight = if (isSelected) FontWeight.SemiBold else FontWeight.Medium
                )
            }
        }
    }
}

@Composable
private fun MemoryCardItem(
    memory: MemoryItem,
    onEdit: () -> Unit,
    onDelete: () -> Unit,
    onShare: () -> Unit,
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
                .padding(horizontal = 16.dp, vertical = 18.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Amber circular badge with icon
            Box(
                modifier = Modifier
                    .size(46.dp)
                    .clip(CircleShape)
                    .background(Color(0xFF332517)),
                contentAlignment = Alignment.Center
            ) {
                val icon = when (memory.iconType) {
                    MemoryItem.ICON_SUN -> Icons.Outlined.WbSunny
                    MemoryItem.ICON_PERSON -> Icons.Outlined.Person
                    MemoryItem.ICON_PLUS -> Icons.Outlined.LocalHospital
                    MemoryItem.ICON_RUN -> Icons.Outlined.DirectionsRun
                    else -> Icons.Outlined.WbSunny
                }
                Icon(
                    imageVector = icon,
                    contentDescription = null,
                    tint = AsterAmber,
                    modifier = Modifier.size(22.dp)
                )
            }

            Spacer(modifier = Modifier.width(16.dp))

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = memory.title,
                    color = AsterTextPrimary,
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Medium,
                    lineHeight = 20.sp
                )

                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = memory.addedAgoLabel,
                    color = AsterTextSecondary,
                    fontSize = 12.sp
                )
            }

            // Explicit Share Action
            IconButton(
                onClick = onShare,
                modifier = Modifier.size(34.dp)
            ) {
                Icon(
                    imageVector = Icons.Outlined.Share,
                    contentDescription = "Explicit Share",
                    tint = AsterTextSecondary,
                    modifier = Modifier.size(18.dp)
                )
            }

            // Edit Action (pencil)
            IconButton(
                onClick = onEdit,
                modifier = Modifier.size(34.dp)
            ) {
                Icon(
                    imageVector = Icons.Outlined.Edit,
                    contentDescription = "Edit Memory",
                    tint = AsterTextSecondary,
                    modifier = Modifier.size(18.dp)
                )
            }

            // Delete Action (trash)
            IconButton(
                onClick = onDelete,
                modifier = Modifier.size(34.dp)
            ) {
                Icon(
                    imageVector = Icons.Outlined.Delete,
                    contentDescription = "Delete Memory",
                    tint = AsterTextSecondary,
                    modifier = Modifier.size(18.dp)
                )
            }
        }
    }
}

@Composable
private fun EditMemoryDialog(
    memory: MemoryItem,
    onSave: (String, String) -> Unit,
    onDismiss: () -> Unit
) {
    var titleText by remember { mutableStateOf(memory.title) }
    var selectedCat by remember { mutableStateOf(memory.category) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = {
            Text(
                text = "Edit Memory",
                color = AsterTextPrimary,
                fontSize = 18.sp,
                fontWeight = FontWeight.Bold
            )
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
                OutlinedTextField(
                    value = titleText,
                    onValueChange = { titleText = it },
                    label = { Text("Memory Content") },
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = AsterAmber,
                        unfocusedBorderColor = AsterSurfaceBorder,
                        focusedTextColor = AsterTextPrimary,
                        unfocusedTextColor = AsterTextPrimary
                    ),
                    modifier = Modifier.fillMaxWidth()
                )

                Text(
                    text = "Category",
                    color = AsterTextSecondary,
                    fontSize = 13.sp
                )

                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    MemoryCategories.EDITABLE_CATEGORIES.forEach { cat ->
                        val isSelected = cat == selectedCat
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(12.dp))
                                .background(if (isSelected) AsterAmber else AsterSurfaceElevated)
                                .clickable { selectedCat = cat }
                                .padding(horizontal = 12.dp, vertical = 6.dp)
                        ) {
                            Text(
                                text = cat,
                                color = if (isSelected) AsterBackground else AsterTextPrimary,
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Medium
                            )
                        }
                    }
                }
            }
        },
        confirmButton = {
            Button(
                onClick = { onSave(titleText, selectedCat) },
                colors = ButtonDefaults.buttonColors(containerColor = AsterAmber)
            ) {
                Text("Save", color = AsterBackground, fontWeight = FontWeight.SemiBold)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel", color = AsterTextSecondary)
            }
        },
        containerColor = AsterSurface
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ExplicitSharingModal(
    memory: MemoryItem,
    targetProfileName: String,
    onConfirmShare: () -> Unit,
    onDismiss: () -> Unit
) {
    val sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true)

    ModalBottomSheet(
        onDismissRequest = onDismiss,
        sheetState = sheetState,
        containerColor = AsterSurface
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp, vertical = 16.dp)
        ) {
            Text(
                text = "Explicit Memory Sharing",
                color = AsterTextPrimary,
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = "Under Aster Companion's strict privacy policy, memories are isolated by default. Do you want to explicitly replicate this memory across profiles?",
                color = AsterTextSecondary,
                fontSize = 14.sp,
                lineHeight = 20.sp
            )

            Spacer(modifier = Modifier.height(16.dp))

            Surface(
                shape = RoundedCornerShape(14.dp),
                color = AsterSurfaceElevated,
                modifier = Modifier.fillMaxWidth()
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        text = "Memory to share:",
                        color = AsterTextSecondary,
                        fontSize = 12.sp
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = memory.title,
                        color = AsterTextPrimary,
                        fontSize = 15.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "Source: Aster  ➔  Destination: $targetProfileName",
                        color = AsterAmber,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Medium
                    )
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                Button(
                    onClick = onDismiss,
                    colors = ButtonDefaults.buttonColors(containerColor = AsterSurfaceElevated),
                    modifier = Modifier.weight(1f)
                ) {
                    Text("Cancel", color = AsterTextSecondary)
                }

                Button(
                    onClick = onConfirmShare,
                    colors = ButtonDefaults.buttonColors(containerColor = AsterAmber),
                    modifier = Modifier.weight(1f)
                ) {
                    Text("Confirm Share", color = AsterBackground, fontWeight = FontWeight.SemiBold)
                }
            }

            Spacer(modifier = Modifier.height(24.dp))
        }
    }
}

@Preview(showBackground = true, backgroundColor = 0xFF121110)
@Composable
fun MemoriesScreenPreview() {
    AsterCompanionTheme {
        MemoriesScreenContent(state = MemoriesUiState())
    }
}
