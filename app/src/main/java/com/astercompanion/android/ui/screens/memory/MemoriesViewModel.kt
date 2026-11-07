package com.astercompanion.android.ui.screens.memory

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.astercompanion.android.model.MemoryCategories
import com.astercompanion.android.model.MemoryItem
import com.astercompanion.android.model.MemoryShareAudit
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class MemoriesUiState(
    val searchQuery: String = "",
    val selectedCategory: String = MemoryCategories.ALL,
    val memories: List<MemoryItem> = defaultMemoryItems(),
    val memoryToEdit: MemoryItem? = null,
    val memoryToDelete: MemoryItem? = null,
    val memoryToShare: MemoryItem? = null,
    val sharingTargetProfile: String = "Nova",
    val snackbarMessage: String? = null
)

fun defaultMemoryItems(): List<MemoryItem> {
    return listOf(
        MemoryItem(
            id = "mem_1",
            profileId = "profile_aster",
            title = "Prefers short answers\nin the morning",
            category = MemoryCategories.PREFERENCES,
            iconType = MemoryItem.ICON_SUN,
            addedAgoLabel = "Added 3 days ago"
        ),
        MemoryItem(
            id = "mem_2",
            profileId = "profile_aster",
            title = "Dad's number saved",
            category = MemoryCategories.PEOPLE,
            iconType = MemoryItem.ICON_PERSON,
            addedAgoLabel = "Added 1 week ago"
        ),
        MemoryItem(
            id = "mem_3",
            profileId = "profile_aster",
            title = "Allergic to peanuts",
            category = MemoryCategories.PREFERENCES,
            iconType = MemoryItem.ICON_PLUS,
            addedAgoLabel = "Added 2 weeks ago"
        ),
        MemoryItem(
            id = "mem_4",
            profileId = "profile_aster",
            title = "Running a half marathon\nin March",
            category = MemoryCategories.PLANS,
            iconType = MemoryItem.ICON_RUN,
            addedAgoLabel = "Added 3 weeks ago"
        )
    )
}

class MemoriesViewModel : ViewModel() {

    private val _uiState = MutableStateFlow(MemoriesUiState())
    val uiState: StateFlow<MemoriesUiState> = _uiState.asStateFlow()

    fun onSearchQueryChanged(query: String) {
        _uiState.update { it.copy(searchQuery = query) }
    }

    fun onCategorySelected(category: String) {
        _uiState.update { it.copy(selectedCategory = category) }
    }

    fun onStartEdit(memory: MemoryItem) {
        _uiState.update { it.copy(memoryToEdit = memory) }
    }

    fun onSaveEdit(memoryId: String, newTitle: String, newCategory: String) {
        _uiState.update { current ->
            val updated = current.memories.map {
                if (it.id == memoryId) it.copy(title = newTitle, category = newCategory, updatedAt = System.currentTimeMillis())
                else it
            }
            current.copy(
                memories = updated,
                memoryToEdit = null,
                snackbarMessage = "Memory updated successfully"
            )
        }
    }

    fun onDismissEdit() {
        _uiState.update { it.copy(memoryToEdit = null) }
    }

    fun onStartDelete(memory: MemoryItem) {
        _uiState.update { it.copy(memoryToDelete = memory) }
    }

    fun onConfirmDelete() {
        val toDelete = _uiState.value.memoryToDelete ?: return
        _uiState.update { current ->
            current.copy(
                memories = current.memories.filterNot { it.id == toDelete.id },
                memoryToDelete = null,
                snackbarMessage = "Memory deleted"
            )
        }
    }

    fun onDismissDelete() {
        _uiState.update { it.copy(memoryToDelete = null) }
    }

    fun onStartShare(memory: MemoryItem) {
        _uiState.update { it.copy(memoryToShare = memory) }
    }

    fun onConfirmShare(memoryId: String, targetProfileName: String) {
        _uiState.update { current ->
            val updated = current.memories.map {
                if (it.id == memoryId) {
                    it.copy(
                        isSharedWithOtherProfile = true,
                        sharedToProfileId = "profile_nova",
                        sharedAt = System.currentTimeMillis()
                    )
                } else it
            }
            current.copy(
                memories = updated,
                memoryToShare = null,
                snackbarMessage = "Memory explicitly shared with $targetProfileName with audit confirmation"
            )
        }
    }

    fun onDismissShare() {
        _uiState.update { it.copy(memoryToShare = null) }
    }

    fun dismissSnackbar() {
        _uiState.update { it.copy(snackbarMessage = null) }
    }
}
