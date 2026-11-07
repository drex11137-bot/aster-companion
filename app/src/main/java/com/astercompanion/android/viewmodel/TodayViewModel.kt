package com.astercompanion.android.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.astercompanion.android.model.CompanionTask
import com.astercompanion.android.model.RecentMemoryCard
import com.astercompanion.android.model.Reminder
import com.astercompanion.android.repository.CompanionRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/**
 * UI State for the Today screen.
 * Adheres strictly to UI reference screenshot (56539447-5086-44aa-b0ad-b98fa9cb6a8d.png).
 */
data class TodayUiState(
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    val companionName: String = "Aster",
    val greeting: String = "Good evening, Maya",
    val tagline: String = "A calmer, brighter you — one step at a time.",
    val isCompanionOnline: Boolean = true,
    val avatarUrl: String = "",
    val nextReminder: Reminder? = null,
    val tasks: List<CompanionTask> = emptyList(),
    val recentMemories: List<RecentMemoryCard> = emptyList(),
    val isSnoozing: Boolean = false
)

/**
 * ViewModel managing the Today screen in Aster Companion.
 * - Next reminder with snooze capability.
 * - Tasks list with interactive checkbox toggling.
 * - Recent memories preview cards.
 * - Companion online status and greeting.
 */
class TodayViewModel(
    private val repository: CompanionRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(TodayUiState(isLoading = true))
    val uiState: StateFlow<TodayUiState> = _uiState.asStateFlow()

    init {
        observeTodayData()
        refreshTodayData()
    }

    private fun observeTodayData() {
        viewModelScope.launch {
            repository.getTodayData()
                .catch { error ->
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            errorMessage = error.message ?: "Failed to load today's data"
                        )
                    }
                }
                .collect { data ->
                    _uiState.update { current ->
                        current.copy(
                            isLoading = false,
                            errorMessage = null,
                            companionName = data.companionName,
                            greeting = data.greeting,
                            tagline = data.tagline,
                            isCompanionOnline = data.isOnline,
                            avatarUrl = data.avatarUrl,
                            nextReminder = data.nextReminder,
                            tasks = data.tasks,
                            recentMemories = data.recentMemories
                        )
                    }
                }
        }
    }

    fun refreshTodayData() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, errorMessage = null) }
            val result = repository.refreshTodayData()
            if (result.isFailure) {
                _uiState.update {
                    it.copy(
                        isLoading = false,
                        errorMessage = result.exceptionOrNull()?.message ?: "Refresh failed"
                    )
                }
            } else {
                _uiState.update { it.copy(isLoading = false) }
            }
        }
    }

    /**
     * Toggles a task's checkbox state with optimistic UI update followed by repository persistence.
     */
    fun toggleTask(taskId: String) {
        val currentTasks = _uiState.value.tasks
        val target = currentTasks.find { it.id == taskId } ?: return
        val newStatus = !target.isCompleted

        // Optimistic update
        _uiState.update { state ->
            val updated = state.tasks.map { task ->
                if (task.id == taskId) task.copy(isCompleted = newStatus) else task
            }
            state.copy(tasks = updated)
        }

        viewModelScope.launch {
            val result = repository.toggleTask(taskId, newStatus)
            if (result.isFailure) {
                // Revert on failure
                _uiState.update { state ->
                    val reverted = state.tasks.map { task ->
                        if (task.id == taskId) target else task
                    }
                    state.copy(
                        tasks = reverted,
                        errorMessage = "Failed to update task status"
                    )
                }
            }
        }
    }

    /**
     * Snoozes the current active reminder.
     */
    fun snoozeReminder(reminderId: String) {
        _uiState.update { it.copy(isSnoozing = true) }
        viewModelScope.launch {
            val result = repository.snoozeReminder(reminderId)
            _uiState.update { state ->
                if (result.isSuccess) {
                    state.copy(
                        isSnoozing = false,
                        nextReminder = state.nextReminder?.copy(isSnoozed = true)
                    )
                } else {
                    state.copy(
                        isSnoozing = false,
                        errorMessage = "Failed to snooze reminder"
                    )
                }
            }
        }
    }

    fun clearError() {
        _uiState.update { it.copy(errorMessage = null) }
    }
}
