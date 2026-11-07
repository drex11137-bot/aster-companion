package com.astercompanion.android.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.astercompanion.android.model.AwarenessState
import com.astercompanion.android.model.CompanionProfile
import com.astercompanion.android.model.ScreenEvent
import com.astercompanion.android.repository.CompanionRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.security.MessageDigest
import java.util.UUID

/**
 * UI State for Continuous Screen Awareness subsystem.
 * Adheres strictly to PRD v1.1 §5 & §13.
 */
data class AwarenessUiState(
    val activeProfileId: String = CompanionProfile.PROFILE_ASTER_ID,
    val isCaptureActive: Boolean = true,
    val isPaused: Boolean = false,
    val isStopped: Boolean = false,
    val isMuted: Boolean = false,
    val captureFps: Float = 120.0f,    // Screen acquisition rate (aspirational 120 FPS)
    val uploadFps: Float = 30.0f,      // Transport rate
    val analysisFps: Float = 5.0f,     // Backend perception/reasoning rate
    val targetCaptureFps: Float = 120.0f,
    val recentEvents: List<ScreenEvent> = emptyList(),
    val totalEventsRecorded: Long = 0L,
    val continuityGapsCount: Int = 0,
    val statusText: String = "Continuous Awareness Active",
    val errorMessage: String? = null
)

/**
 * ViewModel managing Continuous Screen Awareness for Aster Companion.
 * - Manages distinct Capture FPS, Upload FPS, and actual Analysis FPS rates (PRD §5.3).
 * - Fast, non-obstructive pause, stop, and mute controls (PRD §13.4).
 * - Monotonic event sequence integrity and gap tracking (PRD §12).
 */
class AwarenessViewModel(
    private val repository: CompanionRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(AwarenessUiState())
    val uiState: StateFlow<AwarenessUiState> = _uiState.asStateFlow()

    private var currentSequenceNumber: Long = 0L

    init {
        observeActiveProfile()
        observeScreenEvents()
    }

    private fun observeActiveProfile() {
        viewModelScope.launch {
            repository.getActiveProfile().collect { profile ->
                if (profile != null) {
                    _uiState.update { it.copy(activeProfileId = profile.id) }
                }
            }
        }
    }

    private fun observeScreenEvents() {
        viewModelScope.launch {
            repository.getScreenEvents()
                .catch { error ->
                    _uiState.update { it.copy(errorMessage = error.message) }
                }
                .collect { events ->
                    val lastSeq = events.lastOrNull()?.sequenceNumber ?: 0L
                    currentSequenceNumber = maxOf(currentSequenceNumber, lastSeq)
                    _uiState.update { current ->
                        current.copy(
                            recentEvents = events.takeLast(20).reversed(),
                            totalEventsRecorded = events.size.toLong()
                        )
                    }
                }
        }
    }

    /**
     * Updates capture rate (e.g., target 30, 60, or 120 FPS).
     */
    fun setCaptureFps(fps: Float) {
        val bounded = fps.coerceIn(1.0f, 120.0f)
        _uiState.update {
            it.copy(
                captureFps = bounded,
                targetCaptureFps = bounded
            )
        }
    }

    /**
     * Updates measured upload network FPS.
     */
    fun setUploadFps(fps: Float) {
        _uiState.update { it.copy(uploadFps = fps.coerceAtLeast(0.0f)) }
    }

    /**
     * Updates measured multimodal analysis reasoning FPS.
     * Note: Per PRD §5.3, analysis rate must never be conflated with capture rate.
     */
    fun setAnalysisFps(fps: Float) {
        _uiState.update { it.copy(analysisFps = fps.coerceAtLeast(0.0f)) }
    }

    /**
     * Quickly pauses screen capture and analysis.
     */
    fun pauseAwareness() {
        _uiState.update {
            it.copy(
                isPaused = true,
                statusText = "Awareness Paused"
            )
        }
    }

    /**
     * Resumes screen capture and analysis.
     */
    fun resumeAwareness() {
        _uiState.update {
            it.copy(
                isPaused = false,
                isStopped = false,
                statusText = "Continuous Awareness Active"
            )
        }
    }

    /**
     * Stops the awareness session completely.
     */
    fun stopAwareness() {
        _uiState.update {
            it.copy(
                isStopped = true,
                isPaused = false,
                isCaptureActive = false,
                statusText = "Awareness Stopped"
            )
        }
    }

    /**
     * Starts a new awareness session.
     */
    fun startAwareness() {
        _uiState.update {
            it.copy(
                isStopped = false,
                isPaused = false,
                isCaptureActive = true,
                statusText = "Continuous Awareness Active"
            )
        }
    }

    /**
     * Toggles microphone/environmental audio awareness mute state.
     */
    fun toggleMute() {
        _uiState.update {
            val newMuted = !it.isMuted
            it.copy(
                isMuted = newMuted,
                statusText = if (newMuted) "Audio Muted — Video Only" else "Audio & Video Active"
            )
        }
    }

    /**
     * Records a new screen awareness event with monotonic sequence and SHA-256 checksum.
     */
    fun recordEvent(eventType: String, summary: String) {
        if (_uiState.value.isPaused || _uiState.value.isStopped) return

        currentSequenceNumber++
        val timestamp = System.currentTimeMillis()
        val profileId = _uiState.value.activeProfileId
        val checksumPayload = "$profileId:$timestamp:$currentSequenceNumber:$summary"
        val checksum = sha256(checksumPayload)

        val event = ScreenEvent(
            id = "evt_${UUID.randomUUID().toString().take(8)}",
            profileId = profileId,
            timestamp = timestamp,
            sequenceNumber = currentSequenceNumber,
            eventType = eventType,
            summary = summary,
            captureFps = _uiState.value.captureFps,
            uploadFps = _uiState.value.uploadFps,
            analysisFps = _uiState.value.analysisFps,
            checksum = checksum
        )

        viewModelScope.launch {
            val result = repository.recordScreenEvent(event)
            if (result.isFailure) {
                _uiState.update {
                    it.copy(
                        continuityGapsCount = it.continuityGapsCount + 1,
                        errorMessage = "Gap detected in event stream"
                    )
                }
            }
        }
    }

    private fun sha256(input: String): String {
        val bytes = MessageDigest.getInstance("SHA-256").digest(input.toByteArray(Charsets.UTF_8))
        return bytes.joinToString("") { "%02x".format(it) }
    }

    fun clearError() {
        _uiState.update { it.copy(errorMessage = null) }
    }
}
