package com.astercompanion.android.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.astercompanion.android.model.Attachment
import com.astercompanion.android.model.AudioRecordingState
import com.astercompanion.android.model.ChatMessage
import com.astercompanion.android.model.CitationChip
import com.astercompanion.android.model.ScheduleCard
import com.astercompanion.android.model.ScheduleItem
import com.astercompanion.android.model.SuggestionPill
import com.astercompanion.android.repository.CompanionRepository
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/**
 * UI State for the Chat screen.
 * Adheres strictly to UI reference screenshot (79ffed4b-1317-46e6-98db-6eb6c96f60d6.png).
 */
data class ChatUiState(
    val messages: List<ChatMessage> = emptyList(),
    val isStreaming: Boolean = false,
    val inputText: String = "",
    val companionName: String = "Aster",
    val isCompanionOnline: Boolean = true,
    val audioRecordingState: AudioRecordingState = AudioRecordingState.IDLE,
    val recordingDurationSecs: Int = 0,
    val suggestionPills: List<SuggestionPill> = SuggestionPill.defaultPills(),
    val attachments: List<Attachment> = emptyList(),
    val errorMessage: String? = null
)

/**
 * ViewModel managing the multimodal streaming Chat experience in Aster Companion.
 * Adheres strictly to PRD v1.1 §7, §10:
 * - Streaming responses token-by-token.
 * - Interactive Saturday schedule card state (expand, complete items).
 * - Citation chips ("Used 2 memories").
 * - Audio recording state machine (IDLE, RECORDING, PROCESSING, ERROR).
 * - Suggestion pills ('Add reminder', 'Summarize').
 */
