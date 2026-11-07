package com.astercompanion.android.viewmodel

import com.astercompanion.android.MainDispatcherRule
import com.astercompanion.android.data.local.ProfileEntity
import com.astercompanion.android.data.remote.DefaultSupabaseApi
import com.astercompanion.android.model.CompanionProfile
import com.astercompanion.android.model.ScreenEvent
import com.astercompanion.android.repository.CompanionRepository
import com.astercompanion.android.testutil.FakeChatDao
import com.astercompanion.android.testutil.FakeMemoryDao
import com.astercompanion.android.testutil.FakeProfileDao
import com.astercompanion.android.testutil.FakeScreenEventDao
import com.astercompanion.android.testutil.FakeTodayDao
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test

@OptIn(ExperimentalCoroutinesApi::class)
class AwarenessViewModelTest {

    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()

    private val testDispatcher = StandardTestDispatcher()
    private val testScope = TestScope(testDispatcher)

    private lateinit var profileDao: FakeProfileDao
    private lateinit var todayDao: FakeTodayDao
    private lateinit var memoryDao: FakeMemoryDao
    private lateinit var chatDao: FakeChatDao
    private lateinit var screenEventDao: FakeScreenEventDao
    private lateinit var supabaseApi: DefaultSupabaseApi
    private lateinit var repository: CompanionRepository
    private lateinit var viewModel: AwarenessViewModel

    @Before
    fun setup() = testScope.runTest {
        profileDao = FakeProfileDao()
        todayDao = FakeTodayDao()
        memoryDao = FakeMemoryDao()
        chatDao = FakeChatDao()
        screenEventDao = FakeScreenEventDao()
        supabaseApi = DefaultSupabaseApi(simulatedDelayMs = 0L)

        val aster = CompanionProfile.defaultAster()
        profileDao.insertProfile(ProfileEntity.fromDomain(aster))

        repository = CompanionRepository(
            profileDao = profileDao,
            todayDao = todayDao,
            memoryDao = memoryDao,
            chatDao = chatDao,
            screenEventDao = screenEventDao,
            remoteApi = supabaseApi,
            ioDispatcher = testDispatcher
        )

        viewModel = AwarenessViewModel(repository)
    }

    @Test
    fun initialState_distinguishesCaptureAndAnalysisRates() = testScope.runTest {
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertEquals(CompanionProfile.PROFILE_ASTER_ID, state.activeProfileId)
        assertTrue(state.isCaptureActive)
        assertFalse(state.isPaused)
        assertFalse(state.isStopped)
        assertFalse(state.isMuted)

        // PRD §5.3: Distinct capture, upload, and analysis rates
        assertEquals(120.0f, state.captureFps, 0.01f)
        assertEquals(30.0f, state.uploadFps, 0.01f)
        assertEquals(5.0f, state.analysisFps, 0.01f)
    }

    @Test
    fun setFpsRates_updatesDistinctMetricsIndependently() {
        viewModel.setCaptureFps(60.0f)
        viewModel.setUploadFps(24.0f)
        viewModel.setAnalysisFps(4.0f)

        val state = viewModel.uiState.value
        assertEquals(60.0f, state.captureFps, 0.01f)
        assertEquals(24.0f, state.uploadFps, 0.01f)
        assertEquals(4.0f, state.analysisFps, 0.01f)
    }

    @Test
    fun pauseAndResume_updatesAwarenessState() {
        viewModel.pauseAwareness()
        assertTrue(viewModel.uiState.value.isPaused)
        assertEquals("Awareness Paused", viewModel.uiState.value.statusText)

        viewModel.resumeAwareness()
        assertFalse(viewModel.uiState.value.isPaused)
        assertEquals("Continuous Awareness Active", viewModel.uiState.value.statusText)
    }

    @Test
    fun stopAndStart_updatesAwarenessState() {
        viewModel.stopAwareness()
        assertTrue(viewModel.uiState.value.isStopped)
        assertFalse(viewModel.uiState.value.isCaptureActive)
        assertEquals("Awareness Stopped", viewModel.uiState.value.statusText)

        viewModel.startAwareness()
        assertFalse(viewModel.uiState.value.isStopped)
        assertTrue(viewModel.uiState.value.isCaptureActive)
        assertEquals("Continuous Awareness Active", viewModel.uiState.value.statusText)
    }

    @Test
    fun toggleMute_togglesAudioAwareness() {
        assertFalse(viewModel.uiState.value.isMuted)

        viewModel.toggleMute()
        assertTrue(viewModel.uiState.value.isMuted)
        assertEquals("Audio Muted — Video Only", viewModel.uiState.value.statusText)

        viewModel.toggleMute()
        assertFalse(viewModel.uiState.value.isMuted)
        assertEquals("Audio & Video Active", viewModel.uiState.value.statusText)
    }

    @Test
    fun recordEvent_enforcesMonotonicSequenceAndChecksum() = testScope.runTest {
        advanceUntilIdle()

        viewModel.recordEvent(ScreenEvent.EVENT_TYPE_SCENE_CHANGE, "Switched to Photos app")
        viewModel.recordEvent(ScreenEvent.EVENT_TYPE_TEXT_DETECTED, "Detected product title on screen")
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertEquals(2, state.recentEvents.size)

        val event1 = state.recentEvents[1] // Earlier event
        val event2 = state.recentEvents[0] // Latest event

        assertTrue(event2.sequenceNumber > event1.sequenceNumber)
        assertTrue(event1.checksum.isNotEmpty())
        assertTrue(event2.checksum.isNotEmpty())
        assertEquals("Switched to Photos app", event1.summary)
        assertEquals("Detected product title on screen", event2.summary)
    }
}
