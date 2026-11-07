package com.astercompanion.android.ui

import com.astercompanion.android.model.MessageSender
import com.astercompanion.android.ui.screens.chat.ChatViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class ChatViewModelTest {

    private val testDispatcher = StandardTestDispatcher()
    private lateinit var viewModel: ChatViewModel

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        viewModel = ChatViewModel()
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun testInitialStateMatchesScreenshotChat() {
        val state = viewModel.uiState.value
        assertEquals("Aster", state.companionName)
        assertTrue(state.isOnline)
        assertEquals(2, state.messages.size)

        val userMsg = state.messages[0]
        assertEquals(MessageSender.USER, userMsg.sender)
        assertEquals("Can you plan my Saturday?", userMsg.content)

        val companionMsg = state.messages[1]
        assertEquals(MessageSender.COMPANION, companionMsg.sender)
        assertEquals("Sure. You mentioned wanting a slow morning, so I kept it light.", companionMsg.content)
        assertNotNull(companionMsg.scheduleCard)
        assertEquals("Saturday, Nov 15", companionMsg.scheduleCard?.dateTitle)
        assertEquals(2, companionMsg.memoryCitations.size)
    }

    @Test
    fun testQuickActionsPopulateComposer() {
        viewModel.onQuickActionClick("Add reminder")
        assertEquals("Remind me to call Mom tomorrow morning", viewModel.uiState.value.inputText)

        viewModel.onQuickActionClick("Summarize")
        assertEquals("Can you summarize my tasks and schedule?", viewModel.uiState.value.inputText)
    }

    @Test
    fun testSendMessageAddsUserMessageAndTriggersStreaming() = runTest(testDispatcher) {
        viewModel.onInputTextChanged("Hello Aster, remind me about my flight")
        viewModel.sendMessage()

        val stateAfterSend = viewModel.uiState.value
        assertEquals("", stateAfterSend.inputText)
        assertTrue(stateAfterSend.isStreaming)
        val lastMsg = stateAfterSend.messages.last()
        assertEquals(MessageSender.USER, lastMsg.sender)
        assertEquals("Hello Aster, remind me about my flight", lastMsg.content)

        // Advance coroutines to simulate streaming completion
        testDispatcher.scheduler.advanceUntilIdle()

        val finalState = viewModel.uiState.value
        assertFalse(finalState.isStreaming)
        val streamedCompanionMsg = finalState.messages.last()
        assertEquals(MessageSender.COMPANION, streamedCompanionMsg.sender)
        assertTrue(streamedCompanionMsg.content.isNotEmpty())
    }

    @Test
    fun testCitationDialogLifecycle() {
        val citations = listOf("Memory 1", "Memory 2")
        viewModel.onCitationClick(citations)
        assertEquals(citations, viewModel.uiState.value.activeCitationDialog)

        viewModel.dismissCitationDialog()
        assertNull(viewModel.uiState.value.activeCitationDialog)
    }
}
