package com.astercompanion.android.data.sync

import com.astercompanion.android.data.crypto.ChecksumUtil
import com.astercompanion.android.data.local.SyncCheckpointEntity
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicBoolean

/**
 * Interface defining communication with the Aster Companion cloud sync endpoint (PRD v1.1 §6).
 */
interface RemoteSyncClient {
    suspend fun uploadBatch(batch: SyncUploadBatch): Result<SyncUploadResponse>
    suspend fun fetchCheckpoint(deviceId: String, profileId: String): Result<SyncCheckpointEntity?>
}

/**
 * High-fidelity in-memory implementation of RemoteSyncClient for testing, offline simulation,
 * and reliable local verification without external servers.
 */
class MockRemoteSyncClient : RemoteSyncClient {

    private val isNetworkAvailable = AtomicBoolean(true)
    private val processedChecksums = ConcurrentHashMap<String, Long>() // checksum -> sequenceNumber
    private val checkpoints = ConcurrentHashMap<String, SyncCheckpointEntity>() // "$deviceId:$profileId" -> Checkpoint
    private var simulatedFailureCount = 0

    fun setNetworkAvailable(available: Boolean) {
        isNetworkAvailable.set(available)
    }

    fun setSimulatedFailureCount(count: Int) {
        simulatedFailureCount = count
    }

    override suspend fun uploadBatch(batch: SyncUploadBatch): Result<SyncUploadResponse> {
        if (!isNetworkAvailable.get()) {
            return Result.failure(java.io.IOException("Network unavailable (offline)"))
        }

        if (simulatedFailureCount > 0) {
            simulatedFailureCount--
            return Result.failure(java.io.IOException("Simulated transient network error"))
        }

        if (batch.events.isEmpty()) {
            val key = "${batch.deviceId}:${batch.profileId}"
            val currentCheckpoint = checkpoints[key]
            return Result.success(
                SyncUploadResponse(
                    deviceId = batch.deviceId,
                    acknowledgedSequenceNumber = currentCheckpoint?.lastAcknowledgedSequenceNumber ?: 0L,
                    acknowledgedEventIds = emptyList()
                )
            )
        }

        // Validate checksums and verify idempotency
        var maxSeq = 0L
        val acknowledgedIds = mutableListOf<String>()

        for (event in batch.events) {
            // Verify payload checksum
            val isChecksumValid = ChecksumUtil.verifyChecksum(event.payloadJson, event.checksum)
            if (!isChecksumValid) {
                return Result.failure(
                    IllegalArgumentException("Corrupted event payload checksum for event ${event.id}")
                )
            }

            // Check idempotency: if already processed, record but do not re-execute
            val existingSeq = processedChecksums.putIfAbsent(event.checksum, event.sequenceNumber)
            if (existingSeq != null && existingSeq != event.sequenceNumber) {
                // Same payload, different sequence: possible replay or duplication
            }

            if (event.sequenceNumber > maxSeq) {
                maxSeq = event.sequenceNumber
            }
            acknowledgedIds.add(event.id)
        }

        val key = "${batch.deviceId}:${batch.profileId}"
        val existing = checkpoints[key]
        val newMaxSeq = if (existing != null) maxOf(existing.lastAcknowledgedSequenceNumber, maxSeq) else maxSeq

        val updatedCheckpoint = SyncCheckpointEntity(
            deviceId = batch.deviceId,
            profileId = batch.profileId,
            lastAcknowledgedSequenceNumber = newMaxSeq,
            lastServerTimestamp = System.currentTimeMillis(),
            updatedAt = System.currentTimeMillis()
        )
        checkpoints[key] = updatedCheckpoint

        return Result.success(
            SyncUploadResponse(
                deviceId = batch.deviceId,
                acknowledgedSequenceNumber = newMaxSeq,
                acknowledgedEventIds = acknowledgedIds,
                serverTimestamp = System.currentTimeMillis(),
                isSuccess = true
            )
        )
    }

    override suspend fun fetchCheckpoint(deviceId: String, profileId: String): Result<SyncCheckpointEntity?> {
        if (!isNetworkAvailable.get()) {
            return Result.failure(java.io.IOException("Network unavailable (offline)"))
        }
        val key = "$deviceId:$profileId"
        return Result.success(checkpoints[key])
    }

    fun getProcessedChecksumCount(): Int = processedChecksums.size
}
