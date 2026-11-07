package com.astercompanion.android.awareness

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.graphics.Color
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Binder
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.util.Log
import androidx.core.app.NotificationCompat
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

/**
 * Android Foreground Service for Native Screen & Audio Awareness in Aster Companion.
 * Adheres strictly to PRD v1.1 §5 & §13:
 * - Proper Android 14/15 Foreground Service with `foregroundServiceType="mediaProjection|microphone"`.
 * - Handles `MediaProjection.Callback` including `onStop()` when OS or user revokes consent.
 * - Non-obstructive foreground notification with instant "Pause", "Mute Audio", and "Stop" actions.
 * - Coordinates ScreenCaptureEngine, AudioAwarenessEngine, MetricsTracker, and Floating Overlay.
 */
class MediaProjectionService : Service() {

    companion object {
        private const val TAG = "MediaProjectionService"

        const val CHANNEL_ID = "aster_awareness_channel"
        const val NOTIFICATION_ID = 20261101

        const val ACTION_START = "com.astercompanion.android.awareness.ACTION_START"
        const val ACTION_STOP = "com.astercompanion.android.awareness.ACTION_STOP"
        const val ACTION_PAUSE_SCREEN = "com.astercompanion.android.awareness.ACTION_PAUSE_SCREEN"
        const val ACTION_RESUME_SCREEN = "com.astercompanion.android.awareness.ACTION_RESUME_SCREEN"
        const val ACTION_MUTE_AUDIO = "com.astercompanion.android.awareness.ACTION_MUTE_AUDIO"
        const val ACTION_UNMUTE_AUDIO = "com.astercompanion.android.awareness.ACTION_UNMUTE_AUDIO"

        const val EXTRA_RESULT_CODE = "extra_result_code"
        const val EXTRA_RESULT_DATA = "extra_result_data"
        const val EXTRA_PROFILE_ID = "extra_profile_id"
        const val EXTRA_PROFILE_NAME = "extra_profile_name"
        const val EXTRA_AUDIO_MODE = "extra_audio_mode"

        // Global controller access for UI components and ViewModels
        private val _currentStatus = MutableStateFlow(AwarenessStatus.IDLE)
        val currentStatus: StateFlow<AwarenessStatus> = _currentStatus.asStateFlow()

        private val _metrics = MutableStateFlow(AwarenessMetrics())
        val metrics: StateFlow<AwarenessMetrics> = _metrics.asStateFlow()

        private var activeInstance: MediaProjectionService? = null

        fun getActiveInstance(): MediaProjectionService? = activeInstance

        fun startServiceIntent(
            context: Context,
            resultCode: Int,
            resultData: Intent,
            profileId: String = "profile_aster",
            profileName: String = "Aster",
            audioMode: AudioCaptureMode = AudioCaptureMode.DUAL
        ): Intent {
            return Intent(context, MediaProjectionService::class.java).apply {
                action = ACTION_START
                putExtra(EXTRA_RESULT_CODE, resultCode)
                putExtra(EXTRA_RESULT_DATA, resultData)
                putExtra(EXTRA_PROFILE_ID, profileId)
                putExtra(EXTRA_PROFILE_NAME, profileName)
                putExtra(EXTRA_AUDIO_MODE, audioMode.name)
            }
        }
    }

    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
    private val mainHandler = Handler(Looper.getMainLooper())
    private val binder = LocalBinder()

    private var mediaProjectionManager: MediaProjectionManager? = null
    private var mediaProjection: MediaProjection? = null
    private var projectionCallback: MediaProjection.Callback? = null

    private lateinit var screenCaptureEngine: ScreenCaptureEngine
    private lateinit var audioAwarenessEngine: AudioAwarenessEngine
    private lateinit var metricsTracker: MetricsTracker
    private var floatingIndicator: AwarenessFloatingIndicator? = null

    private var activeProfileId: String = "profile_aster"
    private var activeProfileName: String = "Aster"
    private var activeAudioMode: AudioCaptureMode = AudioCaptureMode.DUAL
    private var isScreenPaused: Boolean = false
    private var isAudioMuted: Boolean = false

    inner class LocalBinder : Binder() {
        fun getService(): MediaProjectionService = this@MediaProjectionService
    }

    override fun onCreate() {
        super.onCreate()
        activeInstance = this
        Log.i(TAG, "MediaProjectionService created.")

        createNotificationChannel()

        screenCaptureEngine = ScreenCaptureEngine()
        audioAwarenessEngine = AudioAwarenessEngine(applicationContext, serviceScope)
        metricsTracker = MetricsTracker(serviceScope, activeProfileId)

        floatingIndicator = AwarenessFloatingIndicator(applicationContext)

        // Forward metrics to companion StateFlow
        serviceScope.launch {
            metricsTracker.metrics.collect { updated ->
                _metrics.value = updated
            }
        }
    }

