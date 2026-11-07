package com.astercompanion.android.ui.screens.chat

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.astercompanion.android.model.ChatMessage
import com.astercompanion.android.model.MessageSender
import com.astercompanion.android.model.ScheduleCard
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class ChatUiState(
    val companionName: String = "Aster",
    val isOnline: Boolean = true,
    val inputText: String = "",
    val isStreaming: Boolean = false,
    val messages: List<ChatMessage> = initialChatMessages(),
    val quickActions: List<String> = listOf("Add reminder", "Summarize", "Plan tomorrow"),
    val activeCitationDialog: List<String>? = null
)

fun initialChatMessages(): List<ChatMessage> {
    return listOf(
        ChatMessage(
            id = "msg_user_1",
            profileId = "profile_aster",
            sender = MessageSender.USER,
            content = "Can you plan my Saturday?",
            text = "Can you plan my Saturday?",
            timestamp = 1731702000000L, // 8:20 PM
            deliveryStatus = "read"
        ),
        ChatMessage(
            id = "msg_aster_1",
            profileId = "profile_aster",
            sender = MessageSender.COMPANION,
            content = "Sure. You mentioned wanting a slow morning, so I kept it light.",
            text = "Sure. You mentioned wanting a slow morning, so I kept it light.",
            timestamp = 1731702060000L, // 8:21 PM
            scheduleCard = ScheduleCard(
                id = "sat_schedule_1",
                dateTitle = "Saturday, Nov 15",
                subtitle = "A calm and balanced day"
            ),
            memoryCitations = listOf(
                "You prefer short answers and slow mornings on weekends",
                "Personal reading and yoga are your typical wind-down activities"
            )
        )
    )
}

class ChatViewModel : ViewModel() {

    private val _uiState = MutableStateFlow(ChatUiState())
    val uiState: StateFlow<ChatUiState> = _uiState.asStateFlow()

    private var streamingJob: Job? = null

    fun onInputTextChanged(newText: String) {
        _uiState.update { it.copy(inputText = newText) }
    }

    fun sendMessage() {
        val text = _uiState.value.inputText.trim()
        if (text.isEmpty()) return

        val userMessage = ChatMessage(
            id = "msg_user_${System.currentTimeMillis()}",
            profileId = "profile_aster",
            sender = MessageSender.USER,
            content = text,
            text = text,
            timestamp = System.currentTimeMillis(),
            deliveryStatus = "sent"
        )

        _uiState.update { current ->
            current.copy(
                inputText = "",
                messages = current.messages + userMessage,
                isStreaming = true
            )
        }

        // Simulate streaming response from Aster
        simulateStreamingCompanionResponse(text)
    }

    private fun simulateStreamingCompanionResponse(userPrompt: String) {
        streamingJob?.cancel()
        streamingJob = viewModelScope.launch {
            delay(400)

            val companionMsgId = "msg_aster_${System.currentTimeMillis()}"
            val responseText = when {
                userPrompt.contains("reminder", ignoreCase = true) ->
                    "I've noted that reminder for you. I'll make sure to alert you at the right moment."
                userPrompt.contains("summarize", ignoreCase = true) ->
                    "Here is a summary of your day: 3 tasks pending, reminder scheduled for 7:30 PM, and 4 active memories preserved on-device."
                else ->
                    "I'm here with you. I've considered your preferences and kept everything in harmony with your schedule."
            }

            val words = responseText.split(" ")
            var streamedText = ""

            val placeholder = ChatMessage(
                id = companionMsgId,
                profileId = "profile_aster",
                sender = MessageSender.COMPANION,
                content = "",
                text = "",
                timestamp = System.currentTimeMillis()
            )

            _uiState.update { it.copy(messages = it.messages + placeholder) }

            for (word in words) {
                delay(60)
                streamedText = if (streamedText.isEmpty()) word else "$streamedText $word"
                _uiState.update { current ->
                    current.copy(
                        messages = current.messages.map { msg ->
                            if (msg.id == companionMsgId) msg.copy(content = streamedText, text = streamedText) else msg
                        }
                    )
                }
            }

            _uiState.update { it.copy(isStreaming = false) }
        }
    }

    fun onQuickActionClick(action: String) {
        when (action) {
            "Add reminder" -> {
                _uiState.update { it.copy(inputText = "Remind me to call Mom tomorrow morning") }
            }
            "Summarize" -> {
                _uiState.update { it.copy(inputText = "Can you summarize my tasks and schedule?") }
            }
            "Plan tomorrow" -> {
                _uiState.update { it.copy(inputText = "Plan a productive morning tomorrow") }
            }
        }
    }

    fun onCitationClick(citations: List<String>) {
        _uiState.update { it.copy(activeCitationDialog = citations) }
    }

    fun dismissCitationDialog() {
        _uiState.update { it.copy(activeCitationDialog = null) }
    }
}
