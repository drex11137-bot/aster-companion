package com.astercompanion.android.ui

import com.astercompanion.android.ui.screens.awareness.AwarenessViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.resetMain
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
class AwarenessViewModelTest {

    private val testDispatcher = StandardTestDispatcher()
    private lateinit var viewModel: AwarenessViewModel

    @Before
    fun setUp() {
        Dispatchers.setMain(testDispatcher)
        viewModel = AwarenessViewModel()
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    @Test
    fun testInitialAwarenessState() {
        val state = viewModel.uiState.value
        assertEquals("Aster", state.activeProfileName)
        assertTrue(state.isCaptureActive)
        assertFalse(state.isPaused)
        assertFalse(state.isStopped)
        assertFalse(state.isMuted)
        assertEquals(60.0f, state.captureFps, 2.0f)
        assertEquals(30.0f, state.uploadFps, 2.0f)
        assertEquals(5.0f, state.analysisFps, 1.0f)
        assertEquals(0, state.totalGapsDetected)
        assertTrue(state.recentEvents.isNotEmpty())
    }

    @Test
    fun testTogglePauseControl() {
        assertFalse(viewModel.uiState.value.isPaused)

        viewModel.togglePause()
        assertTrue(viewModel.uiState.value.isPaused)
        assertEquals("Awareness capture paused", viewModel.uiState.value.feedbackToast)

        viewModel.togglePause()
        assertFalse(viewModel.uiState.value.isPaused)
        assertEquals("Awareness capture resumed", viewModel.uiState.value.feedbackToast)

        viewModel.dismissFeedback()
        assertNull(viewModel.uiState.value.feedbackToast)
    }

    @Test
    fun testToggleStopControl() {
        assertFalse(viewModel.uiState.value.isStopped)
        assertTrue(viewModel.uiState.value.isCaptureActive)

        viewModel.toggleStop()
        assertTrue(viewModel.uiState.value.isStopped)
        assertFalse(viewModel.uiState.value.isCaptureActive)

        viewModel.toggleStop()
        assertFalse(viewModel.uiState.value.isStopped)
        assertTrue(viewModel.uiState.value.isCaptureActive)
    }

    @Test
    fun testToggleMuteControl() {
        assertFalse(viewModel.uiState.value.isMuted)

        viewModel.toggleMute()
        assertTrue(viewModel.uiState.value.isMuted)

        viewModel.toggleMute()
        assertFalse(viewModel.uiState.value.isMuted)
    }
}
