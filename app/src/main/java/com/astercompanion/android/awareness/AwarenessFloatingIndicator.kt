package com.astercompanion.android.awareness

import android.annotation.SuppressLint
import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.PixelFormat
import android.graphics.RectF
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.util.Log
import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.Button
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import kotlin.math.abs

/**
 * Floating System Overlay Indicator and Contextual Control Panel for Aster Companion.
 * Adheres strictly to PRD v1.1 §13.4 & §13.5:
 * - Subtle, non-obstructive glowing pill indicator.
 * - Draggable and edge-snapping across system overlay.
 * - Tap opens the compact Contextual Control Panel with real-time FPS instrumentation,
 *   profile boundary info, continuity gap warnings, and instant Pause/Mute/Stop controls.
 */
class AwarenessFloatingIndicator(private val context: Context) {

    companion object {
        private const val TAG = "FloatingIndicator"

        // Design System Palette from PNG Reference Screenshots
        val COLOR_BG_GRAPHITE = Color.parseColor("#141311")
        val COLOR_SURFACE_CARD = Color.parseColor("#201E1A")
        val COLOR_BORDER = Color.parseColor("#332F28")
        val COLOR_AMBER_GLOW = Color.parseColor("#F59E0B")
        val COLOR_VIOLET_ACCENT = Color.parseColor("#7C66DC")
        val COLOR_TEXT_PRIMARY = Color.parseColor("#F4F4F5")
        val COLOR_TEXT_SECONDARY = Color.parseColor("#A1A1AA")
        val COLOR_STATUS_ACTIVE = Color.parseColor("#10B981")
        val COLOR_STATUS_PAUSED = Color.parseColor("#F59E0B")
        val COLOR_STATUS_REVOKED = Color.parseColor("#EF4444")
    }

    private val windowManager: WindowManager =
        context.getSystemService(Context.WINDOW_SERVICE) as WindowManager
    private val mainHandler = Handler(Looper.getMainLooper())

    private var pillView: PillView? = null
    private var controlPanelView: View? = null
    private var pillParams: WindowManager.LayoutParams? = null

    private var isPanelOpen = false
    private var activeProfileName: String = "Aster"
    private var currentStatus: AwarenessStatus = AwarenessStatus.ACTIVE
    private var isAudioMuted: Boolean = false
    private var activeService: MediaProjectionService? = null

