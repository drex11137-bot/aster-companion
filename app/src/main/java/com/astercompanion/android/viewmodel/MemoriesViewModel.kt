package com.astercompanion.android.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.astercompanion.android.model.CompanionProfile
import com.astercompanion.android.model.MemoryCategories
import com.astercompanion.android.model.MemoryItem
import com.astercompanion.android.model.MemoryShareAudit
import com.astercompanion.android.repository.CompanionRepository
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.flatMapLatest
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/**
 * UI State for the Memories screen.
 * Adheres strictly to UI reference screenshot (56d6d982-5337-4170-80e5-1e156d239b38.png).
 */
data class MemoriesUiState(
    val memories: List<MemoryItem> = emptyList(),
    val searchQuery: String = "",
    val activeCategory: String = MemoryCategories.ALL,
    val categories: List<String> = MemoryCategories.FILTER_CATEGORIES,
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    val successMessage: String? = null,
    // State for memory editing dialog
    val editingMemory: MemoryItem? = null,
    // State for explicit cross-profile sharing (PRD §9.4)
    val memoryPendingShare: MemoryItem? = null,
    val targetProfileIdForShare: String = CompanionProfile.PROFILE_NOVA_ID,
    val isSharingInProgress: Boolean = false,
    val lastShareAudit: MemoryShareAudit? = null
)

/**
 * ViewModel managing the Memories system in Aster Companion.
 * Adheres strictly to PRD v1.1 §9.4 & §14:
 * - Search query filtering.
 * - Active category filter chips ('All', 'People', 'Preferences', 'Plans').
 * - Memory deletion and editing.
 * - Explicit cross-profile sharing with user confirmation and audit logging.
 */
@OptIn(ExperimentalCoroutinesApi::class)
class MemoriesViewModel(
    private val repository: CompanionRepository
) : ViewModel() {

    private val _searchQuery = MutableStateFlow("")
    val searchQuery: StateFlow<String> = _searchQuery.asStateFlow()

    private val _activeCategory = MutableStateFlow(MemoryCategories.ALL)
    val activeCategory: StateFlow<String> = _activeCategory.asStateFlow()

    private val _uiState = MutableStateFlow(MemoriesUiState(isLoading = true))
    val uiState: StateFlow<MemoriesUiState> = _uiState.asStateFlow()

    init {
        observeMemories()
    }

    private fun observeMemories() {
        viewModelScope.launch {
            combine(_activeCategory, _searchQuery) { category, query ->
                Pair(category, query)
            }.flatMapLatest { (category, query) ->
                repository.getMemories(category, query)
            }.collect { memoryList ->
                _uiState.update { current ->
                    current.copy(
                        memories = memoryList,
                        isLoading = false,
                        searchQuery = _searchQuery.value,
                        activeCategory = _activeCategory.value
                    )
                }
            }
        }
    }

    fun onSearchQueryChanged(query: String) {
        _searchQuery.value = query
        _uiState.update { it.copy(searchQuery = query) }
    }

    fun selectCategory(category: String) {
        _activeCategory.value = category
        _uiState.update { it.copy(activeCategory = category) }
    }

    /**
     * Deletes a memory item.
     */
    fun deleteMemory(memoryId: String) {
        viewModelScope.launch {
            val result = repository.deleteMemory(memoryId)
            if (result.isSuccess) {
                _uiState.update {
                    it.copy(successMessage = "Memory deleted successfully")
                }
            } else {
                _uiState.update {
                    it.copy(errorMessage = result.exceptionOrNull()?.message ?: "Failed to delete memory")
                }
            }
        }
    }

    /**
     * Opens the edit dialog for the specified memory item.
     */
    fun startEditingMemory(memory: MemoryItem) {
        _uiState.update { it.copy(editingMemory = memory) }
    }

    /**
     * Dismisses the edit dialog.
     */
    fun cancelEditing() {
        _uiState.update { it.copy(editingMemory = null) }
    }

    /**
     * Saves edits to an existing memory item.
     */
    fun saveMemoryEdit(memoryId: String, newTitle: String, newCategory: String) {
        if (newTitle.isBlank()) {
            _uiState.update { it.copy(errorMessage = "Memory title cannot be empty") }
            return
        }

        viewModelScope.launch {
            val result = repository.updateMemory(memoryId, newTitle, newCategory)
            if (result.isSuccess) {
                _uiState.update {
                    it.copy(
                        editingMemory = null,
                        successMessage = "Memory updated"
                    )
                }
            } else {
                _uiState.update {
                    it.copy(errorMessage = result.exceptionOrNull()?.message ?: "Failed to update memory")
                }
            }
        }
    }

    /**
     * Adds a new memory item.
     */
    fun addMemory(title: String, category: String, iconType: String = MemoryItem.ICON_SUN) {
        if (title.isBlank()) {
            _uiState.update { it.copy(errorMessage = "Memory title cannot be empty") }
            return
        }

        viewModelScope.launch {
            val result = repository.addMemory(title, category, iconType)
            if (result.isSuccess) {
                _uiState.update { it.copy(successMessage = "Memory saved") }
            } else {
                _uiState.update {
                    it.copy(errorMessage = result.exceptionOrNull()?.message ?: "Failed to save memory")
                }
            }
        }
    }

    /**
     * Initiates explicit sharing flow to profile B (e.g. Nova).
     * PRD §9.4 requirement: Clear identification and explicit user confirmation.
     */
    fun initiateShareToProfile(memory: MemoryItem, targetProfileId: String = CompanionProfile.PROFILE_NOVA_ID) {
        _uiState.update {
            it.copy(
                memoryPendingShare = memory,
                targetProfileIdForShare = targetProfileId,
                errorMessage = null
            )
        }
    }

    fun cancelShare() {
        _uiState.update {
            it.copy(memoryPendingShare = null)
        }
    }

    /**
     * Confirms and executes explicit sharing of an individual memory to Profile B.
     * Generates immutable audit trail per PRD §9.4.
     */
    fun confirmShare() {
        val memory = _uiState.value.memoryPendingShare ?: return
        val targetProfileId = _uiState.value.targetProfileIdForShare

        _uiState.update { it.copy(isSharingInProgress = true) }

        viewModelScope.launch {
            val result = repository.shareMemoryToProfile(memory.id, targetProfileId)
            if (result.isSuccess) {
                val audit = result.getOrNull()
                _uiState.update {
                    it.copy(
                        isSharingInProgress = false,
                        memoryPendingShare = null,
                        lastShareAudit = audit,
                        successMessage = "Explicitly shared '${memory.title}' to profile $targetProfileId"
                    )
                }
            } else {
                _uiState.update {
                    it.copy(
                        isSharingInProgress = false,
                        errorMessage = result.exceptionOrNull()?.message ?: "Failed to share memory"
                    )
                }
            }
        }
    }

    fun clearMessages() {
        _uiState.update { it.copy(errorMessage = null, successMessage = null) }
    }
}
