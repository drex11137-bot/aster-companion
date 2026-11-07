package com.astercompanion.android.repository

import com.astercompanion.android.MainDispatcherRule
import com.astercompanion.android.data.local.MemoryEntity
import com.astercompanion.android.data.local.ProfileEntity
import com.astercompanion.android.data.local.ReminderEntity
import com.astercompanion.android.data.local.TaskEntity
import com.astercompanion.android.data.remote.DefaultSupabaseApi
import com.astercompanion.android.model.Attachment
import com.astercompanion.android.model.AttachmentType
import com.astercompanion.android.model.CompanionProfile
import com.astercompanion.android.model.MemoryCategories
import com.astercompanion.android.model.MemoryItem
import com.astercompanion.android.model.ScreenEvent
import com.astercompanion.android.testutil.FakeChatDao
import com.astercompanion.android.testutil.FakeMemoryDao
import com.astercompanion.android.testutil.FakeProfileDao
import com.astercompanion.android.testutil.FakeScreenEventDao
import com.astercompanion.android.testutil.FakeTodayDao
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.test.UnconfinedTestDispatcher
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
class CompanionRepositoryTest {

    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()

    private val testDispatcher = UnconfinedTestDispatcher()

    private lateinit var profileDao: FakeProfileDao
    private lateinit var todayDao: FakeTodayDao
    private lateinit var memoryDao: FakeMemoryDao
    private lateinit var chatDao: FakeChatDao
    private lateinit var screenEventDao: FakeScreenEventDao
    private lateinit var supabaseApi: DefaultSupabaseApi
    private lateinit var repository: CompanionRepository

