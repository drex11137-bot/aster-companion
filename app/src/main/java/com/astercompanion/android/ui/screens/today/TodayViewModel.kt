package com.astercompanion.android.ui.screens.today

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.astercompanion.android.model.CompanionTask
import com.astercompanion.android.model.RecentMemoryCard
import com.astercompanion.android.model.Reminder
import com.astercompanion.android.model.TodayData
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class TodayUiState(
    val companionName: String = "Aster",
    val userName: String = "Maya",
    val greeting: String = "Good evening, Maya",
    val tagline: String = "A calmer, brighter you — one step at a time.",
    val isOnline: Boolean = true,
    val nextReminder: Reminder? = Reminder(
        id = "rem_1",
        profileId = "profile_aster",
        title = "Call Dad at 7:30 PM",
        dayLabel = "Today",
        isSnoozed = false
    ),
    val tasks: List<CompanionTask> = listOf(
        CompanionTask(
            id = "task_1",
            profileId = "profile_aster",
            title = "Book dentist",
            dueLabel = "Today",
            isCompleted = false
        ),
        CompanionTask(
            id = "task_2",
            profileId = "profile_aster",
            title = "Finish budget draft",
            dueLabel = "Tomorrow",
            isCompleted = false
        ),
        CompanionTask(
            id = "task_3",
            profileId = "profile_aster",
            title = "Pick up parcel",
            dueLabel = "This week",
            isCompleted = false
        )
    ),
    val recentMemories: List<RecentMemoryCard> = listOf(
        RecentMemoryCard(
            id = "mem_1",
            profileId = "profile_aster",
            title = "You love oat flat whites",
            timeAgoLabel = "Noted 3 days ago",
            imageUrl = "memory_coffee"
        ),
        RecentMemoryCard(
            id = "mem_2",
            profileId = "profile_aster",
            title = "Sister's birthday: Nov 14",
            timeAgoLabel = "Added last week",
            imageUrl = "memory_flowers"
        ),
        RecentMemoryCard(
            id = "mem_3",
            profileId = "profile_aster",
            title = "Running a half marathon in March",
            timeAgoLabel = "Added 3 weeks ago",
            imageUrl = null
        )
    ),
    val isSnoozedFeedback: String? = null
)

class TodayViewModel : ViewModel() {

    private val _uiState = MutableStateFlow(TodayUiState())
    val uiState: StateFlow<TodayUiState> = _uiState.asStateFlow()

    fun snoozeReminder() {
        _uiState.update { current ->
            val reminder = current.nextReminder ?: return@update current
            val newSnoozed = !reminder.isSnoozed
            current.copy(
                nextReminder = reminder.copy(isSnoozed = newSnoozed),
                isSnoozedFeedback = if (newSnoozed) "Reminder snoozed for 15 minutes" else "Reminder resumed"
            )
        }
    }

    fun toggleTask(taskId: String) {
        _uiState.update { current ->
            val updatedTasks = current.tasks.map { task ->
                if (task.id == taskId) {
                    task.copy(isCompleted = !task.isCompleted)
                } else {
                    task
                }
            }
            current.copy(tasks = updatedTasks)
        }
    }

    fun dismissFeedback() {
        _uiState.update { it.copy(isSnoozedFeedback = null) }
    }
}
