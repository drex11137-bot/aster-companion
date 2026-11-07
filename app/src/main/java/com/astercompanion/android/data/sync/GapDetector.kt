package com.astercompanion.android.data.sync

import com.astercompanion.android.data.local.OutboxEventEntity
import com.astercompanion.android.data.local.SyncGapDao
import com.astercompanion.android.data.local.SyncGapEntity
import java.util.UUID

/**
 * Detects skipped sequence numbers and records unrecoverable gaps without inventing false continuity (PRD v1.1 §6.3, §6.4).
 */
class GapDetector(
    private val syncGapDao: SyncGapDao? = null
) {
    /**
     * Checks if there is a sequence gap between lastKnownSequence and incomingSequence.
     * If a gap is detected, persists a SyncGapEntity and returns GapDetectionResult.GapDetected.
     */
    suspend fun checkSequence(
        deviceId: String,
        profileId: String,
        lastKnownSequence: Long,
        incomingSequence: Long,
        reason: String = "SEQUENCE_SKIP_DETECTED"
    ): GapDetectionResult {
        val expected = lastKnownSequence + 1

        return when {
            incomingSequence == expected -> {
                GapDetectionResult.Continuous
            }
            incomingSequence < expected -> {
                GapDetectionResult.DuplicateOrOlder
            }
            else -> {
                // Gap detected: sequence numbers between expected and incomingSequence - 1 are missing
                val missingCount = incomingSequence - expected
                val gap = SyncGapEntity(
                    id = UUID.randomUUID().toString(),
                    deviceId = deviceId,
                    profileId = profileId,
                    fromSequence = expected,
                    toSequence = incomingSequence - 1,
                    missingCount = missingCount,
                    detectedAt = System.currentTimeMillis(),
                    reason = reason,
                    isAcknowledged = false
                )
                syncGapDao?.insertGap(gap)
                GapDetectionResult.GapDetected(gap)
            }
        }
    }

    /**
     * Audits an ordered list of events for internal continuity gaps.
     * Does not invent fake events; reports all observed gaps.
     */
    fun findGapsInBatch(
        deviceId: String,
        profileId: String,
        events: List<OutboxEventEntity>,
        initialExpectedSequence: Long
    ): List<SyncGapEntity> {
        val gaps = mutableListOf<SyncGapEntity>()
        var expected = initialExpectedSequence

        for (event in events) {
            if (event.sequenceNumber > expected) {
                gaps.add(
                    SyncGapEntity(
                        id = UUID.randomUUID().toString(),
                        deviceId = deviceId,
                        profileId = profileId,
                        fromSequence = expected,
                        toSequence = event.sequenceNumber - 1,
                        missingCount = event.sequenceNumber - expected,
                        detectedAt = System.currentTimeMillis(),
                        reason = "BATCH_SEQUENCE_DISCONTINUITY"
                    )
                )
            }
            if (event.sequenceNumber >= expected) {
                expected = event.sequenceNumber + 1
            }
        }
        return gaps
    }
}
