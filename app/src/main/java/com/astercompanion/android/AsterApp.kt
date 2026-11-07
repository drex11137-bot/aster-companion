package com.astercompanion.android

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import com.astercompanion.android.awareness.MediaProjectionService
import com.astercompanion.android.data.local.AsterDatabase

/**
 * AsterApp
 *
 * Application entry point for Aster Companion.
 * Initializes database instances and configures high-priority notification channels
 * for the foreground media projection awareness service.
 */
class AsterApp : Application() {

    override fun onCreate() {
        super.onCreate()
        createNotificationChannels()
        // Initialize offline Room database instance early
        AsterDatabase.getInstance(this)
    }

    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                MediaProjectionService.CHANNEL_ID,
                getString(R.string.notification_channel_name),
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = getString(R.string.notification_channel_desc)
                setShowBadge(false)
            }
            val manager = getSystemService(NotificationManager::class.java)
            manager?.createNotificationChannel(channel)
        }
    }
}
