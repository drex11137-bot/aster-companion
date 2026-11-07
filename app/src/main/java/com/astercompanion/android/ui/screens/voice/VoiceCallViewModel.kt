package com.astercompanion.android.ui.screens.voice

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

enum class CallSpeakerState {
    LISTENING,
    COMPANION_SPEAKING,
    BARGE_IN_DETECTED
}

data class VoiceCallUiState(
    val companionName: String = "Aster",
    val callDurationSeconds: Long = 0L,
    val speakerState: CallSpeakerState = CallSpeakerState.COMPANION_SPEAKING,
    val liveTranscript: String = "I’ve set your Saturday schedule with a slow morning and light afternoon workout.",
    val userSpeechBuffer: String = "",
    val isMicMuted: Boolean = false,
    val isSpeakerOn: Boolean = true,
    val audioAmplitude: Float = 0.65f,
    val isCallActive: Boolean = true
)

class VoiceCallViewModel(
    autoStartLoops: Boolean = true
) : ViewModel() {

    private val _uiState = MutableStateFlow(VoiceCallUiState())
    val uiState: StateFlow<VoiceCallUiState> = _uiState.asStateFlow()

    private var timerJob: Job? = null
    private var visualizerJob: Job? = null

    init {
        if (autoStartLoops) {
            startCallTimer()
            startAudioVisualizerLoop()
        }
    }

    private fun startCallTimer() {
        timerJob?.cancel()
        timerJob = viewModelScope.launch {
            while (isActive && _uiState.value.isCallActive) {
                delay(1000)
                _uiState.update { it.copy(callDurationSeconds = it.callDurationSeconds + 1) }
            }
        }
    }

    private fun startAudioVisualizerLoop() {
        visualizerJob?.cancel()
        visualizerJob = viewModelScope.launch {
            while (isActive && _uiState.value.isCallActive) {
                delay(120)
                _uiState.update { current ->
                    if (current.isMicMuted) {
                        current.copy(audioAmplitude = 0.1f)
                    } else {
                        val amp = when (current.speakerState) {
                            CallSpeakerState.COMPANION_SPEAKING -> (0.5f..0.95f).random()
                            CallSpeakerState.LISTENING -> (0.2f..0.45f).random()
                            CallSpeakerState.BARGE_IN_DETECTED -> 0.85f
                        }
                        current.copy(audioAmplitude = amp)
                    }
                }
            }
        }
    }

    private fun ClosedFloatingPointRange<Float>.random(): Float {
        return start + Math.random().toFloat() * (endInclusive - start)
    }

    fun triggerBargeIn() {
        viewModelScope.launch {
            _uiState.update {
                it.copy(
                    speakerState = CallSpeakerState.BARGE_IN_DETECTED,
                    liveTranscript = "Aster paused (Barge-in detected)",
                    userSpeechBuffer = "Actually, can we move lunch to 1:30 PM?"
                )
            }
            delay(1500)
            _uiState.update {
                it.copy(
                    speakerState = CallSpeakerState.COMPANION_SPEAKING,
                    liveTranscript = "Got it! Moving lunch to 1:30 PM and shifting personal time slightly.",
                    userSpeechBuffer = ""
                )
            }
        }
    }

    fun toggleMute() {
        _uiState.update { it.copy(isMicMuted = !it.isMicMuted) }
    }

    fun toggleSpeaker() {
        _uiState.update { it.copy(isSpeakerOn = !it.isSpeakerOn) }
    }

    fun stopLoops() {
        timerJob?.cancel()
        visualizerJob?.cancel()
    }

    override fun onCleared() {
        super.onCleared()
        stopLoops()
    }

    fun endCall(onCallEnded: () -> Unit) {
        _uiState.update { it.copy(isCallActive = false) }
        stopLoops()
        onCallEnded()
    }
}
