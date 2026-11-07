package com.astercompanion.android.ui.screens.companion

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.astercompanion.android.model.CompanionProfile
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class CompanionStudioUiState(
    val selectedProfileId: String = CompanionProfile.PROFILE_ASTER_ID,
    val asterProfile: CompanionProfile = CompanionProfile.defaultAster(),
    val novaProfile: CompanionProfile = CompanionProfile.defaultNova(),
    val isEditingName: Boolean = false,
    val editedName: String = "Aster",
    val saveFeedbackMessage: String? = null
) {
    val currentProfile: CompanionProfile
        get() = if (selectedProfileId == CompanionProfile.PROFILE_ASTER_ID) asterProfile else novaProfile
}

class CompanionStudioViewModel : ViewModel() {

    private val _uiState = MutableStateFlow(CompanionStudioUiState())
    val uiState: StateFlow<CompanionStudioUiState> = _uiState.asStateFlow()

    fun selectProfile(profileId: String) {
        _uiState.update { current ->
            val profile = if (profileId == CompanionProfile.PROFILE_ASTER_ID) current.asterProfile else current.novaProfile
            current.copy(
                selectedProfileId = profileId,
                editedName = profile.name
            )
        }
    }

    fun onStartEditName() {
        _uiState.update { it.copy(isEditingName = true, editedName = it.currentProfile.name) }
    }

    fun onNameChange(newName: String) {
        _uiState.update { it.copy(editedName = newName) }
    }

    fun onConfirmNameEdit() {
        _uiState.update { current ->
            val updated = current.currentProfile.copy(name = current.editedName)
            if (current.selectedProfileId == CompanionProfile.PROFILE_ASTER_ID) {
                current.copy(asterProfile = updated, isEditingName = false)
            } else {
                current.copy(novaProfile = updated, isEditingName = false)
            }
        }
    }

    fun onDismissNameEdit() {
        _uiState.update { it.copy(isEditingName = false) }
    }

    fun selectHairColor(colorName: String) {
        _uiState.update { current ->
            val updated = current.currentProfile.copy(hairColor = colorName)
            if (current.selectedProfileId == CompanionProfile.PROFILE_ASTER_ID) {
                current.copy(asterProfile = updated)
            } else {
                current.copy(novaProfile = updated)
            }
        }
    }

    fun selectEyeColor(colorName: String) {
        _uiState.update { current ->
            val updated = current.currentProfile.copy(eyeColor = colorName)
            if (current.selectedProfileId == CompanionProfile.PROFILE_ASTER_ID) {
                current.copy(asterProfile = updated)
            } else {
                current.copy(novaProfile = updated)
            }
        }
    }

    fun selectStyle(styleName: String) {
        _uiState.update { current ->
            val updated = current.currentProfile.copy(style = styleName)
            if (current.selectedProfileId == CompanionProfile.PROFILE_ASTER_ID) {
                current.copy(asterProfile = updated)
            } else {
                current.copy(novaProfile = updated)
            }
        }
    }

    fun selectVoice(voiceName: String) {
        _uiState.update { current ->
            val updated = current.currentProfile.copy(voice = voiceName)
            if (current.selectedProfileId == CompanionProfile.PROFILE_ASTER_ID) {
                current.copy(asterProfile = updated)
            } else {
                current.copy(novaProfile = updated)
            }
        }
    }

    fun saveCompanion() {
        _uiState.update { current ->
            current.copy(
                saveFeedbackMessage = "${current.currentProfile.name} customized and saved to device."
            )
        }
    }

    fun dismissFeedback() {
        _uiState.update { it.copy(saveFeedbackMessage = null) }
    }
}
