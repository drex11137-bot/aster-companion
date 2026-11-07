package com.astercompanion.android.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.astercompanion.android.model.CompanionProfile
import com.astercompanion.android.repository.CompanionRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/**
 * UI State for Companion Studio screen.
 * Adheres strictly to UI reference screenshot (a98599e6-e707-4cb8-a85f-85293d19df71.png).
 */
data class CompanionStudioUiState(
    val activeProfileId: String = CompanionProfile.PROFILE_ASTER_ID,
    val name: String = "Aster",
    val avatarUrl: String = "",
    val selectedHairColor: String = CompanionProfile.HAIR_AUBURN,
    val selectedEyeColor: String = CompanionProfile.EYE_HAZEL,
    val selectedStyle: String = CompanionProfile.STYLE_NATURAL,
    val selectedVoice: String = CompanionProfile.VOICE_WARM,
    val availableHairColors: List<String> = CompanionProfile.ALL_HAIR_COLORS,
    val availableEyeColors: List<String> = CompanionProfile.ALL_EYE_COLORS,
    val availableStyles: List<String> = CompanionProfile.ALL_STYLES,
    val availableVoices: List<String> = CompanionProfile.ALL_VOICES,
    val isSaving: Boolean = false,
    val isSwitchingProfile: Boolean = false,
    val successMessage: String? = null,
    val errorMessage: String? = null
)

/**
 * ViewModel managing the Companion Studio customization & profile switching.
 * Adheres strictly to PRD v1.1 §8, §9:
 * - Profile switching ('Aster' vs 'Nova') with enforced active profile constraint.
 * - Customization of Hair color, Eye color, Style, and Voice chips.
 * - Companion name editing.
 * - Saving settings to local Room DB and Supabase.
 */
class CompanionStudioViewModel(
    private val repository: CompanionRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(CompanionStudioUiState())
    val uiState: StateFlow<CompanionStudioUiState> = _uiState.asStateFlow()

    init {
        observeActiveProfile()
    }

    private fun observeActiveProfile() {
        viewModelScope.launch {
            repository.getActiveProfile().collect { profile ->
                if (profile != null) {
                    _uiState.update { current ->
                        current.copy(
                            activeProfileId = profile.id,
                            name = profile.name,
                            avatarUrl = profile.avatarUrl,
                            selectedHairColor = profile.hairColor,
                            selectedEyeColor = profile.eyeColor,
                            selectedStyle = profile.style,
                            selectedVoice = profile.voice
                        )
                    }
                }
            }
        }
    }

    /**
     * Switches between Profile A ("Aster") and Profile B ("Nova").
     * Enforces active profile constraint (only 1 profile active on this device at a time).
     */
    fun switchProfile(targetProfileId: String) {
        if (targetProfileId == _uiState.value.activeProfileId) return

        _uiState.update { it.copy(isSwitchingProfile = true, errorMessage = null) }

        viewModelScope.launch {
            val result = repository.switchProfile(targetProfileId)
            if (result.isSuccess) {
                val newProfile = result.getOrThrow()
                _uiState.update {
                    it.copy(
                        isSwitchingProfile = false,
                        activeProfileId = newProfile.id,
                        name = newProfile.name,
                        avatarUrl = newProfile.avatarUrl,
                        selectedHairColor = newProfile.hairColor,
                        selectedEyeColor = newProfile.eyeColor,
                        selectedStyle = newProfile.style,
                        selectedVoice = newProfile.voice,
                        successMessage = "Switched to ${newProfile.name}"
                    )
                }
            } else {
                _uiState.update {
                    it.copy(
                        isSwitchingProfile = false,
                        errorMessage = result.exceptionOrNull()?.message ?: "Failed to switch profile"
                    )
                }
            }
        }
    }

    fun onNameChanged(newName: String) {
        _uiState.update { it.copy(name = newName) }
    }

    fun selectHairColor(color: String) {
        _uiState.update { it.copy(selectedHairColor = color) }
    }

    fun selectEyeColor(color: String) {
        _uiState.update { it.copy(selectedEyeColor = color) }
    }

    fun selectStyle(style: String) {
        _uiState.update { it.copy(selectedStyle = style) }
    }

    fun selectVoice(voice: String) {
        _uiState.update { it.copy(selectedVoice = voice) }
    }

    /**
     * Persists all companion settings and appearance attributes to Room DB and Supabase.
     */
    fun saveSettings() {
        val currentState = _uiState.value
        val cleanName = currentState.name.trim()
        if (cleanName.isEmpty()) {
            _uiState.update { it.copy(errorMessage = "Companion name cannot be empty") }
            return
        }

        _uiState.update { it.copy(isSaving = true, errorMessage = null) }

        viewModelScope.launch {
            val settingsResult = repository.saveCompanionSettings(
                name = cleanName,
                avatar = currentState.avatarUrl,
                voice = currentState.selectedVoice,
                style = currentState.selectedStyle
            )
            val appearanceResult = repository.updateAppearance(
                hairColor = currentState.selectedHairColor,
                eyeColor = currentState.selectedEyeColor
            )

            if (settingsResult.isSuccess && appearanceResult.isSuccess) {
                _uiState.update {
                    it.copy(
                        isSaving = false,
                        successMessage = "Companion settings saved successfully"
                    )
                }
            } else {
                val error = settingsResult.exceptionOrNull() ?: appearanceResult.exceptionOrNull()
                _uiState.update {
                    it.copy(
                        isSaving = false,
                        errorMessage = error?.message ?: "Failed to save settings"
                    )
                }
            }
        }
    }

    fun clearMessages() {
        _uiState.update { it.copy(errorMessage = null, successMessage = null) }
    }
}
