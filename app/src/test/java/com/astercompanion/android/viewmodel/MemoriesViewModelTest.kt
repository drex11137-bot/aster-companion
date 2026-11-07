package com.astercompanion.android.viewmodel

import com.astercompanion.android.MainDispatcherRule
import com.astercompanion.android.data.local.MemoryEntity
import com.astercompanion.android.data.local.ProfileEntity
import com.astercompanion.android.data.remote.DefaultSupabaseApi
import com.astercompanion.android.model.CompanionProfile
import com.astercompanion.android.model.MemoryCategories
import com.astercompanion.android.model.MemoryItem
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
class MemoriesViewModelTest {

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
    private lateinit var viewModel: MemoriesViewModel

    @Before
    fun setup() = testScope.runTest {
        profileDao = FakeProfileDao()
        todayDao = FakeTodayDao()
        memoryDao = FakeMemoryDao()
        chatDao = FakeChatDao()
        screenEventDao = FakeScreenEventDao()
        supabaseApi = DefaultSupabaseApi(simulatedDelayMs = 0L)

        // Seed Aster profile
        val aster = CompanionProfile.defaultAster()
        profileDao.insertProfile(ProfileEntity.fromDomain(aster))

        // Seed memories matching screenshot 56d6d982
        memoryDao.insertMemories(
            listOf(
                MemoryEntity(id = "m1", profileId = CompanionProfile.PROFILE_ASTER_ID, title = "Prefers short answers in the morning", category = MemoryCategories.PREFERENCES, iconType = MemoryItem.ICON_SUN, addedAgoLabel = "Added 3 days ago", createdAt = 1000L, updatedAt = 1000L),
                MemoryEntity(id = "m2", profileId = CompanionProfile.PROFILE_ASTER_ID, title = "Dad's number saved", category = MemoryCategories.PEOPLE, iconType = MemoryItem.ICON_PERSON, addedAgoLabel = "Added 1 week ago", createdAt = 2000L, updatedAt = 2000L),
                MemoryEntity(id = "m3", profileId = CompanionProfile.PROFILE_ASTER_ID, title = "Allergic to peanuts", category = MemoryCategories.PREFERENCES, iconType = MemoryItem.ICON_PLUS, addedAgoLabel = "Added 2 weeks ago", createdAt = 3000L, updatedAt = 3000L),
                MemoryEntity(id = "m4", profileId = CompanionProfile.PROFILE_ASTER_ID, title = "Running a half marathon in March", category = MemoryCategories.PLANS, iconType = MemoryItem.ICON_RUN, addedAgoLabel = "Added 3 weeks ago", createdAt = 4000L, updatedAt = 4000L)
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

        viewModel = MemoriesViewModel(repository)
    }

    @Test
    fun initialState_loadsAllMemoriesAndFilterCategories() = testScope.runTest {
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertFalse(state.isLoading)
        assertEquals(4, state.memories.size)
        assertEquals(MemoryCategories.ALL, state.activeCategory)
        assertEquals(listOf("All", "People", "Preferences", "Plans"), state.categories)
    }

    @Test
    fun selectCategory_filtersMemoryList() = testScope.runTest {
        advanceUntilIdle()

        // Filter by Preferences
        viewModel.selectCategory(MemoryCategories.PREFERENCES)
        advanceUntilIdle()

        val statePrefs = viewModel.uiState.value
        assertEquals(2, statePrefs.memories.size)
        assertTrue(statePrefs.memories.all { it.category == MemoryCategories.PREFERENCES })

        // Filter by People
        viewModel.selectCategory(MemoryCategories.PEOPLE)
        advanceUntilIdle()

        val statePeople = viewModel.uiState.value
        assertEquals(1, statePeople.memories.size)
        assertEquals("Dad's number saved", statePeople.memories[0].title)

        // Filter by Plans
        viewModel.selectCategory(MemoryCategories.PLANS)
        advanceUntilIdle()

        val statePlans = viewModel.uiState.value
        assertEquals(1, statePlans.memories.size)
        assertEquals("Running a half marathon in March", statePlans.memories[0].title)
    }

    @Test
    fun onSearchQueryChanged_filtersMemoriesByTitle() = testScope.runTest {
        advanceUntilIdle()

        viewModel.onSearchQueryChanged("peanuts")
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertEquals(1, state.memories.size)
        assertEquals("Allergic to peanuts", state.memories[0].title)
    }

    @Test
    fun deleteMemory_removesMemoryFromState() = testScope.runTest {
        advanceUntilIdle()

        viewModel.deleteMemory("m1")
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertEquals(3, state.memories.size)
        assertTrue(state.memories.none { it.id == "m1" })
        assertEquals("Memory deleted successfully", state.successMessage)
    }

    @Test
    fun editMemory_flowUpdatesMemorySuccessfully() = testScope.runTest {
        advanceUntilIdle()

        val target = viewModel.uiState.value.memories.find { it.id == "m2" }!!
        viewModel.startEditingMemory(target)

        assertEquals("Dad's number saved", viewModel.uiState.value.editingMemory?.title)

        // Save edit
        viewModel.saveMemoryEdit("m2", "Dad's new cell number saved", MemoryCategories.PEOPLE)
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertNull(state.editingMemory)
        assertEquals("Memory updated", state.successMessage)

        val updated = state.memories.find { it.id == "m2" }
        assertEquals("Dad's new cell number saved", updated?.title)
    }

    @Test
    fun editMemory_validationFailsOnBlankTitle() = testScope.runTest {
        advanceUntilIdle()

        viewModel.saveMemoryEdit("m2", "   ", MemoryCategories.PEOPLE)
        assertEquals("Memory title cannot be empty", viewModel.uiState.value.errorMessage)
    }

    @Test
    fun addMemory_addsNewItemSuccessfully() = testScope.runTest {
        advanceUntilIdle()

        viewModel.addMemory("Loves dark roast coffee", MemoryCategories.PREFERENCES, MemoryItem.ICON_SUN)
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertEquals("Memory saved", state.successMessage)
        assertEquals(5, state.memories.size)
    }

    @Test
    fun explicitSharing_confirmsAndCreatesAuditTrail() = testScope.runTest {
        advanceUntilIdle()

        val memoryToShare = viewModel.uiState.value.memories.first()
        viewModel.initiateShareToProfile(memoryToShare, CompanionProfile.PROFILE_NOVA_ID)

        val statePending = viewModel.uiState.value
        assertNotNull(statePending.memoryPendingShare)
        assertEquals(memoryToShare.id, statePending.memoryPendingShare?.id)
        assertEquals(CompanionProfile.PROFILE_NOVA_ID, statePending.targetProfileIdForShare)

        // Confirm sharing
        viewModel.confirmShare()
        advanceUntilIdle()

        val stateConfirmed = viewModel.uiState.value
        assertNull(stateConfirmed.memoryPendingShare)
        assertFalse(stateConfirmed.isSharingInProgress)
        assertNotNull(stateConfirmed.lastShareAudit)
        assertEquals(memoryToShare.id, stateConfirmed.lastShareAudit?.memoryId)
        assertEquals(CompanionProfile.PROFILE_ASTER_ID, stateConfirmed.lastShareAudit?.sourceProfileId)
        assertEquals(CompanionProfile.PROFILE_NOVA_ID, stateConfirmed.lastShareAudit?.targetProfileId)
        assertTrue(stateConfirmed.successMessage?.contains("Explicitly shared") == true)
    }

    @Test
    fun explicitSharing_cancelResetsPendingState() = testScope.runTest {
        advanceUntilIdle()

        val memoryToShare = viewModel.uiState.value.memories.first()
        viewModel.initiateShareToProfile(memoryToShare, CompanionProfile.PROFILE_NOVA_ID)
        viewModel.cancelShare()

        assertNull(viewModel.uiState.value.memoryPendingShare)
    }
}