    /**
     * Custom lightweight canvas-drawn glowing pill indicator.
     */
    @SuppressLint("ViewConstructor")
    inner class PillView(context: Context) : View(context) {
        private val bgPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = COLOR_BG_GRAPHITE
            style = Paint.Style.FILL
        }
        private val borderPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = COLOR_BORDER
            style = Paint.Style.STROKE
            strokeWidth = 3.0f
        }
        private val glowPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = COLOR_STATUS_ACTIVE
            style = Paint.Style.FILL
        }
        private val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            color = COLOR_TEXT_PRIMARY
            textSize = 34.0f
            isFakeBoldText = true
        }

        private val rect = RectF()

        override fun onDraw(canvas: Canvas) {
            super.onDraw(canvas)
            val w = width.toFloat()
            val h = height.toFloat()
            val radius = h / 2.0f

            rect.set(2.0f, 2.0f, w - 2.0f, h - 2.0f)
            canvas.drawRoundRect(rect, radius, radius, bgPaint)
            canvas.drawRoundRect(rect, radius, radius, borderPaint)

            // Dynamic status dot color
            glowPaint.color = when (currentStatus) {
                AwarenessStatus.ACTIVE -> if (isAudioMuted) COLOR_AMBER_GLOW else COLOR_STATUS_ACTIVE
                AwarenessStatus.PAUSED -> COLOR_STATUS_PAUSED
                AwarenessStatus.REVOKED -> COLOR_STATUS_REVOKED
                else -> COLOR_VIOLET_ACCENT
            }

            // Draw status indicator circle
            val dotRadius = 9.0f
            val dotX = 28.0f
            val dotY = h / 2.0f
            canvas.drawCircle(dotX, dotY, dotRadius, glowPaint)

            // Draw "Aster" label
            val text = activeProfileName
            val textY = (h / 2.0f) - ((textPaint.descent() + textPaint.ascent()) / 2.0f)
            canvas.drawText(text, 50.0f, textY, textPaint)
        }
    }

    /**
     * Shows floating pill overlay if overlay permission is granted.
     */
    fun show(profileName: String, service: MediaProjectionService) {
        this.activeProfileName = profileName
        this.activeService = service

        if (!canDrawOverlays()) {
            Log.w(TAG, "SYSTEM_ALERT_WINDOW permission not granted; skipping system overlay.")
            return
        }

        mainHandler.post {
            if (pillView != null) return@post

            val layoutType = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
            } else {
                @Suppress("DEPRECATION")
                WindowManager.LayoutParams.TYPE_PHONE
            }

            val params = WindowManager.LayoutParams(
                dpToPx(130),
                dpToPx(44),
                layoutType,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                        WindowManager.LayoutParams.FLAG_LAYOUT_NO_LIMITS,
                PixelFormat.TRANSLUCENT
            ).apply {
                gravity = Gravity.TOP or Gravity.START
                x = 24
                y = 180
            }
            pillParams = params

            val view = PillView(context)
            setupTouchListener(view, params)
            pillView = view

            try {
                windowManager.addView(view, params)
                Log.i(TAG, "Floating awareness indicator pill displayed.")
            } catch (e: Exception) {
                Log.e(TAG, "Failed to add floating indicator to WindowManager", e)
            }
        }
    }

    @SuppressLint("ClickableViewAccessibility")
    private fun setupTouchListener(view: View, params: WindowManager.LayoutParams) {
        var initialX = 0
        var initialY = 0
        var initialTouchX = 0f
        var initialTouchY = 0f
        var isClick = true

        view.setOnTouchListener { _, event ->
            when (event.action) {
                MotionEvent.ACTION_DOWN -> {
                    initialX = params.x
                    initialY = params.y
                    initialTouchX = event.rawX
                    initialTouchY = event.rawY
                    isClick = true
                    true
                }
                MotionEvent.ACTION_MOVE -> {
                    val deltaX = (event.rawX - initialTouchX).toInt()
                    val deltaY = (event.rawY - initialTouchY).toInt()
                    if (abs(deltaX) > 10 || abs(deltaY) > 10) {
                        isClick = false
                    }
                    params.x = initialX + deltaX
                    params.y = initialY + deltaY
                    try {
                        windowManager.updateViewLayout(view, params)
                    } catch (e: Exception) {
                        // View may be detached
                    }
                    true
                }
                MotionEvent.ACTION_UP -> {
                    if (isClick) {
                        toggleControlPanel()
                    }
                    true
                }
                else -> false
            }
        }
    }

    /**
     * Toggles visibility of the compact Contextual Control Panel.
     */
    fun toggleControlPanel() {
        mainHandler.post {
            if (isPanelOpen) {
                dismissControlPanel()
            } else {
                showControlPanel()
            }
        }
    }

    private fun showControlPanel() {
        if (controlPanelView != null || !canDrawOverlays()) return

        val layoutType = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY
        } else {
            @Suppress("DEPRECATION")
            WindowManager.LayoutParams.TYPE_PHONE
        }

        val params = WindowManager.LayoutParams(
            dpToPx(340),
            WindowManager.LayoutParams.WRAP_CONTENT,
            layoutType,
            WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or WindowManager.LayoutParams.FLAG_WATCH_OUTSIDE_TOUCH,
            PixelFormat.TRANSLUCENT
        ).apply {
            gravity = Gravity.CENTER
        }

        val panel = buildControlPanelView()
        controlPanelView = panel

        try {
            windowManager.addView(panel, params)
            isPanelOpen = true
            Log.i(TAG, "Contextual Control Panel opened.")
        } catch (e: Exception) {
            Log.e(TAG, "Failed to display Contextual Control Panel", e)
        }
    }

    private fun dismissControlPanel() {
        controlPanelView?.let { panel ->
            try {
                windowManager.removeView(panel)
            } catch (e: Exception) {
                Log.w(TAG, "Error removing control panel view", e)
            }
            controlPanelView = null
            isPanelOpen = false
            Log.i(TAG, "Contextual Control Panel dismissed.")
        }
    }

    /**
     * Builds the Contextual Control Panel per PRD v1.1 §13.5:
     * - Current operating state
     * - Active profile boundary
     * - Instant Pause/Resume, Mute/Unmute, and Stop controls
     * - Separate real-time FPS instrumentation (Capture, Upload, Ingest, Analysis)
     * - Timeline continuity gap tracker
     */
    private fun buildControlPanelView(): View {
        val root = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(COLOR_BG_GRAPHITE)
            setPadding(dpToPx(18), dpToPx(18), dpToPx(18), dpToPx(18))
            layoutParams = ViewGroup.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.WRAP_CONTENT
            )
        }

        // Header: Profile & Status
        val header = LinearLayout(context).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        val title = TextView(context).apply {
            text = "$activeProfileName Companion"
            setTextColor(COLOR_TEXT_PRIMARY)
            textSize = 18f
            typeface = android.graphics.Typeface.DEFAULT_BOLD
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1.0f)
        }
        val closeBtn = Button(context).apply {
            text = "✕"
            setTextColor(COLOR_TEXT_SECONDARY)
            setBackgroundColor(Color.TRANSPARENT)
            setOnClickListener { dismissControlPanel() }
        }
        header.addView(title)
        header.addView(closeBtn)
        root.addView(header)

        // Status Banner
        val statusText = TextView(context).apply {
            text = "State: ${currentStatus.name} • ${if (isAudioMuted) "Audio Muted" else "Audio Active"}"
            setTextColor(COLOR_AMBER_GLOW)
            textSize = 13f
            setPadding(0, dpToPx(4), 0, dpToPx(12))
        }
        root.addView(statusText)

        // Real-time Instrumentation Card
        val metricsCard = LinearLayout(context).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(COLOR_SURFACE_CARD)
            setPadding(dpToPx(12), dpToPx(12), dpToPx(12), dpToPx(12))
        }
        val metricsTitle = TextView(context).apply {
            text = "PERFORMANCE INSTRUMENTATION (PRD §5.3)"
            setTextColor(COLOR_VIOLET_ACCENT)
            textSize = 11f
            typeface = android.graphics.Typeface.DEFAULT_BOLD
        }
        metricsCard.addView(metricsTitle)

        val latestMetrics = MediaProjectionService.metrics.value
        val fpsText = TextView(context).apply {
            text = String.format(
                "Capture: %.1f fps  |  Upload: %.1f fps\nIngest: %.1f fps   |  Analysis: %.1f fps",
                latestMetrics.captureFps,
                latestMetrics.uploadFps,
                latestMetrics.ingestFps,
                latestMetrics.analysisFps
            )
            setTextColor(COLOR_TEXT_PRIMARY)
            textSize = 13f
            setPadding(0, dpToPx(6), 0, dpToPx(6))
        }
        metricsCard.addView(fpsText)

        val gapsText = TextView(context).apply {
            val gap = latestMetrics.lastGap
            text = if (gap == null) {
                "Continuity: Uninterrupted (0 gaps detected)"
            } else {
                "Continuity Warning: Gap of ${gap.durationMs}ms at seq ${gap.startSequence}..${gap.endSequence}"
            }
            setTextColor(if (gap == null) COLOR_STATUS_ACTIVE else COLOR_STATUS_PAUSED)
            textSize = 12f
        }
        metricsCard.addView(gapsText)
        root.addView(metricsCard)

        // Quick Action Buttons Row
        val actionsRow = LinearLayout(context).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER
            setPadding(0, dpToPx(14), 0, dpToPx(6))
        }

        val pauseResumeBtn = Button(context).apply {
            text = if (currentStatus == AwarenessStatus.PAUSED) "Resume" else "Pause"
            setTextColor(COLOR_TEXT_PRIMARY)
            setBackgroundColor(COLOR_SURFACE_CARD)
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1.0f)
            setOnClickListener {
                if (currentStatus == AwarenessStatus.PAUSED) {
                    activeService?.resumeScreen()
                } else {
                    activeService?.pauseScreen()
                }
                dismissControlPanel()
            }
        }
        actionsRow.addView(pauseResumeBtn)

        val muteBtn = Button(context).apply {
            text = if (isAudioMuted) "Unmute" else "Mute"
            setTextColor(COLOR_TEXT_PRIMARY)
            setBackgroundColor(COLOR_SURFACE_CARD)
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1.0f)
            setOnClickListener {
                if (isAudioMuted) {
                    activeService?.unmuteAudio()
                } else {
                    activeService?.muteAudio()
                }
                dismissControlPanel()
            }
        }
        actionsRow.addView(muteBtn)

        val stopBtn = Button(context).apply {
            text = "Stop"
            setTextColor(Color.WHITE)
            setBackgroundColor(COLOR_STATUS_REVOKED)
            layoutParams = LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1.0f)
            setOnClickListener {
                activeService?.stopAwarenessSession()
                dismissControlPanel()
            }
        }
        actionsRow.addView(stopBtn)

        root.addView(actionsRow)
        return root
    }

    fun updateState(status: AwarenessStatus) {
        this.currentStatus = status
        mainHandler.post {
            pillView?.invalidate()
        }
    }

    fun updateAudioMuted(muted: Boolean) {
        this.isAudioMuted = muted
        mainHandler.post {
            pillView?.invalidate()
        }
    }

    fun dismiss() {
        mainHandler.post {
            dismissControlPanel()
            pillView?.let { view ->
                try {
                    windowManager.removeView(view)
                } catch (e: Exception) {
                    Log.w(TAG, "Error removing pill view", e)
                }
                pillView = null
            }
        }
    }

    private fun canDrawOverlays(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            Settings.canDrawOverlays(context)
        } else {
            true
        }
    }

    private fun dpToPx(dp: Int): Int {
        val density = context.resources.displayMetrics.density
        return (dp * density).toInt()
    }
}
