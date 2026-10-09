package com.keyboardsounds.app

import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.provider.Settings
import android.text.TextUtils
import android.widget.SeekBar
import androidx.appcompat.app.AppCompatActivity
import androidx.preference.PreferenceManager
import com.google.android.material.chip.Chip
import com.keyboardsounds.app.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private lateinit var previewSoundManager: SoundManager

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        previewSoundManager = SoundManager(this)

        setupUI()
    }

    override fun onResume() {
        super.onResume()
        updateServiceStatus()
    }

    private fun setupUI() {
        val prefs = PreferenceManager.getDefaultSharedPreferences(this)

        // Status Button
        binding.btnEnableService.setOnClickListener {
            val intent = Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
            startActivity(intent)
        }

        // Profile Selection
        val savedProfile = prefs.getString("selected_profile", "Cream") ?: "Cream"
        previewSoundManager.loadProfile(savedProfile)

        when (savedProfile) {
            "Cream" -> binding.chipCream.isChecked = true
            "Cherry MX Red" -> binding.chipCherryRed.isChecked = true
            "Cherry MX Brown" -> binding.chipCherryBrown.isChecked = true
            "Holy Panda" -> binding.chipHolyPanda.isChecked = true
            "Kailh Box White" -> binding.chipKailhWhite.isChecked = true
            "Tealios V2" -> binding.chipTealios.isChecked = true
            "Buckling Spring" -> binding.chipBuckling.isChecked = true
            "Crystal Purple" -> binding.chipCrystalPurple.isChecked = true
            "Japanese Black" -> binding.chipJapaneseBlack.isChecked = true
            "Milky Yellow" -> binding.chipMilkyYellow.isChecked = true
            "Oreo" -> binding.chipOreo.isChecked = true
            "Super Red" -> binding.chipSuperRed.isChecked = true
            "Cardboard" -> binding.chipCardboard.isChecked = true
            else -> binding.chipCream.isChecked = true
        }

        binding.chipGroupProfiles.setOnCheckedStateChangeListener { group, checkedIds ->
            if (checkedIds.isEmpty()) return@setOnCheckedStateChangeListener
            val selectedChip = group.findViewById<Chip>(checkedIds.first()) ?: return@setOnCheckedStateChangeListener

            val profileFolder = when (selectedChip.id) {
                R.id.chipCream -> "Cream"
                R.id.chipCherryRed -> "Cherry MX Red"
                R.id.chipCherryBrown -> "Cherry MX Brown"
                R.id.chipHolyPanda -> "Holy Panda"
                R.id.chipKailhWhite -> "Kailh Box White"
                R.id.chipTealios -> "Tealios V2"
                R.id.chipBuckling -> "Buckling Spring"
                R.id.chipCrystalPurple -> "Crystal Purple"
                R.id.chipJapaneseBlack -> "Japanese Black"
                R.id.chipMilkyYellow -> "Milky Yellow"
                R.id.chipOreo -> "Oreo"
                R.id.chipSuperRed -> "Super Red"
                R.id.chipCardboard -> "Cardboard"
                else -> "Cream"
            }

            prefs.edit().putString("selected_profile", profileFolder).apply()
            previewSoundManager.loadProfile(profileFolder)
            previewSoundManager.playKeyDown()
        }

        // Volume SeekBar
        val savedVolume = prefs.getInt("volume_percent", 85)
        binding.seekBarVolume.progress = savedVolume
        binding.tvVolumePercent.text = "$savedVolume%"
        previewSoundManager.volume = savedVolume / 100f

        binding.seekBarVolume.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {
                binding.tvVolumePercent.text = "$progress%"
                previewSoundManager.volume = progress / 100f
            }

            override fun onStartTrackingTouch(seekBar: SeekBar?) {}

            override fun onStopTrackingTouch(seekBar: SeekBar?) {
                val vol = seekBar?.progress ?: 85
                prefs.edit().putInt("volume_percent", vol).apply()
                previewSoundManager.playKeyDown()
            }
        })

        // Haptics Switch
        val savedHaptics = prefs.getBoolean("haptics_enabled", true)
        binding.switchHaptics.isChecked = savedHaptics
        binding.switchHaptics.setOnCheckedChangeListener { _, isChecked ->
            prefs.edit().putBoolean("haptics_enabled", isChecked).apply()
        }

        // Test Typing Field
        binding.etTestTyping.addTextChangedListener(object : android.text.TextWatcher {
            private var lastLen = 0
            private var lastBackspaceTime = 0L

            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {
                lastLen = s?.length ?: 0
            }
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
                if (!TypingAccessibilityService.isServiceRunning) {
                    val newLen = s?.length ?: 0
                    val now = System.currentTimeMillis()
                    if (newLen > lastLen) {
                        lastBackspaceTime = 0L
                        previewSoundManager.playKeyDown()
                    } else if (newLen < lastLen) {
                        if (now - lastBackspaceTime >= 450L) {
                            previewSoundManager.playBackspace()
                        }
                        lastBackspaceTime = now
                    }
                }
            }
            override fun afterTextChanged(s: android.text.Editable?) {}
        })
    }

    private fun updateServiceStatus() {
        try {
            val isEnabled = isAccessibilityServiceEnabled(this, TypingAccessibilityService::class.java)
            val indicatorDrawable = binding.statusIndicator.background as? GradientDrawable

            if (isEnabled) {
                binding.tvServiceStatus.text = getString(R.string.service_status_enabled)
                binding.tvServiceStatus.setTextColor(getColor(R.color.accent_green))
                binding.tvStatusHelp.text = "Keyboard Sounds is active and playing sounds on your phone keyboard!"
                binding.btnEnableService.text = "Service is Active (Tap to Open Settings)"
                binding.btnEnableService.backgroundTintList = android.content.res.ColorStateList.valueOf(Color.parseColor("#1F2937"))
                indicatorDrawable?.setColor(getColor(R.color.accent_green))
            } else {
                binding.tvServiceStatus.text = getString(R.string.service_status_disabled)
                binding.tvServiceStatus.setTextColor(getColor(R.color.accent_red))
                binding.tvStatusHelp.text = "To hear sounds while typing in any app, enable Keyboard Sounds in your phone's Accessibility Settings."
                binding.btnEnableService.text = getString(R.string.enable_service_btn)
                binding.btnEnableService.backgroundTintList = android.content.res.ColorStateList.valueOf(getColor(R.color.accent_green))
                indicatorDrawable?.setColor(getColor(R.color.accent_red))
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun isAccessibilityServiceEnabled(context: Context, serviceClass: Class<*>): Boolean {
        val expectedFullName = "${context.packageName}/${serviceClass.name}"
        val expectedShortName = "${context.packageName}/.${serviceClass.simpleName}"
        val enabledServices = Settings.Secure.getString(
            context.contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES
        ) ?: return false

        val colonSplitter = TextUtils.SimpleStringSplitter(':')
        colonSplitter.setString(enabledServices)

        while (colonSplitter.hasNext()) {
            val componentName = colonSplitter.next()
            if (componentName.equals(expectedFullName, ignoreCase = true) ||
                componentName.equals(expectedShortName, ignoreCase = true)) {
                return true
            }
        }
        return false
    }

    override fun onDestroy() {
        super.onDestroy()
        previewSoundManager.release()
    }
}
