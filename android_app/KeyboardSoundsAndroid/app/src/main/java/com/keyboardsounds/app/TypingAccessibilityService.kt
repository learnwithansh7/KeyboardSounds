package com.keyboardsounds.app

import android.accessibilityservice.AccessibilityService
import android.content.Context
import android.content.SharedPreferences
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import androidx.preference.PreferenceManager

class TypingAccessibilityService : AccessibilityService(), SharedPreferences.OnSharedPreferenceChangeListener {

    private val tag = "KeyboardSounds"
    private lateinit var soundManager: SoundManager
    private lateinit var prefs: SharedPreferences
    private var vibrator: Vibrator? = null

    private var isHapticsEnabled = true
    private var lastEventTime = 0L
    private var lastBackspaceTime = 0L
    private val backspaceHoldCooldownMs = 450L

    companion object {
        var isServiceRunning = false
            private set
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        isServiceRunning = true
        Log.i(tag, "TypingAccessibilityService onServiceConnected!")

        soundManager = SoundManager(this)
        prefs = PreferenceManager.getDefaultSharedPreferences(this)
        prefs.registerOnSharedPreferenceChangeListener(this)

        initVibrator()
        loadPreferences()
    }

    private fun initVibrator() {
        vibrator = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val vibratorManager = getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
            vibratorManager?.defaultVibrator
        } else {
            @Suppress("DEPRECATION")
            getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
        }
    }

    private fun loadPreferences() {
        val profileFolder = prefs.getString("selected_profile", "Cream") ?: "Cream"
        val volumePercent = prefs.getInt("volume_percent", 85)
        isHapticsEnabled = prefs.getBoolean("haptics_enabled", true)

        soundManager.volume = (volumePercent.coerceIn(0, 100) / 100f)
        soundManager.loadProfile(profileFolder)
        Log.i(tag, "Preferences reloaded: profile=$profileFolder, vol=$volumePercent%, haptics=$isHapticsEnabled")
    }

    override fun onSharedPreferenceChanged(sharedPreferences: SharedPreferences?, key: String?) {
        loadPreferences()
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event == null) return

        val eventType = event.eventType
        if (eventType != AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED &&
            eventType != AccessibilityEvent.TYPE_VIEW_CLICKED) {
            return
        }

        val now = System.currentTimeMillis()
        if (now - lastEventTime < 20) {
            return
        }

        if (eventType == AccessibilityEvent.TYPE_VIEW_TEXT_CHANGED) {
            val addedCount = event.addedCount
            val removedCount = event.removedCount
            val textList = event.text
            val currentText = textList?.joinToString("") ?: ""
            val beforeText = event.beforeText?.toString()

            Log.i(tag, "TextChanged: added=$addedCount, removed=$removedCount, text='$currentText'")

            when {
                addedCount > 0 -> {
                    lastBackspaceTime = 0L
                    val fromIndex = event.fromIndex
                    val toIndex = (fromIndex + addedCount).coerceAtMost(currentText.length)
                    val addedSegment = if (fromIndex in 0 until currentText.length && toIndex <= currentText.length) {
                        currentText.substring(fromIndex, toIndex)
                    } else {
                        ""
                    }

                    when {
                        addedSegment.contains("\n") -> soundManager.playEnter()
                        addedSegment.contains(" ") -> soundManager.playSpace()
                        else -> soundManager.playKeyDown()
                    }
                    performHapticClick()
                    lastEventTime = now
                }
                removedCount > 0 -> {
                    handleBackspace(now)
                }
                beforeText != null && currentText.length > beforeText.length -> {
                    lastBackspaceTime = 0L
                    soundManager.playKeyDown()
                    performHapticClick()
                    lastEventTime = now
                }
                beforeText != null && currentText.length < beforeText.length -> {
                    handleBackspace(now)
                }
                currentText.isNotEmpty() -> {
                    lastBackspaceTime = 0L
                    soundManager.playKeyDown()
                    performHapticClick()
                    lastEventTime = now
                }
            }
        } else if (eventType == AccessibilityEvent.TYPE_VIEW_CLICKED) {
            val pkg = event.packageName?.toString() ?: ""
            val cls = event.className?.toString() ?: ""
            if (pkg.contains("inputmethod", ignoreCase = true) ||
                pkg.contains("latin", ignoreCase = true) ||
                pkg.contains("keyboard", ignoreCase = true) ||
                cls.contains("keyboard", ignoreCase = true) ||
                cls.contains("key", ignoreCase = true)) {
                Log.i(tag, "Key Click: pkg=$pkg, cls=$cls")
                soundManager.playKeyDown()
                performHapticClick()
                lastEventTime = now
            }
        }
    }

    private fun handleBackspace(now: Long) {
        val timeSinceLast = now - lastBackspaceTime
        lastBackspaceTime = now

        // If backspace is being held down (burst of deletions within 450ms),
        // only sound ONCE on the initial press and suppress continuous machine-gun clicks
        if (timeSinceLast < backspaceHoldCooldownMs) {
            Log.d(tag, "Backspace repeat suppressed (held down): delta=${timeSinceLast}ms")
            return
        }

        soundManager.playBackspace()
        performHapticClick()
        lastEventTime = now
    }

    private fun performHapticClick() {
        if (!isHapticsEnabled) return
        val v = vibrator ?: return
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                v.vibrate(VibrationEffect.createPredefined(VibrationEffect.EFFECT_CLICK))
            } else {
                @Suppress("DEPRECATION")
                v.vibrate(15)
            }
        } catch (_: Exception) {
        }
    }

    override fun onInterrupt() {
    }

    override fun onDestroy() {
        super.onDestroy()
        isServiceRunning = false
        prefs.unregisterOnSharedPreferenceChangeListener(this)
        soundManager.release()
    }
}
