package com.astercompanion.android.ui.screens.awareness

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.astercompanion.android.model.AwarenessState
import com.astercompanion.android.model.ScreenEvent
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

data class AwarenessUiState(
    val activeProfileName: String = "Aster",
    val activeProfileId: String = "profile_aster",
    val isCaptureActive: Boolean = true,
    val isPaused: Boolean = false,
    val isStopped: Boolean = false,
    val isMuted: Boolean = false,
    val captureFps: Float = 60.0f,
    val uploadFps: Float = 30.0f,
    val analysisFps: Float = 5.0f,
    val totalFramesCaptured: Long = 18420L,
    val totalGapsDetected: Int = 0,
    val monotonicSequenceNumber: Long = 18420L,
    val recentEvents: List<ScreenEvent> = initialRecentEvents(),
    val feedbackToast: String? = null
)

fun initialRecentEvents(): List<ScreenEvent> = listOf(
    ScreenEvent(
        id = "evt_1",
        profileId = "profile_aster",
        timestamp = System.currentTimeMillis() - 2000,
        sequenceNumber = 18419,
        eventType = ScreenEvent.EVENT_TYPE_SCENE_CHANGE,
        summary = "User switched from Settings to Calendar",
        captureFps = 60.0f,
        uploadFps = 30.0f,
        analysisFps = 5.0f
    ),
    ScreenEvent(
        id = "evt_2",
        profileId = "profile_aster",
        timestamp = System.currentTimeMillis() - 12000,
        sequenceNumber = 18418,
        eventType = ScreenEvent.EVENT_TYPE_TEXT_DETECTED,
        summary = "Detected Saturday schedule notes on screen",
        captureFps = 60.0f,
        uploadFps = 30.0f,
        analysisFps = 5.0f
    ),
    ScreenEvent(
        id = "evt_3",
        profileId = "profile_aster",
        timestamp = System.currentTimeMillis() - 45000,
        sequenceNumber = 18417,
        eventType = ScreenEvent.EVENT_TYPE_PERIODIC_SAMPLE,
        summary = "Ambient baseline scene verification",
        captureFps = 60.0f,
        uploadFps = 30.0f,
        analysisFps = 5.0f
    )
)

class AwarenessViewModel : ViewModel() {

    private val _uiState = MutableStateFlow(AwarenessUiState())
    val uiState: StateFlow<AwarenessUiState> = _uiState.asStateFlow()

    private var telemetryJob: Job? = null

    init {
        startTelemetryLoop()
    }

    private fun startTelemetryLoop() {
        telemetryJob?.cancel()
        telemetryJob = viewModelScope.launch {
            while (isActive) {
                delay(1000)
                _uiState.update { current ->
                    if (current.isPaused || current.isStopped) {
                        current
                    } else {
                        val jitter = ((-5..5).random()) * 0.1f
                        current.copy(
                            captureFps = (60.0f + jitter).coerceIn(58f, 62f),
                            uploadFps = (30.0f + jitter * 0.5f).coerceIn(28f, 31f),
                            analysisFps = (5.0f + jitter * 0.1f).coerceIn(4.8f, 5.2f),
                            totalFramesCaptured = current.totalFramesCaptured + 60,
                            monotonicSequenceNumber = current.monotonicSequenceNumber + 60
                        )
                    }
                }
            }
        }
    }

    fun togglePause() {
        _uiState.update { current ->
            val nextPaused = !current.isPaused
            current.copy(
                isPaused = nextPaused,
                feedbackToast = if (nextPaused) "Awareness capture paused" else "Awareness capture resumed"
            )
        }
    }

    fun toggleStop() {
        _uiState.update { current ->
            val nextStopped = !current.isStopped
            current.copy(
                isStopped = nextStopped,
                isCaptureActive = !nextStopped,
                feedbackToast = if (nextStopped) "Awareness capture stopped" else "Awareness capture started"
            )
        }
    }

    fun toggleMute() {
        _uiState.update { current ->
            val nextMuted = !current.isMuted
            current.copy(
                isMuted = nextMuted,
                feedbackToast = if (nextMuted) "Microphone muted" else "Microphone unmuted"
            )
        }
    }

    fun dismissFeedback() {
        _uiState.update { it.copy(feedbackToast = null) }
    }
}
