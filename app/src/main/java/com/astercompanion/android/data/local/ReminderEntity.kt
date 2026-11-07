package com.astercompanion.android.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey
import com.astercompanion.android.model.Reminder

@Entity(tableName = "reminders")
data class ReminderEntity(
    @PrimaryKey val id: String,
    val profileId: String,
    val title: String,
    val dayLabel: String,
    val isSnoozed: Boolean,
    val snoozeUntil: Long?,
    val createdAt: Long
) {
    fun toDomain(): Reminder = Reminder(
        id = id,
        profileId = profileId,
        title = title,
        dayLabel = dayLabel,
        isSnoozed = isSnoozed,
        snoozeUntil = snoozeUntil,
        createdAt = createdAt
    )

    companion object {
        fun fromDomain(domain: Reminder): ReminderEntity = ReminderEntity(
            id = domain.id,
            profileId = domain.profileId,
            title = domain.title,
            dayLabel = domain.dayLabel,
            isSnoozed = domain.isSnoozed,
            snoozeUntil = domain.snoozeUntil,
            createdAt = domain.createdAt
        )
    }
}
