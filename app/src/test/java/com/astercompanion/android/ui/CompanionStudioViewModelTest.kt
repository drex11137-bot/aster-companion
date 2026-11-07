package com.astercompanion.android.ui

import com.astercompanion.android.model.CompanionProfile
import com.astercompanion.android.ui.screens.companion.CompanionStudioViewModel
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class CompanionStudioViewModelTest {

    private lateinit var viewModel: CompanionStudioViewModel

    @Before
    fun setUp() {
        viewModel = CompanionStudioViewModel()
    }

    @Test
    fun testInitialProfileIsAster() {
        val state = viewModel.uiState.value
        assertEquals(CompanionProfile.PROFILE_ASTER_ID, state.selectedProfileId)
        assertEquals("Aster", state.currentProfile.name)
        assertEquals(CompanionProfile.HAIR_AUBURN, state.currentProfile.hairColor)
        assertEquals(CompanionProfile.EYE_HAZEL, state.currentProfile.eyeColor)
        assertEquals(CompanionProfile.STYLE_NATURAL, state.currentProfile.style)
        assertEquals(CompanionProfile.VOICE_WARM, state.currentProfile.voice)
    }

    @Test
    fun testProfileSwitchingToNova() {
        viewModel.selectProfile(CompanionProfile.PROFILE_NOVA_ID)
        val state = viewModel.uiState.value
        assertEquals(CompanionProfile.PROFILE_NOVA_ID, state.selectedProfileId)
        assertEquals("Nova", state.currentProfile.name)
    }

    @Test
    fun testCustomizingAppearanceOptions() {
        viewModel.selectHairColor(CompanionProfile.HAIR_BLACK)
        assertEquals(CompanionProfile.HAIR_BLACK, viewModel.uiState.value.currentProfile.hairColor)

        viewModel.selectEyeColor(CompanionProfile.EYE_BLUE)
        assertEquals(CompanionProfile.EYE_BLUE, viewModel.uiState.value.currentProfile.eyeColor)

        viewModel.selectStyle(CompanionProfile.STYLE_CREATIVE)
        assertEquals(CompanionProfile.STYLE_CREATIVE, viewModel.uiState.value.currentProfile.style)

        viewModel.selectVoice(CompanionProfile.VOICE_CALM)
        assertEquals(CompanionProfile.VOICE_CALM, viewModel.uiState.value.currentProfile.voice)
    }

    @Test
    fun testRenamingCompanionFlow() {
        viewModel.onStartEditName()
        assertTrue(viewModel.uiState.value.isEditingName)

        viewModel.onNameChange("Astra")
        assertEquals("Astra", viewModel.uiState.value.editedName)

        viewModel.onConfirmNameEdit()
        assertFalse(viewModel.uiState.value.isEditingName)
        assertEquals("Astra", viewModel.uiState.value.currentProfile.name)
    }

    @Test
    fun testSaveCompanionEmitsFeedback() {
        viewModel.saveCompanion()
        assertNotNull(viewModel.uiState.value.saveFeedbackMessage)
        assertTrue(viewModel.uiState.value.saveFeedbackMessage!!.contains("saved to device"))

        viewModel.dismissFeedback()
        assertNull(viewModel.uiState.value.saveFeedbackMessage)
    }
}
