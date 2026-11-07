package com.astercompanion.android.ui

import com.astercompanion.android.ui.screens.voice.CallSpeakerState
import com.astercompanion.android.ui.screens.voice.VoiceCallViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class VoiceCallViewModelTest {

    private val testDispatcher = StandardTestDispatcher()
    private lateinit var viewModel: VoiceCallViewModel

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        viewModel = VoiceCallViewModel(autoStartLoops = false)
    }

    @After
    fun tearDown() {
        viewModel.stopLoops()
        Dispatchers.resetMain()
    }

    @Test
    fun testInitialCallState() {
        val state = viewModel.uiState.value
        assertEquals("Aster", state.companionName)
        assertTrue(state.isCallActive)
        assertFalse(state.isMicMuted)
        assertTrue(state.isSpeakerOn)
        assertEquals(CallSpeakerState.COMPANION_SPEAKING, state.speakerState)
        assertTrue(state.liveTranscript.isNotEmpty())
    }

    @Test
    fun testBargeInInteraction() = runTest(testDispatcher) {
        viewModel.triggerBargeIn()

        // Immediate state is BARGE_IN_DETECTED
        assertEquals(CallSpeakerState.BARGE_IN_DETECTED, viewModel.uiState.value.speakerState)
        assertTrue(viewModel.uiState.value.liveTranscript.contains("Barge-in detected"))
        assertTrue(viewModel.uiState.value.userSpeechBuffer.isNotEmpty())

        // Advance dispatcher by 1500ms
        testDispatcher.scheduler.advanceTimeBy(1600)
        testDispatcher.scheduler.runCurrent()

        assertEquals(CallSpeakerState.COMPANION_SPEAKING, viewModel.uiState.value.speakerState)
        assertEquals("", viewModel.uiState.value.userSpeechBuffer)
    }

    @Test
    fun testAudioMuteAndSpeakerToggles() {
        assertFalse(viewModel.uiState.value.isMicMuted)
        viewModel.toggleMute()
        assertTrue(viewModel.uiState.value.isMicMuted)

        assertTrue(viewModel.uiState.value.isSpeakerOn)
        viewModel.toggleSpeaker()
        assertFalse(viewModel.uiState.value.isSpeakerOn)
    }

    @Test
    fun testEndCallTerminatesSession() {
        var callEndedInvoked = false
        viewModel.endCall {
            callEndedInvoked = true
        }
        assertFalse(viewModel.uiState.value.isCallActive)
        assertTrue(callEndedInvoked)
    }
}
