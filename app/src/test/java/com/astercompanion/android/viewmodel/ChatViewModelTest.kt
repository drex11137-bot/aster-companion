package com.astercompanion.android.viewmodel

import com.astercompanion.android.MainDispatcherRule
import com.astercompanion.android.data.local.ChatMessageEntity
import com.astercompanion.android.data.local.ProfileEntity
import com.astercompanion.android.data.remote.DefaultSupabaseApi
import com.astercompanion.android.model.Attachment
import com.astercompanion.android.model.AttachmentType
import com.astercompanion.android.model.AudioRecordingState
import com.astercompanion.android.model.ChatMessage
import com.astercompanion.android.model.CompanionProfile
import com.astercompanion.android.model.MessageSender
import com.astercompanion.android.model.ScheduleCard
import com.astercompanion.android.model.SuggestionPill
import com.astercompanion.android.repository.CompanionRepository
import com.astercompanion.android.testutil.FakeChatDao
import com.astercompanion.android.testutil.FakeMemoryDao
import com.astercompanion.android.testutil.FakeProfileDao
import com.astercompanion.android.testutil.FakeScreenEventDao
import com.astercompanion.android.testutil.FakeTodayDao
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.advanceTimeBy
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
class ChatViewModelTest {

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
    private lateinit var viewModel: ChatViewModel

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

        // Seed initial chat message matching screenshot 79ffed4b
        chatDao.insertMessage(
            ChatMessageEntity(
                id = "msg_seed_1",
                profileId = CompanionProfile.PROFILE_ASTER_ID,
                sender = MessageSender.COMPANION.name,
                text = "Sure. You mentioned wanting a slow morning, so I kept it light.",
                timestampLabel = "8:21 PM",
                isStreaming = false,
                isDelivered = true,
                hasScheduleCard = true,
                citationsSummary = "Used 2 memories",
                createdAt = 1000L
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

        viewModel = ChatViewModel(repository)
    }

    @Test
    fun initialState_loadsMessagesAndDefaultPills() = testScope.runTest {
        advanceUntilIdle()

        val state = viewModel.uiState.value
        assertEquals("Aster", state.companionName)
        assertTrue(state.isCompanionOnline)
        assertEquals(1, state.messages.size)

        val firstMessage = state.messages.first()
        assertEquals("Sure. You mentioned wanting a slow morning, so I kept it light.", firstMessage.text)
        assertNotNull(firstMessage.scheduleCard)
        assertEquals("Saturday, Nov 15", firstMessage.scheduleCard?.dateTitle)
        assertEquals(5, firstMessage.scheduleCard?.items?.size)
        assertEquals("Used 2 memories", firstMessage.citations.firstOrNull()?.text)

        // Suggestion pills
        assertEquals(2, state.suggestionPills.size)
        assertEquals("Add reminder", state.suggestionPills[0].label)
        assertEquals("Summarize", state.suggestionPills[1].label)
    }

    @Test
    fun onInputTextChanged_updatesState() {
        viewModel.onInputTextChanged("Hello Aster")
        assertEquals("Hello Aster", viewModel.uiState.value.inputText)
    }

    @Test
    fun sendMessage_clearsInputAndTriggersStreaming() = testScope.runTest {
        advanceUntilIdle()

        viewModel.onInputTextChanged("Can you plan my Saturday?")
        viewModel.sendMessage()

        // Input text should be cleared immediately
        assertEquals("", viewModel.uiState.value.inputText)

        advanceUntilIdle()
        assertFalse(viewModel.uiState.value.isStreaming)
    }

    @Test
    fun toggleScheduleItemCompletion_updatesItemInState() = testScope.runTest {
        advanceUntilIdle()

        val message = viewModel.uiState.value.messages.first()
        val card = message.scheduleCard!!
        val firstItemId = card.items.first().id

        assertFalse(card.items.first().isCompleted)

        viewModel.toggleScheduleItemCompletion(card.id, firstItemId)

        val updatedMessage = viewModel.uiState.value.messages.first()
        val updatedCard = updatedMessage.scheduleCard!!
        assertTrue(updatedCard.items.first().isCompleted)
    }

    @Test
    fun toggleScheduleItemExpanded_updatesExpansionState() = testScope.runTest {
        advanceUntilIdle()

        val message = viewModel.uiState.value.messages.first()
        val card = message.scheduleCard!!
        val firstItemId = card.items.first().id

        assertFalse(card.items.first().isExpanded)

        viewModel.toggleScheduleItemExpanded(card.id, firstItemId)

        val updatedMessage = viewModel.uiState.value.messages.first()
        val updatedCard = updatedMessage.scheduleCard!!
        assertTrue(updatedCard.items.first().isExpanded)
    }

    @Test
    fun toggleCitationExpanded_updatesCitationState() = testScope.runTest {
        advanceUntilIdle()

        val message = viewModel.uiState.value.messages.first()
        val citation = message.citations.first()

        assertFalse(citation.isExpanded)

        viewModel.toggleCitationExpanded(message.id, citation.id)

        val updatedMessage = viewModel.uiState.value.messages.first()
        val updatedCitation = updatedMessage.citations.first()
        assertTrue(updatedCitation.isExpanded)
    }

    @Test
    fun onSuggestionPillSelected_addReminder_prefillsInput() {
        val reminderPill = SuggestionPill("p1", "Add reminder", "reminder")
        viewModel.onSuggestionPillSelected(reminderPill)

        assertEquals("Remind me to ", viewModel.uiState.value.inputText)
    }

    @Test
    fun onSuggestionPillSelected_summarize_triggersMessage() = testScope.runTest {
        advanceUntilIdle()

        val summarizePill = SuggestionPill("p2", "Summarize", "summarize")
        viewModel.onSuggestionPillSelected(summarizePill)

        advanceUntilIdle()
        assertFalse(viewModel.uiState.value.isStreaming)
    }

    @Test
    fun audioRecording_transitionsThroughLifecycle() = testScope.runTest {
        assertEquals(AudioRecordingState.IDLE, viewModel.uiState.value.audioRecordingState)

        // Start
        viewModel.startAudioRecording()
        assertEquals(AudioRecordingState.RECORDING, viewModel.uiState.value.audioRecordingState)

        // Stop
        viewModel.stopAudioRecording()
        assertEquals(AudioRecordingState.PROCESSING, viewModel.uiState.value.audioRecordingState)

        advanceUntilIdle()
        assertEquals(AudioRecordingState.IDLE, viewModel.uiState.value.audioRecordingState)
    }

    @Test
    fun cancelAudioRecording_resetsToIdle() {
        viewModel.startAudioRecording()
        assertEquals(AudioRecordingState.RECORDING, viewModel.uiState.value.audioRecordingState)

        viewModel.cancelAudioRecording()
        assertEquals(AudioRecordingState.IDLE, viewModel.uiState.value.audioRecordingState)
    }

    @Test
    fun attachments_addAndRemove() {
        val attachment = Attachment(
            id = "att_1",
            type = AttachmentType.IMAGE,
            name = "receipt.png",
            uri = "content://media/1",
            sizeBytes = 1024L
        )

        viewModel.addAttachment(attachment)
        assertEquals(1, viewModel.uiState.value.attachments.size)

        viewModel.removeAttachment("att_1")
        assertEquals(0, viewModel.uiState.value.attachments.size)
    }
}