    @Before
    fun setup() = runBlocking {
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

        // Seed Today reminder & tasks
        todayDao.insertReminder(
            ReminderEntity(
                id = "rem_1",
                profileId = CompanionProfile.PROFILE_ASTER_ID,
                title = "Call Dad at 7:30 PM",
                dayLabel = "Today",
                isSnoozed = false,
                snoozeUntil = null,
                createdAt = 1000L
            )
        )
        todayDao.insertTasks(
            listOf(
                TaskEntity("task_1", CompanionProfile.PROFILE_ASTER_ID, "Book dentist", "Today", false, null, 1000L),
                TaskEntity("task_2", CompanionProfile.PROFILE_ASTER_ID, "Finish budget draft", "Tomorrow", false, null, 2000L),
                TaskEntity("task_3", CompanionProfile.PROFILE_ASTER_ID, "Pick up parcel", "This week", false, null, 3000L)
            )
        )

        // Seed Memories
        memoryDao.insertMemories(
            listOf(
                MemoryEntity(id = "mem_1", profileId = CompanionProfile.PROFILE_ASTER_ID, title = "Prefers short answers in the morning", category = MemoryCategories.PREFERENCES, iconType = MemoryItem.ICON_SUN, addedAgoLabel = "Added 3 days ago", createdAt = 1000L, updatedAt = 1000L),
                MemoryEntity(id = "mem_2", profileId = CompanionProfile.PROFILE_ASTER_ID, title = "Dad's number saved", category = MemoryCategories.PEOPLE, iconType = MemoryItem.ICON_PERSON, addedAgoLabel = "Added 1 week ago", createdAt = 2000L, updatedAt = 2000L),
                MemoryEntity(id = "mem_3", profileId = CompanionProfile.PROFILE_ASTER_ID, title = "Allergic to peanuts", category = MemoryCategories.PREFERENCES, iconType = MemoryItem.ICON_PLUS, addedAgoLabel = "Added 2 weeks ago", createdAt = 3000L, updatedAt = 3000L),
                MemoryEntity(id = "mem_4", profileId = CompanionProfile.PROFILE_ASTER_ID, title = "Running a half marathon in March", category = MemoryCategories.PLANS, iconType = MemoryItem.ICON_RUN, addedAgoLabel = "Added 3 weeks ago", createdAt = 4000L, updatedAt = 4000L)
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
    }

    @Test
    fun getActiveProfile_returnsActiveAsterProfile() = runTest {
        val active = repository.getActiveProfile().first()
        assertNotNull(active)
        assertEquals(CompanionProfile.PROFILE_ASTER_ID, active?.id)
        assertEquals("Aster", active?.name)
        assertTrue(active?.isActiveOnDevice == true)
    }

    @Test
    fun switchProfile_enforcesSingleActiveProfileConstraint() = runTest {
        // Initially Aster is active
        val initial = repository.getActiveProfileOnce()
        assertEquals(CompanionProfile.PROFILE_ASTER_ID, initial?.id)

        // Switch to Nova
        val result = repository.switchProfile(CompanionProfile.PROFILE_NOVA_ID)
        assertTrue(result.isSuccess)

        // Verify Nova is active and Aster is inactive
        val nova = profileDao.getProfileById(CompanionProfile.PROFILE_NOVA_ID)
        val aster = profileDao.getProfileById(CompanionProfile.PROFILE_ASTER_ID)
        assertTrue(nova?.isActiveOnDevice == true)
        assertFalse(aster?.isActiveOnDevice == true)

        val activeNow = repository.getActiveProfile().first()
        assertEquals(CompanionProfile.PROFILE_NOVA_ID, activeNow?.id)
    }

    @Test
    fun getTodayData_returnsRemindersTasksAndRecentMemories() = runTest {
        val todayData = repository.getTodayData().first()
        assertEquals("Aster", todayData.companionName)
        assertEquals("Call Dad at 7:30 PM", todayData.nextReminder?.title)
        assertEquals(3, todayData.tasks.size)
        assertEquals("Book dentist", todayData.tasks[0].title)
        assertEquals(2, todayData.recentMemories.size)
    }

    @Test
    fun toggleTask_updatesTaskState() = runTest {
        val result = repository.toggleTask("task_1", true)
        assertTrue(result.isSuccess)

        val updatedToday = repository.getTodayData().first()
        val task1 = updatedToday.tasks.find { it.id == "task_1" }
        assertTrue(task1?.isCompleted == true)
    }

    @Test
    fun snoozeReminder_updatesReminderSnoozedState() = runTest {
        val result = repository.snoozeReminder("rem_1")
        assertTrue(result.isSuccess)

        val updatedToday = repository.getTodayData().first()
        assertTrue(updatedToday.nextReminder?.isSnoozed == true)
    }

    @Test
    fun getMemories_filtersByCategoryAndSearchQuery() = runTest {
        // Filter by Preferences
        val prefs = repository.getMemories(MemoryCategories.PREFERENCES, "").first()
        assertEquals(2, prefs.size)
        assertTrue(prefs.all { it.category == MemoryCategories.PREFERENCES })

        // Filter by People
        val people = repository.getMemories(MemoryCategories.PEOPLE, "").first()
        assertEquals(1, people.size)
        assertEquals("Dad's number saved", people[0].title)

        // Search query
        val searchMarathon = repository.getMemories(MemoryCategories.ALL, "marathon").first()
        assertEquals(1, searchMarathon.size)
        assertEquals("Running a half marathon in March", searchMarathon[0].title)
    }

    @Test
    fun addMemory_and_updateMemory_and_deleteMemory() = runTest {
        // Add
        val addResult = repository.addMemory("Loves dark roast coffee", MemoryCategories.PREFERENCES)
        assertTrue(addResult.isSuccess)
        val addedId = addResult.getOrThrow().id

        // Verify present
        val memoriesAfterAdd = repository.getMemories(MemoryCategories.PREFERENCES, "dark roast").first()
        assertEquals(1, memoriesAfterAdd.size)

        // Update
        val updateResult = repository.updateMemory(addedId, "Loves light roast coffee", MemoryCategories.PREFERENCES)
        assertTrue(updateResult.isSuccess)
        assertEquals("Loves light roast coffee", updateResult.getOrThrow().title)

        // Delete
        val deleteResult = repository.deleteMemory(addedId)
        assertTrue(deleteResult.isSuccess)

        val memoriesAfterDelete = repository.getMemories(MemoryCategories.PREFERENCES, "roast").first()
        assertTrue(memoriesAfterDelete.isEmpty())
    }

    @Test
    fun shareMemoryToProfile_createsAuditAndMaintainsIsolation() = runTest {
        val shareResult = repository.shareMemoryToProfile("mem_1", CompanionProfile.PROFILE_NOVA_ID)
        assertTrue(shareResult.isSuccess)

        val audit = shareResult.getOrThrow()
        assertEquals("mem_1", audit.memoryId)
        assertEquals(CompanionProfile.PROFILE_ASTER_ID, audit.sourceProfileId)
        assertEquals(CompanionProfile.PROFILE_NOVA_ID, audit.targetProfileId)
        assertTrue(audit.confirmedByUser)

        // Verify copy exists in Nova's isolated pool
        val novaMemories = memoryDao.getMemories(CompanionProfile.PROFILE_NOVA_ID, "All", "").first()
        assertEquals(1, novaMemories.size)
        assertEquals("Prefers short answers in the morning", novaMemories[0].title)
        assertTrue(novaMemories[0].isSharedWithOtherProfile)
    }

    @Test
    fun sendMessage_streamsResponseAndIntegratesScheduleCard() = runTest {
        val chunks = repository.sendMessage("Can you plan my Saturday?").toList()
        assertTrue(chunks.isNotEmpty())

        val finalChunk = chunks.last()
        assertTrue(finalChunk.isFinal)
        assertNotNull(finalChunk.scheduleCard)
        assertEquals("Saturday, Nov 15", finalChunk.scheduleCard?.dateTitle)
        assertEquals(5, finalChunk.scheduleCard?.items?.size)
        assertEquals("Used 2 memories", finalChunk.citations.firstOrNull()?.text)
    }

    @Test
    fun recordScreenEvent_validatesMonotonicSequence() = runTest {
        val event1 = ScreenEvent(
            id = "evt_1",
            profileId = CompanionProfile.PROFILE_ASTER_ID,
            timestamp = System.currentTimeMillis(),
            sequenceNumber = 1L,
            eventType = ScreenEvent.EVENT_TYPE_SCENE_CHANGE,
            summary = "App switch to Browser",
            captureFps = 120.0f,
            uploadFps = 30.0f,
            analysisFps = 5.0f,
            checksum = "abc123hash"
        )
        val result1 = repository.recordScreenEvent(event1)
        assertTrue(result1.isSuccess)

        // Insert event with lower sequence number: repository should automatically advance it
        val event2 = event1.copy(id = "evt_2", sequenceNumber = 1L)
        val result2 = repository.recordScreenEvent(event2)
        assertTrue(result2.isSuccess)

        val storedEvents = repository.getScreenEvents().first()
        assertEquals(2, storedEvents.size)
        assertTrue(storedEvents[1].sequenceNumber > storedEvents[0].sequenceNumber)
    }

    @Test
    fun saveCompanionSettings_and_updateAppearance() = runTest {
        val saveResult = repository.saveCompanionSettings(
            name = "Aster Pro",
            avatar = "avatar_aster_glow.png",
            voice = CompanionProfile.VOICE_CALM,
            style = CompanionProfile.STYLE_PROFESSIONAL
        )
        assertTrue(saveResult.isSuccess)
        assertEquals("Aster Pro", saveResult.getOrThrow().name)

        val appearResult = repository.updateAppearance(
            hairColor = CompanionProfile.HAIR_SILVER,
            eyeColor = CompanionProfile.EYE_BLUE
        )
        assertTrue(appearResult.isSuccess)

        val updatedProfile = repository.getActiveProfileOnce()
        assertEquals("Aster Pro", updatedProfile?.name)
        assertEquals(CompanionProfile.VOICE_CALM, updatedProfile?.voice)
        assertEquals(CompanionProfile.STYLE_PROFESSIONAL, updatedProfile?.style)
        assertEquals(CompanionProfile.HAIR_SILVER, updatedProfile?.hairColor)
        assertEquals(CompanionProfile.EYE_BLUE, updatedProfile?.eyeColor)
    }
}
