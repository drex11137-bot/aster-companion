package com.astercompanion.android.ui

import com.astercompanion.android.model.MemoryCategories
import com.astercompanion.android.ui.screens.memory.MemoriesViewModel
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class MemoriesViewModelTest {

    private lateinit var viewModel: MemoriesViewModel

    @Before
    fun setUp() {
        viewModel = MemoriesViewModel()
    }

    @Test
    fun testInitialMemoriesMatchScreenshot() {
        val state = viewModel.uiState.value
        assertEquals(4, state.memories.size)
        assertEquals(MemoryCategories.ALL, state.selectedCategory)

        assertEquals("Prefers short answers\nin the morning", state.memories[0].title)
        assertEquals("Dad's number saved", state.memories[1].title)
        assertEquals("Allergic to peanuts", state.memories[2].title)
        assertEquals("Running a half marathon\nin March", state.memories[3].title)
    }

    @Test
    fun testCategoryFilterSelection() {
        viewModel.onCategorySelected(MemoryCategories.PEOPLE)
        assertEquals(MemoryCategories.PEOPLE, viewModel.uiState.value.selectedCategory)

        viewModel.onCategorySelected(MemoryCategories.PLANS)
        assertEquals(MemoryCategories.PLANS, viewModel.uiState.value.selectedCategory)
    }

    @Test
    fun testSearchQueryChange() {
        viewModel.onSearchQueryChanged("peanuts")
        assertEquals("peanuts", viewModel.uiState.value.searchQuery)
    }

    @Test
    fun testEditMemoryFlow() {
        val target = viewModel.uiState.value.memories[0]
        viewModel.onStartEdit(target)
        assertEquals(target, viewModel.uiState.value.memoryToEdit)

        viewModel.onSaveEdit(target.id, "Prefers short answers and quiet mornings", MemoryCategories.PREFERENCES)
        assertNull(viewModel.uiState.value.memoryToEdit)
        val updated = viewModel.uiState.value.memories.first { it.id == target.id }
        assertEquals("Prefers short answers and quiet mornings", updated.title)
    }

    @Test
    fun testDeleteMemoryFlow() {
        val target = viewModel.uiState.value.memories[1]
        viewModel.onStartDelete(target)
        assertEquals(target, viewModel.uiState.value.memoryToDelete)

        viewModel.onConfirmDelete()
        assertNull(viewModel.uiState.value.memoryToDelete)
        assertEquals(3, viewModel.uiState.value.memories.size)
        assertFalse(viewModel.uiState.value.memories.any { it.id == target.id })
    }

    @Test
    fun testExplicitSharingFlow() {
        val target = viewModel.uiState.value.memories[2]
        viewModel.onStartShare(target)
        assertEquals(target, viewModel.uiState.value.memoryToShare)

        viewModel.onConfirmShare(target.id, "Nova")
        assertNull(viewModel.uiState.value.memoryToShare)
        val sharedMemory = viewModel.uiState.value.memories.first { it.id == target.id }
        assertTrue(sharedMemory.isSharedWithOtherProfile)
        assertEquals("profile_nova", sharedMemory.sharedToProfileId)
        assertNotNull(sharedMemory.sharedAt)
    }
}
