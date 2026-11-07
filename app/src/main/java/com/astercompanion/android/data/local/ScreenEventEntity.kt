package com.astercompanion.android.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.astercompanion.android.model.ScreenEvent

@Entity(tableName = "screen_events")
data class ScreenEventEntity(
    @PrimaryKey val id: String,
    val profileId: String,
    val timestamp: Long,
    val sequenceNumber: Long,
    val eventType: String,
    val summary: String,
    val captureFps: Float,
    val uploadFps: Float,
    val analysisFps: Float,
    val checksum: String
) {
    fun toDomain(): ScreenEvent = ScreenEvent(
        id = id,
        profileId = profileId,
        timestamp = timestamp,
        sequenceNumber = sequenceNumber,
        eventType = eventType,
        summary = summary,
        captureFps = captureFps,
        uploadFps = uploadFps,
        analysisFps = analysisFps,
        checksum = checksum
    )

    companion object {
        fun fromDomain(domain: ScreenEvent): ScreenEventEntity = ScreenEventEntity(
            id = domain.id,
            profileId = domain.profileId,
            timestamp = domain.timestamp,
            sequenceNumber = domain.sequenceNumber,
            eventType = domain.eventType,
            summary = domain.summary,
            captureFps = domain.captureFps,
            uploadFps = domain.uploadFps,
            analysisFps = domain.analysisFps,
            checksum = domain.checksum
        )
    }
}