    override fun onBind(intent: Intent?): IBinder = binder

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent == null) {
            return START_NOT_STICKY
        }

        when (intent.action) {
            ACTION_START -> {
                val resultCode = intent.getIntExtra(EXTRA_RESULT_CODE, -1)
                val resultData = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                    intent.getParcelableExtra(EXTRA_RESULT_DATA, Intent::class.java)
                } else {
                    @Suppress("DEPRECATION")
                    intent.getParcelableExtra<Intent>(EXTRA_RESULT_DATA)
                }
                val profileId = intent.getStringExtra(EXTRA_PROFILE_ID) ?: "profile_aster"
                val profileName = intent.getStringExtra(EXTRA_PROFILE_NAME) ?: "Aster"
                val modeStr = intent.getStringExtra(EXTRA_AUDIO_MODE) ?: AudioCaptureMode.DUAL.name
                val audioMode = try { AudioCaptureMode.valueOf(modeStr) } catch (e: Exception) { AudioCaptureMode.DUAL }

                if (resultCode != -1 && resultData != null) {
                    startAwarenessSession(resultCode, resultData, profileId, profileName, audioMode)
                } else {
                    Log.e(TAG, "Cannot start awareness: missing MediaProjection result code or data.")
                    stopSelf()
                }
            }
            ACTION_PAUSE_SCREEN -> pauseScreen()
            ACTION_RESUME_SCREEN -> resumeScreen()
            ACTION_MUTE_AUDIO -> muteAudio()
            ACTION_UNMUTE_AUDIO -> unmuteAudio()
            ACTION_STOP -> stopAwarenessSession()
        }

        return START_NOT_STICKY
    }

    private fun startAwarenessSession(
        resultCode: Int,
        resultData: Intent,
        profileId: String,
        profileName: String,
        audioMode: AudioCaptureMode
    ) {
        activeProfileId = profileId
        activeProfileName = profileName
        activeAudioMode = audioMode
        isScreenPaused = false
        isAudioMuted = false

        _currentStatus.value = AwarenessStatus.INITIALIZING

        // Start Foreground immediately before MediaProjection setup (Strict Android 14 requirement)
        val initialNotification = buildNotification()
        val foregroundType = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            var type = ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION
            if (audioMode != AudioCaptureMode.NONE && Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
                type = type or ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE
            }
            type
        } else {
            0
        }

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            startForeground(NOTIFICATION_ID, initialNotification, foregroundType)
        } else {
            startForeground(NOTIFICATION_ID, initialNotification)
        }

        try {
            mediaProjectionManager = getSystemService(Context.MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
            val projection = mediaProjectionManager?.getMediaProjection(resultCode, resultData)

            if (projection == null) {
                Log.e(TAG, "Failed to acquire MediaProjection from MediaProjectionManager")
                _currentStatus.value = AwarenessStatus.ERROR
                stopSelf()
                return
            }
            mediaProjection = projection

            // Setup MediaProjection.Callback for revocation & dynamic content changes
            val callback = object : MediaProjection.Callback() {
                override fun onStop() {
                    super.onStop()
                    Log.w(TAG, "MediaProjection consent revoked by user or system OS callback.")
                    handleConsentRevoked()
                }
            }
            projectionCallback = callback
            projection.registerCallback(callback, mainHandler)

            val displayMetrics = resources.displayMetrics
            val config = AwarenessConfig(
                targetWidth = displayMetrics.widthPixels,
                targetHeight = displayMetrics.heightPixels,
                targetDpi = displayMetrics.densityDpi,
                audioMode = audioMode
            )

            metricsTracker.reset(profileId)

            // Start Screen and Audio engines
            screenCaptureEngine.start(projection, config, metricsTracker)
            audioAwarenessEngine.start(projection, audioMode, config.audioSampleRate, metricsTracker)

            _currentStatus.value = AwarenessStatus.ACTIVE
            updateNotification()

            // Display floating overlay pill
            floatingIndicator?.show(activeProfileName, this)

            Log.i(TAG, "Awareness session active for profile $profileName ($profileId)")
        } catch (t: Throwable) {
            Log.e(TAG, "Exception initializing MediaProjection awareness session", t)
            _currentStatus.value = AwarenessStatus.ERROR
            stopSelf()
        }
    }

    /**
     * Handles revocation of consent per PRD v1.1 §13.
     */
    private fun handleConsentRevoked() {
        _currentStatus.value = AwarenessStatus.REVOKED
        screenCaptureEngine.stop()
        audioAwarenessEngine.stop()
        metricsTracker.stop()

        updateNotification()
        floatingIndicator?.updateState(AwarenessStatus.REVOKED)

        mainHandler.postDelayed({
            stopSelf()
        }, 1500L)
    }

    fun pauseScreen() {
        if (_currentStatus.value == AwarenessStatus.ACTIVE) {
            screenCaptureEngine.pause()
            isScreenPaused = true
            _currentStatus.value = AwarenessStatus.PAUSED
            updateNotification()
            floatingIndicator?.updateState(AwarenessStatus.PAUSED)
        }
    }

    fun resumeScreen() {
        if (_currentStatus.value == AwarenessStatus.PAUSED) {
            screenCaptureEngine.resume()
            isScreenPaused = false
            _currentStatus.value = AwarenessStatus.ACTIVE
            updateNotification()
            floatingIndicator?.updateState(AwarenessStatus.ACTIVE)
        }
    }

    fun muteAudio() {
        audioAwarenessEngine.mute()
        isAudioMuted = true
        updateNotification()
        floatingIndicator?.updateAudioMuted(true)
    }

    fun unmuteAudio() {
        audioAwarenessEngine.unmute()
        isAudioMuted = false
        updateNotification()
        floatingIndicator?.updateAudioMuted(false)
    }

    fun stopAwarenessSession() {
        Log.i(TAG, "Stopping awareness session requested by user/service.")
        _currentStatus.value = AwarenessStatus.IDLE

        screenCaptureEngine.stop()
        audioAwarenessEngine.stop()
        metricsTracker.stop()

        try {
            projectionCallback?.let { mediaProjection?.unregisterCallback(it) }
            mediaProjection?.stop()
        } catch (e: Exception) {
            Log.w(TAG, "Error stopping MediaProjection", e)
        } finally {
            mediaProjection = null
            projectionCallback = null
        }

        floatingIndicator?.dismiss()

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
            stopForeground(STOP_FOREGROUND_REMOVE)
        } else {
            @Suppress("DEPRECATION")
            stopForeground(true)
        }
        stopSelf()
    }

    private fun updateNotification() {
        val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        manager.notify(NOTIFICATION_ID, buildNotification())
    }

    private fun buildNotification(): Notification {
        val status = _currentStatus.value
        val title = "$activeProfileName • Continuous Awareness"
        val statusText = when (status) {
            AwarenessStatus.ACTIVE -> if (isAudioMuted) "Screen aware • Audio muted" else "Screen and audio aware"
            AwarenessStatus.PAUSED -> if (isAudioMuted) "Screen paused • Audio muted" else "Screen paused • Audio aware"
            AwarenessStatus.MUTED -> "Screen aware • Audio muted"
            AwarenessStatus.REVOKED -> "Consent revoked by system or user"
            AwarenessStatus.INITIALIZING -> "Initializing awareness capture..."
            AwarenessStatus.ERROR -> "Awareness session encountered an error"
            AwarenessStatus.IDLE -> "Awareness idle"
        }

        val builder = NotificationCompat.Builder(this, CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_menu_camera)
            .setContentTitle(title)
            .setContentText(statusText)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .setColor(Color.parseColor("#F59E0B")) // Warm amber accent

        // Quick Pause / Resume Action
        if (status == AwarenessStatus.PAUSED) {
            val resumeIntent = Intent(this, MediaProjectionService::class.java).apply {
                action = ACTION_RESUME_SCREEN
            }
            val resumePendingIntent = PendingIntent.getService(
                this, 1, resumeIntent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            builder.addAction(android.R.drawable.ic_media_play, "Resume", resumePendingIntent)
        } else if (status == AwarenessStatus.ACTIVE) {
            val pauseIntent = Intent(this, MediaProjectionService::class.java).apply {
                action = ACTION_PAUSE_SCREEN
            }
            val pausePendingIntent = PendingIntent.getService(
                this, 2, pauseIntent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            builder.addAction(android.R.drawable.ic_media_pause, "Pause", pausePendingIntent)
        }

        // Quick Mute / Unmute Action
        if (activeAudioMode != AudioCaptureMode.NONE) {
            if (isAudioMuted) {
                val unmuteIntent = Intent(this, MediaProjectionService::class.java).apply {
                    action = ACTION_UNMUTE_AUDIO
                }
                val unmutePendingIntent = PendingIntent.getService(
                    this, 3, unmuteIntent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
                )
                builder.addAction(android.R.drawable.stat_notify_chat, "Unmute Audio", unmutePendingIntent)
            } else {
                val muteIntent = Intent(this, MediaProjectionService::class.java).apply {
                    action = ACTION_MUTE_AUDIO
                }
                val mutePendingIntent = PendingIntent.getService(
                    this, 4, muteIntent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
                )
                builder.addAction(android.R.drawable.ic_lock_silent_mode, "Mute Audio", mutePendingIntent)
            }
        }

        // Quick Stop Action
        val stopIntent = Intent(this, MediaProjectionService::class.java).apply {
            action = ACTION_STOP
        }
        val stopPendingIntent = PendingIntent.getService(
            this, 5, stopIntent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        builder.addAction(android.R.drawable.ic_menu_close_clear_cancel, "Stop", stopPendingIntent)

        return builder.build()
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Aster Continuous Awareness",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Non-obstructive foreground controls for screen and audio awareness"
                setShowBadge(false)
                enableVibration(false)
                enableLights(false)
            }
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
            manager.createNotificationChannel(channel)
        }
    }

    val frameFlow: SharedFlow<CapturedFrame>
        get() = screenCaptureEngine.frameFlow

    val audioFlow: SharedFlow<AudioChunk>
        get() = audioAwarenessEngine.audioFlow

    override fun onDestroy() {
        super.onDestroy()
        activeInstance = null
        stopAwarenessSession()
        serviceScope.cancel()
        Log.i(TAG, "MediaProjectionService destroyed.")
    }
}
