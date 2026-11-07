package com.astercompanion.android.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.astercompanion.android.model.MemoryShareAudit

@Entity(tableName = "memory_audits")
data class MemoryAuditEntity(
    @PrimaryKey val id: String,
    val memoryId: String,
    val memoryTitle: String,
    val sourceProfileId: String,
    val targetProfileId: String,
    val timestamp: Long,
    val confirmedByUser: Boolean
) {
    fun toDomain(): MemoryShareAudit = MemoryShareAudit(
        id = id,
        memoryId = memoryId,
        memoryTitle = memoryTitle,
        sourceProfileId = sourceProfileId,
        targetProfileId = targetProfileId,
        timestamp = timestamp,
        confirmedByUser = confirmedByUser
    )

    companion object {
        fun fromDomain(domain: MemoryShareAudit): MemoryAuditEntity = MemoryAuditEntity(
            id = domain.id,
            memoryId = domain.memoryId,
            memoryTitle = domain.memoryTitle,
            sourceProfileId = domain.sourceProfileId,
            targetProfileId = domain.targetProfileId,
            timestamp = domain.timestamp,
            confirmedByUser = domain.confirmedByUser
        )
    }
}
