package com.astercompanion.android.ui.components

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Add
import androidx.compose.material.icons.outlined.BookmarkBorder
import androidx.compose.material.icons.outlined.DirectionsRun
import androidx.compose.material.icons.outlined.PersonOutline
import androidx.compose.material.icons.outlined.WbSunny
import androidx.compose.ui.graphics.Color
import com.astercompanion.android.model.CompanionProfile
import com.astercompanion.android.model.MemoryItem
import com.astercompanion.android.ui.theme.AsterColors
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Unit verification tests for Aster Companion UI Components and Design System Tokens.
 * Validates specifications matching the 4 reference PNG screenshots:
 * - 79ffed4b-1317-46e6-98db-6eb6c96f60d6.png (Chat & Schedule timeline)
 * - 56d6d982-5337-4170-80e5-1e156d239b38.png (Memories card list)
 * - 56539447-5086-44aa-b0ad-b98fa9cb6a8d.png (Today screen & tasks)
 * - a98599e6-e707-4cb8-a85f-85293d19df71.png (Companion studio & swatches)
 */
class AsterComponentsTest {

    @Test
    fun testScheduleTimelineMilestonesMatchScreenshot() {
        val milestones = DefaultScheduleTimeline.items
        assertEquals("Schedule timeline must contain exactly 5 milestones", 5, milestones.size)

        // Milestone 1: Coffee / Slow morning
        assertEquals("9:00 AM", milestones[0].time)
        assertEquals("Slow morning", milestones[0].title)
        assertEquals("Coffee, a good book, no rush", milestones[0].description)

        // Milestone 2: Dumbbell / Gentle workout
        assertEquals("11:30 AM", milestones[1].time)
        assertEquals("Gentle workout", milestones[1].title)
        assertEquals("Yoga or a walk outside", milestones[1].description)

        // Milestone 3: Fork/Knife / Lunch
        assertEquals("1:00 PM", milestones[2].time)
        assertEquals("Lunch", milestones[2].title)
        assertEquals("Something fresh and local", milestones[2].description)

        // Milestone 4: Book / Personal time
        assertEquals("3:00 PM", milestones[3].time)
        assertEquals("Personal time", milestones[3].title)
        assertEquals("Read, journal, or a creative project", milestones[3].description)

        // Milestone 5: Moon / Wind down
        assertEquals("7:00 PM", milestones[4].time)
        assertEquals("Wind down", milestones[4].title)
        assertEquals("A quiet evening", milestones[4].description)
    }

    @Test
    fun testMemoryIconResolver() {
        assertEquals(Icons.Outlined.WbSunny, resolveMemoryIcon(MemoryItem.ICON_SUN))
        assertEquals(Icons.Outlined.WbSunny, resolveMemoryIcon("morning"))
        assertEquals(Icons.Outlined.PersonOutline, resolveMemoryIcon(MemoryItem.ICON_PERSON))
        assertEquals(Icons.Outlined.PersonOutline, resolveMemoryIcon("contact"))
        assertEquals(Icons.Outlined.Add, resolveMemoryIcon(MemoryItem.ICON_PLUS))
        assertEquals(Icons.Outlined.Add, resolveMemoryIcon("medical"))
        assertEquals(Icons.Outlined.DirectionsRun, resolveMemoryIcon(MemoryItem.ICON_RUN))
        assertEquals(Icons.Outlined.DirectionsRun, resolveMemoryIcon("plans"))
        assertEquals(Icons.Outlined.BookmarkBorder, resolveMemoryIcon(MemoryItem.ICON_BOOKMARK))
        // Fallback default
        assertEquals(Icons.Outlined.WbSunny, resolveMemoryIcon("unknown_icon"))
    }

    @Test
    fun testHairSwatchesPalette() {
        val swatches = DefaultSwatches.HairSwatches
        assertEquals(5, swatches.size)

        val labels = swatches.map { it.label }
        assertTrue(labels.contains(CompanionProfile.HAIR_AUBURN))
        assertTrue(labels.contains(CompanionProfile.HAIR_BLACK))
        assertTrue(labels.contains(CompanionProfile.HAIR_BROWN))
        assertTrue(labels.contains(CompanionProfile.HAIR_BLONDE))
        assertTrue(labels.contains(CompanionProfile.HAIR_SILVER))

        val auburn = swatches.first { it.label == CompanionProfile.HAIR_AUBURN }
        assertEquals(AsterColors.HairAuburn, auburn.color)
    }

    @Test
    fun testEyeSwatchesPalette() {
        val swatches = DefaultSwatches.EyeSwatches
        assertEquals(5, swatches.size)

        val labels = swatches.map { it.label }
        assertTrue(labels.contains(CompanionProfile.EYE_HAZEL))
        assertTrue(labels.contains(CompanionProfile.EYE_BROWN))
        assertTrue(labels.contains(CompanionProfile.EYE_BLUE))
        assertTrue(labels.contains(CompanionProfile.EYE_GREEN))
        assertTrue(labels.contains(CompanionProfile.EYE_GREY))

        val hazel = swatches.first { it.label == CompanionProfile.EYE_HAZEL }
        assertEquals(AsterColors.EyeHazel, hazel.color)
    }

    @Test
    fun testDefaultQuickActions() {
        val actions = DefaultQuickActions.list
        assertEquals(2, actions.size)
        assertEquals("Add reminder", actions[0].label)
        assertEquals("Summarize", actions[1].label)
    }

    @Test
    fun testAsterColorsTokensAndBannedColorsCompliance() {
        // Core tokens must match screenshot values
        assertEquals(Color(0xFFE59843), AsterColors.AmberPrimary)
        assertEquals(Color(0xFFF5A623), AsterColors.AmberBright)
        assertEquals(Color(0xFF4CD964), AsterColors.OnlineGreen)
        assertEquals(Color(0xFF1C1A18), AsterColors.SurfaceCard)

        // Strict Banned Colors Verification: ensure none of the 8 banned colors are in AsterColors
        val bannedHexes = listOf(
            0xFF0b0d11,
            0xFF14171d,
            0xFF1c2029,
            0xFF222733,
            0xFF2a303e,
            0xFF343b4d,
            0xFF252a36,
            0xFF12151b
        )

        val asterColorList = listOf(
            AsterColors.Background,
            AsterColors.SurfaceCard,
            AsterColors.SurfaceElevated,
            AsterColors.SurfaceContainer,
            AsterColors.BorderSubtle,
            AsterColors.BorderActive,
            AsterColors.AmberPrimary,
            AsterColors.AmberBright,
            AsterColors.AmberContainer,
            AsterColors.OnlineGreen,
            AsterColors.TextPrimary,
            AsterColors.TextSecondary,
            AsterColors.TextMuted
        )

        asterColorList.forEach { color ->
            val argbLong = (color.value shr 32).toLong()
            assertFalse(
                "Color $color must not match any banned hex",
                bannedHexes.contains(argbLong)
            )
        }
    }
}