class ChatViewModel(
    private val repository: CompanionRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()

    private var streamingJob: Job? = null
    private var recordingTimerJob: Job? = null

    init {
        observeActiveProfile()
        observeChatMessages()
    }

    private fun observeActiveProfile() {
        viewModelScope.launch {
            repository.getActiveProfile().collect { profile ->
                if (profile != null) {
                    _uiState.update {
                        it.copy(
                            companionName = profile.name,
                            isCompanionOnline = profile.isOnline
                        )
                    }
                }
            }
        }
    }

    private fun observeChatMessages() {
        viewModelScope.launch {
            repository.getChatMessages()
                .catch { error ->
                    _uiState.update { it.copy(errorMessage = error.message) }
                }
                .collect { messageList ->
                    _uiState.update { current ->
                        // Preserve any active streaming state
                        current.copy(
                            messages = messageList,
                            isStreaming = messageList.any { it.isStreaming }
                        )
                    }
                }
        }
    }

    fun onInputTextChanged(text: String) {
        _uiState.update { it.copy(inputText = text) }
    }

    /**
     * Sends message with optional attachments and streams companion response chunk-by-chunk.
     */
    fun sendMessage(customText: String? = null) {
        val textToSend = (customText ?: _uiState.value.inputText).trim()
        if (textToSend.isEmpty() && _uiState.value.attachments.isEmpty()) return

        val currentAttachments = _uiState.value.attachments

        // Reset input immediately
        _uiState.update {
            it.copy(
                inputText = "",
                attachments = emptyList(),
                isStreaming = true,
                errorMessage = null
            )
        }

        streamingJob?.cancel()
        streamingJob = viewModelScope.launch {
            repository.sendMessage(textToSend, currentAttachments)
                .catch { error ->
                    _uiState.update {
                        it.copy(
                            isStreaming = false,
                            errorMessage = error.message ?: "Failed to receive response"
                        )
                    }
                }
                .collect { chunk ->
                    _uiState.update { current ->
                        current.copy(isStreaming = !chunk.isFinal)
                    }
                }
        }
    }

    /**
     * Interactively toggles a Saturday schedule item completion state.
     */
    fun toggleScheduleItemCompletion(scheduleCardId: String, itemId: String) {
        _uiState.update { state ->
            val updatedMessages = state.messages.map { msg ->
                val card = msg.scheduleCard
                if (card != null && (card.id == scheduleCardId || msg.id == scheduleCardId)) {
                    val updatedItems = card.items.map { item ->
                        if (item.id == itemId) item.copy(isCompleted = !item.isCompleted) else item
                    }
                    msg.copy(scheduleCard = card.copy(items = updatedItems))
                } else {
                    msg
                }
            }
            state.copy(messages = updatedMessages)
        }
    }

    /**
     * Expands or collapses a schedule item to show detailed activities.
     */
    fun toggleScheduleItemExpanded(scheduleCardId: String, itemId: String) {
        _uiState.update { state ->
            val updatedMessages = state.messages.map { msg ->
                val card = msg.scheduleCard
                if (card != null && (card.id == scheduleCardId || msg.id == scheduleCardId)) {
                    val updatedItems = card.items.map { item ->
                        if (item.id == itemId) item.copy(isExpanded = !item.isExpanded) else item
                    }
                    msg.copy(scheduleCard = card.copy(items = updatedItems))
                } else {
                    msg
                }
            }
            state.copy(messages = updatedMessages)
        }
    }

    /**
     * Expands or collapses a citation chip ("Used 2 memories").
     */
    fun toggleCitationExpanded(messageId: String, citationId: String) {
        _uiState.update { state ->
            val updatedMessages = state.messages.map { msg ->
                if (msg.id == messageId) {
                    val updatedCitations = msg.citations.map { cite ->
                        if (cite.id == citationId) cite.copy(isExpanded = !cite.isExpanded) else cite
                    }
                    msg.copy(citations = updatedCitations)
                } else {
                    msg
                }
            }
            state.copy(messages = updatedMessages)
        }
    }

    /**
     * Handles selection of a suggestion pill ('Add reminder', 'Summarize').
     */
    fun onSuggestionPillSelected(pill: SuggestionPill) {
        when (pill.label) {
            SuggestionPill.PILL_ADD_REMINDER -> {
                _uiState.update { it.copy(inputText = "Remind me to ") }
            }
            SuggestionPill.PILL_SUMMARIZE -> {
                sendMessage("Please summarize our recent conversation and plans.")
            }
            else -> {
                sendMessage(pill.label)
            }
        }
    }

    /**
     * Starts audio recording for voice interaction.
     */
    fun startAudioRecording() {
        if (_uiState.value.audioRecordingState != AudioRecordingState.IDLE) return

        _uiState.update {
            it.copy(
                audioRecordingState = AudioRecordingState.RECORDING,
                recordingDurationSecs = 0,
                errorMessage = null
            )
        }

        recordingTimerJob?.cancel()
        recordingTimerJob = viewModelScope.launch {
            while (_uiState.value.audioRecordingState == AudioRecordingState.RECORDING) {
                delay(1000L)
                _uiState.update { it.copy(recordingDurationSecs = it.recordingDurationSecs + 1) }
            }
        }
    }

    /**
     * Stops recording and simulates speech-to-text processing followed by sending transcribed text.
     */
    fun stopAudioRecording() {
        if (_uiState.value.audioRecordingState != AudioRecordingState.RECORDING) return
        recordingTimerJob?.cancel()

        _uiState.update { it.copy(audioRecordingState = AudioRecordingState.PROCESSING) }

        viewModelScope.launch {
            // Processing audio viseme/speech input
            delay(500L)
            _uiState.update {
                it.copy(
                    audioRecordingState = AudioRecordingState.IDLE,
                    recordingDurationSecs = 0
                )
            }
            // Trigger sample transcribed prompt
            sendMessage("Can you plan my Saturday?")
        }
    }

    /**
     * Cancels active audio recording.
     */
    fun cancelAudioRecording() {
        recordingTimerJob?.cancel()
        _uiState.update {
            it.copy(
                audioRecordingState = AudioRecordingState.IDLE,
                recordingDurationSecs = 0
            )
        }
    }

    fun addAttachment(attachment: Attachment) {
        _uiState.update {
            it.copy(attachments = it.attachments + attachment)
        }
    }

    fun removeAttachment(attachmentId: String) {
        _uiState.update {
            it.copy(attachments = it.attachments.filterNot { a -> a.id == attachmentId })
        }
    }

    fun clearChat() {
        viewModelScope.launch {
            repository.clearChat()
        }
    }

    fun clearError() {
        _uiState.update { it.copy(errorMessage = null) }
    }
}
