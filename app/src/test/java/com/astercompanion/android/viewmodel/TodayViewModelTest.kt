package com.astercompanion.android.viewmodel

import com.astercompanion.android.MainDispatcherRule
import com.astercompanion.android.data.local.MemoryEntity
import com.astercompanion.android.data.local.ProfileEntity
import com.astercompanion.android.data.local.ReminderEntity
import com.astercompanion.android.data.local.TaskEntity
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
class TodayViewModelTest {

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
    private lateinit var viewModel: TodayViewModel

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

        // Seed Reminder
        todayDao.insertReminder(
            ReminderEntity(
                id = "rem_today_1",
                profileId = CompanionProfile.PROFILE_ASTER_ID,
                title = "Call Dad at 7:30 PM",
                dayLabel = "Today",
                isSnoozed = false,
                snoozeUntil = null,
                createdAt = 1000L
            )
        )

        // Seed 3 tasks from screenshot 56539447
        todayDao.insertTasks(
            listOf(
                TaskEntity("t1", CompanionProfile.PROFILE_ASTER_ID, "Book dentist", "Today", false, null, 100L),
                TaskEntity("t2", CompanionProfile.PROFILE_ASTER_ID, "Finish budget draft", "Tomorrow", false, null, 200L),
                TaskEntity("t3", CompanionProfile.PROFILE_ASTER_ID, "Pick up parcel", "This week", false, null, 300L)
            )
        )

        // Seed memories
        memoryDao.insertMemories(
            listOf(
                MemoryEntity(id = "m1", profileId = CompanionProfile.PROFILE_ASTER_ID, title = "You love oat flat whites", category = MemoryCategories.PREFERENCES, iconType = MemoryItem.ICON_SUN, addedAgoLabel = "Noted 3 days ago", createdAt = 100L, updatedAt = 100L),
                MemoryEntity(id = "m2", profileId = CompanionProfile.PROFILE_ASTER_ID, title = "Sister's birthday: Nov 14", category = MemoryCategories.PEOPLE, iconType = MemoryItem.ICON_PERSON, addedAgoLabel = "Added last week", createdAt = 200L, updatedAt = 200L)
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

        viewModel = TodayViewModel(repository)
    }

    @Test
    fun initialState_loadsTodayDataSuccessfully() = testScope.runTest {
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertFalse(state.isLoading)
        assertNull(state.errorMessage)
        assertEquals("Aster", state.companionName)
        assertEquals("Good evening, Maya", state.greeting)
        assertEquals("A calmer, brighter you — one step at a time.", state.tagline)
        assertTrue(state.isCompanionOnline)

        // Next reminder
        assertNotNull(state.nextReminder)
        assertEquals("Call Dad at 7:30 PM", state.nextReminder?.title)
        assertEquals("Today", state.nextReminder?.dayLabel)
        assertFalse(state.nextReminder?.isSnoozed == true)

        // Tasks
        assertEquals(3, state.tasks.size)
        assertEquals("Book dentist", state.tasks[0].title)
        assertEquals("Finish budget draft", state.tasks[1].title)
        assertEquals("Pick up parcel", state.tasks[2].title)

        // Recent memories
        assertEquals(2, state.recentMemories.size)
        assertEquals("Sister's birthday: Nov 14", state.recentMemories[0].title)
        assertEquals("You love oat flat whites", state.recentMemories[1].title)
    }

    @Test
    fun toggleTask_optimisticallyUpdatesAndPersists() = testScope.runTest {
        advanceUntilIdle()

        // Toggle task 1 to completed
        viewModel.toggleTask("t1")
        advanceUntilIdle()

        val state = viewModel.uiState.value
        val task1 = state.tasks.find { it.id == "t1" }
        assertTrue(task1?.isCompleted == true)

        // Toggle back to incomplete
        viewModel.toggleTask("t1")
        advanceUntilIdle()

        val task1Reverted = viewModel.uiState.value.tasks.find { it.id == "t1" }
        assertFalse(task1Reverted?.isCompleted == true)
    }

    @Test
    fun snoozeReminder_setsSnoozedState() = testScope.runTest {
        advanceUntilIdle()

        viewModel.snoozeReminder("rem_today_1")
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertFalse(state.isSnoozing)
        assertTrue(state.nextReminder?.isSnoozed == true)
    }

    @Test
    fun refreshTodayData_triggersRemoteSync() = testScope.runTest {
        advanceUntilIdle()

        viewModel.refreshTodayData()
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertFalse(state.isLoading)
        assertNull(state.errorMessage)
        assertEquals("Aster", state.companionName)
    }
}
