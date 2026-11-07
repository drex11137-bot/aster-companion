package com.astercompanion.android.data.local

import com.astercompanion.android.data.local.MemoryEntity
import com.astercompanion.android.data.local.ProfileEntity
import com.astercompanion.android.data.repository.AsterRepository
import com.astercompanion.android.data.sync.MockRemoteSyncClient
import com.astercompanion.android.data.sync.SyncEngine
import com.astercompanion.android.data.testutil.FakeChatMessageDao
import com.astercompanion.android.data.testutil.FakeMemoryDao
import com.astercompanion.android.data.testutil.FakeOutboxDao
import com.astercompanion.android.data.testutil.FakeProfileDao
import com.astercompanion.android.data.testutil.FakeSyncCheckpointDao
import com.astercompanion.android.data.testutil.FakeSyncGapDao
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class ProfileAndMemoryIsolationTest {

    private lateinit var profileDao: FakeProfileDao
    private lateinit var memoryDao: FakeMemoryDao
    private lateinit var chatMessageDao: FakeChatMessageDao
    private lateinit var outboxDao: FakeOutboxDao
    private lateinit var syncCheckpointDao: FakeSyncCheckpointDao
    private lateinit var syncGapDao: FakeSyncGapDao
    private lateinit var remoteClient: MockRemoteSyncClient
    private lateinit var syncEngine: SyncEngine
    private lateinit var repository: AsterRepository

    @Before
    fun setUp() {
        profileDao = FakeProfileDao()
        memoryDao = FakeMemoryDao()
        chatMessageDao = FakeChatMessageDao()
        outboxDao = FakeOutboxDao()
        syncCheckpointDao = FakeSyncCheckpointDao()
        syncGapDao = FakeSyncGapDao()
        remoteClient = MockRemoteSyncClient()

        syncEngine = SyncEngine(
            outboxDao = outboxDao,
            syncCheckpointDao = syncCheckpointDao,
            syncGapDao = syncGapDao,
            chatMessageDao = chatMessageDao,
            remoteClient = remoteClient,
            deviceId = "pixel_9_test_device"
        )

        repository = AsterRepository(
            profileDao = profileDao,
            memoryDao = memoryDao,
            chatMessageDao = chatMessageDao,
            syncEngine = syncEngine
        )
    }

    @Test
    fun testMaxTwoProfilesEnforcement() = runBlocking {
        // Create 1st profile
        val profile1Result = repository.createProfile(name = "Aster", voice = "Warm voice")
        assertTrue(profile1Result.isSuccess)
        val profile1 = profile1Result.getOrThrow()
        assertEquals("Aster", profile1.name)
        assertTrue(profile1.isActive) // 1st profile is active by default

        // Create 2nd profile
        val profile2Result = repository.createProfile(name = "Nova", voice = "Calm")
        assertTrue(profile2Result.isSuccess)
        val profile2 = profile2Result.getOrThrow()
        assertEquals("Nova", profile2.name)
        assertFalse(profile2.isActive)

        assertEquals(2, profileDao.countProfiles())

        // Attempt to create 3rd profile (PRD v1.1 §9.1: max 2 companion profiles allowed per account)
        val profile3Result = repository.createProfile(name = "Celeste", voice = "Playful")
        assertTrue(profile3Result.isFailure)
        assertTrue(profile3Result.exceptionOrNull()?.message?.contains("Maximum of 2") == true)
        assertEquals(2, profileDao.countProfiles())
    }

    @Test
    fun testProfileSwitchingPreservesSingleActiveDeviceRule() = runBlocking {
        val p1 = repository.createProfile("Aster").getOrThrow()
        val p2 = repository.createProfile("Nova").getOrThrow()

        // P1 should be active initially
        val active1 = repository.getActiveProfileSync()
        assertNotNull(active1)
        assertEquals(p1.id, active1?.id)
        assertTrue(active1?.isActive == true)

        // Switch to P2 (PRD v1.1 §9.5, §9.6)
        repository.switchProfile(p2.id)

        val active2 = repository.getActiveProfileSync()
        assertNotNull(active2)
        assertEquals(p2.id, active2?.id)
        assertTrue(active2?.isActive == true)

        // Verify P1 is no longer active
        val updatedP1 = profileDao.getProfileById(p1.id)
        assertFalse(updatedP1?.isActive == true)
    }

    @Test
    fun testStrictMemoryIsolationBetweenProfiles() = runBlocking {
        val p1 = repository.createProfile("Aster").getOrThrow()
        val p2 = repository.createProfile("Nova").getOrThrow()

        // Save memories under Profile 1
        repository.saveMemory(
            profileId = p1.id,
            content = "You love oat flat whites",
            category = MemoryEntity.CATEGORY_PREFERENCE
        )
        repository.saveMemory(
            profileId = p1.id,
            content = "Sister's birthday: Nov 14",
            category = MemoryEntity.CATEGORY_RELATIONSHIP
        )

        // Save memory under Profile 2
        repository.saveMemory(
            profileId = p2.id,
            content = "Allergic to peanuts",
            category = MemoryEntity.CATEGORY_PREFERENCE
        )

        // Profile 1 queries must only return Profile 1 memories
        val p1Memories = repository.getActiveMemories(p1.id).first()
        assertEquals(2, p1Memories.size)
        assertTrue(p1Memories.any { it.content == "You love oat flat whites" })
        assertTrue(p1Memories.any { it.content == "Sister's birthday: Nov 14" })
        assertFalse(p1Memories.any { it.content == "Allergic to peanuts" }) // MUST NOT LEAK

        // Profile 2 queries must only return Profile 2 memories
        val p2Memories = repository.getActiveMemories(p2.id).first()
        assertEquals(1, p2Memories.size)
        assertEquals("Allergic to peanuts", p2Memories[0].content)
        assertFalse(p2Memories.any { it.content == "You love oat flat whites" }) // MUST NOT LEAK
    }

    @Test
    fun testMemoryPinningAndForgetting() = runBlocking {
        val p1 = repository.createProfile("Aster").getOrThrow()

        val mem1 = repository.saveMemory(
            profileId = p1.id,
            content = "Running a half marathon in March",
            category = MemoryEntity.CATEGORY_ACTIVITY
        )
        val mem2 = repository.saveMemory(
            profileId = p1.id,
            content = "Prefers short answers in the morning",
            category = MemoryEntity.CATEGORY_PREFERENCE
        )

        // Pin mem1
        repository.setMemoryPinned(p1.id, mem1.id, true)
        val pinned = repository.getPinnedMemories(p1.id).first()
        assertEquals(1, pinned.size)
        assertEquals(mem1.id, pinned[0].id)

        // Forget mem2
        repository.setMemoryForgotten(p1.id, mem2.id, true)
        val active = repository.getActiveMemories(p1.id).first()
        assertEquals(1, active.size)
        assertEquals(mem1.id, active[0].id)

        // Search
        val searchResult = repository.searchMemories(p1.id, "marathon").first()
        assertEquals(1, searchResult.size)
        assertEquals("Running a half marathon in March", searchResult[0].content)
    }
}
