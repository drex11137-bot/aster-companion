package com.astercompanion.android.data.sync

import com.astercompanion.android.data.local.OutboxEventEntity
import com.astercompanion.android.data.local.SyncGapEntity

/**
 * Represents availability of cloud AI reasoning and services (PRD v1.1 §6.5).
 * Distinct online/offline state: user can always read local cached history,
 * but cloud AI and actions are clearly indicated as unavailable when offline.
 */
sealed class CloudAiAvailability {
    object Available : CloudAiAvailability()

    data class UnavailableOffline(
        val message: String = "Network is offline. Cloud AI reasoning, audio streaming, and device actions are temporarily unavailable. Local cached history and memories remain fully accessible."
    ) : CloudAiAvailability()

    data class Degraded(
        val reason: String
    ) : CloudAiAvailability()
}

/**
 * State snapshot of the offline database and synchronization engine.
 */
data class SyncState(
    val isOnline: Boolean = true,
    val isSyncing: Boolean = false,
    val pendingEventCount: Int = 0,
    val lastAcknowledgedSequence: Long = 0L,
    val totalGapsDetected: Int = 0,
    val cloudAiAvailability: CloudAiAvailability = CloudAiAvailability.Available,
    val lastSyncTimestamp: Long? = null,
    val lastErrorMessage: String? = null
)

/**
 * Batch of outbox events ready for upload.
 */
data class SyncUploadBatch(
    val deviceId: String,
    val profileId: String,
    val events: List<OutboxEventEntity>
)

/**
 * Server acknowledgment response after an idempotent upload.
 */
data class SyncUploadResponse(
    val deviceId: String,
    val acknowledgedSequenceNumber: Long,
    val acknowledgedEventIds: List<String>,
    val serverTimestamp: Long = System.currentTimeMillis(),
    val isSuccess: Boolean = true,
    val errorMessage: String? = null
)

/**
 * Result of sequence gap evaluation.
 */
sealed class GapDetectionResult {
    object Continuous : GapDetectionResult()
    object DuplicateOrOlder : GapDetectionResult()
    data class GapDetected(val gap: SyncGapEntity) : GapDetectionResult()
}
