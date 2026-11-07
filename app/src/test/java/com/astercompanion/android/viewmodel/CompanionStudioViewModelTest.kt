package com.astercompanion.android.viewmodel

import com.astercompanion.android.MainDispatcherRule
import com.astercompanion.android.data.local.ProfileEntity
import com.astercompanion.android.data.remote.DefaultSupabaseApi
import com.astercompanion.android.model.CompanionProfile
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
class CompanionStudioViewModelTest {

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
    private lateinit var viewModel: CompanionStudioViewModel

    @Before
    fun setup() = testScope.runTest {
        profileDao = FakeProfileDao()
        todayDao = FakeTodayDao()
        memoryDao = FakeMemoryDao()
        chatDao = FakeChatDao()
        screenEventDao = FakeScreenEventDao()
        supabaseApi = DefaultSupabaseApi(simulatedDelayMs = 0L)

        // Seed Aster and Nova
        val aster = CompanionProfile.defaultAster()
        val nova = CompanionProfile.defaultNova()
        profileDao.insertProfiles(
            listOf(
                ProfileEntity.fromDomain(aster),
                ProfileEntity.fromDomain(nova)
            )
        )

        repository = CompanionRepository(
            profileDao = profileDao,
            todayDao = todayDao,
            memoryDao = memoryDao,
            chatDao = chatDao,
            screenEventDao = screenEventDao,
            remoteApi = supabaseApi,
            ioDispatcher = testDispatcher
        )

        viewModel = CompanionStudioViewModel(repository)
    }

    @Test
    fun initialState_loadsAsterSettingsAndOptions() = testScope.runTest {
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertEquals(CompanionProfile.PROFILE_ASTER_ID, state.activeProfileId)
        assertEquals("Aster", state.name)
        assertEquals(CompanionProfile.HAIR_AUBURN, state.selectedHairColor)
        assertEquals(CompanionProfile.EYE_HAZEL, state.selectedEyeColor)
        assertEquals(CompanionProfile.STYLE_NATURAL, state.selectedStyle)
        assertEquals(CompanionProfile.VOICE_WARM, state.selectedVoice)

        // Verify available options match screenshot a98599e6
        assertEquals(listOf("Auburn", "Black", "Brown", "Blonde", "Silver"), state.availableHairColors)
        assertEquals(listOf("Hazel", "Brown", "Blue", "Green", "Grey"), state.availableEyeColors)
        assertEquals(listOf("Natural", "Casual", "Professional", "Creative"), state.availableStyles)
        assertEquals(listOf("Warm voice", "Calm", "Energetic", "Playful"), state.availableVoices)
    }

    @Test
    fun switchProfile_switchesToNovaAndLoadsNovaSettings() = testScope.runTest {
        advanceUntilIdle()

        viewModel.switchProfile(CompanionProfile.PROFILE_NOVA_ID)
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertFalse(state.isSwitchingProfile)
        assertEquals(CompanionProfile.PROFILE_NOVA_ID, state.activeProfileId)
        assertEquals("Nova", state.name)
        assertEquals("Switched to Nova", state.successMessage)
    }

    @Test
    fun chipSelections_updateUIState() {
        viewModel.onNameChanged("Aster AI")
        viewModel.selectHairColor(CompanionProfile.HAIR_BLACK)
        viewModel.selectEyeColor(CompanionProfile.EYE_BLUE)
        viewModel.selectStyle(CompanionProfile.STYLE_PROFESSIONAL)
        viewModel.selectVoice(CompanionProfile.VOICE_ENERGETIC)

        val state = viewModel.uiState.value
        assertEquals("Aster AI", state.name)
        assertEquals(CompanionProfile.HAIR_BLACK, state.selectedHairColor)
        assertEquals(CompanionProfile.EYE_BLUE, state.selectedEyeColor)
        assertEquals(CompanionProfile.STYLE_PROFESSIONAL, state.selectedStyle)
        assertEquals(CompanionProfile.VOICE_ENERGETIC, state.selectedVoice)
    }

    @Test
    fun saveSettings_persistsChangesSuccessfully() = testScope.runTest {
        advanceUntilIdle()

        viewModel.onNameChanged("Aster Prime")
        viewModel.selectVoice(CompanionProfile.VOICE_CALM)
        viewModel.selectStyle(CompanionProfile.STYLE_CREATIVE)
        viewModel.selectHairColor(CompanionProfile.HAIR_SILVER)
        viewModel.selectEyeColor(CompanionProfile.EYE_GREEN)

        viewModel.saveSettings()
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertFalse(state.isSaving)
        assertEquals("Companion settings saved successfully", state.successMessage)

        // Verify persistence in repository
        val active = repository.getActiveProfileOnce()
        assertEquals("Aster Prime", active?.name)
        assertEquals(CompanionProfile.VOICE_CALM, active?.voice)
        assertEquals(CompanionProfile.STYLE_CREATIVE, active?.style)
        assertEquals(CompanionProfile.HAIR_SILVER, active?.hairColor)
        assertEquals(CompanionProfile.EYE_GREEN, active?.eyeColor)
    }

    @Test
    fun saveSettings_validationFailsOnBlankName() = testScope.runTest {
        advanceUntilIdle()

        viewModel.onNameChanged("   ")
        viewModel.saveSettings()

        val state = viewModel.uiState.value
        assertEquals("Companion name cannot be empty", state.errorMessage)
    }
}
