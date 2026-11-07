package com.astercompanion.android.ui

import com.astercompanion.android.ui.screens.today.TodayViewModel
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class TodayViewModelTest {

    private lateinit var viewModel: TodayViewModel

    @Before
    fun setUp() {
        viewModel = TodayViewModel()
    }

    @Test
    fun testInitialStateMatchesDesignSpecification() {
        val state = viewModel.uiState.value
        assertEquals("Aster", state.companionName)
        assertEquals("Maya", state.userName)
        assertEquals("Good evening, Maya", state.greeting)
        assertEquals("A calmer, brighter you — one step at a time.", state.tagline)
        assertTrue(state.isOnline)

        assertNotNull(state.nextReminder)
        assertEquals("Call Dad at 7:30 PM", state.nextReminder?.title)
        assertEquals("Today", state.nextReminder?.dayLabel)
        assertFalse(state.nextReminder?.isSnoozed ?: true)

        assertEquals(3, state.tasks.size)
        assertEquals("Book dentist", state.tasks[0].title)
        assertEquals("Finish budget draft", state.tasks[1].title)
        assertEquals("Pick up parcel", state.tasks[2].title)

        assertEquals(3, state.recentMemories.size)
        assertEquals("You love oat flat whites", state.recentMemories[0].title)
        assertEquals("Sister's birthday: Nov 14", state.recentMemories[1].title)
    }

    @Test
    fun testSnoozeReminderTogglesState() {
        assertFalse(viewModel.uiState.value.nextReminder?.isSnoozed ?: true)

        viewModel.snoozeReminder()
        assertTrue(viewModel.uiState.value.nextReminder?.isSnoozed ?: false)
        assertEquals("Reminder snoozed for 15 minutes", viewModel.uiState.value.isSnoozedFeedback)

        viewModel.snoozeReminder()
        assertFalse(viewModel.uiState.value.nextReminder?.isSnoozed ?: true)
        assertEquals("Reminder resumed", viewModel.uiState.value.isSnoozedFeedback)

        viewModel.dismissFeedback()
        assertNull(viewModel.uiState.value.isSnoozedFeedback)
    }

    @Test
    fun testToggleTaskTogglesCompletion() {
        val taskId = "task_1"
        assertFalse(viewModel.uiState.value.tasks.first { it.id == taskId }.isCompleted)

        viewModel.toggleTask(taskId)
        assertTrue(viewModel.uiState.value.tasks.first { it.id == taskId }.isCompleted)

        viewModel.toggleTask(taskId)
        assertFalse(viewModel.uiState.value.tasks.first { it.id == taskId }.isCompleted)
    }
}
