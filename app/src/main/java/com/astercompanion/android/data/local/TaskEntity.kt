package com.astercompanion.android.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.astercompanion.android.model.CompanionTask

@Entity(tableName = "companion_tasks")
data class TaskEntity(
    @PrimaryKey val id: String,
    val profileId: String,
    val title: String,
    val dueLabel: String,
    val isCompleted: Boolean,
    val completedAt: Long?,
    val createdAt: Long
) {
    fun toDomain(): CompanionTask = CompanionTask(
        id = id,
        profileId = profileId,
        title = title,
        dueLabel = dueLabel,
        isCompleted = isCompleted,
        completedAt = completedAt,
        createdAt = createdAt
    )

    companion object {
        fun fromDomain(domain: CompanionTask): TaskEntity = TaskEntity(
            id = domain.id,
            profileId = domain.profileId,
            title = domain.title,
            dueLabel = domain.dueLabel,
            isCompleted = domain.isCompleted,
            completedAt = domain.completedAt,
            createdAt = domain.createdAt
        )
    }
}
