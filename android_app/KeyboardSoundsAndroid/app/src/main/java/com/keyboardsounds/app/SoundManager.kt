package com.keyboardsounds.app

import android.content.Context
import android.content.res.AssetFileDescriptor
import android.media.AudioAttributes
import android.media.SoundPool
import android.util.Log
import java.io.IOException
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CopyOnWriteArrayList
import kotlin.random.Random

class SoundManager(private val context: Context) {

    private val tag = "KeyboardSounds"
    private var soundPool: SoundPool? = null

    private val keySounds = CopyOnWriteArrayList<Int>()
    private var spaceSoundId: Int? = null
    private var enterSoundId: Int? = null
    private var backspaceSoundId: Int? = null

    private val readySoundIds = ConcurrentHashMap.newKeySet<Int>()
    private var pendingPlay = false

    private var currentProfileFolder: String = "Cream"
    var volume: Float = 0.85f

    init {
        initSoundPool()
    }

    private fun initSoundPool() {
        val audioAttributes = AudioAttributes.Builder()
            .setUsage(AudioAttributes.USAGE_MEDIA)
            .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
            .build()

        soundPool = SoundPool.Builder()
            .setMaxStreams(32)
            .setAudioAttributes(audioAttributes)
            .build().apply {
                setOnLoadCompleteListener { _, sampleId, status ->
                    if (status == 0) {
                        readySoundIds.add(sampleId)
                        if (pendingPlay) {
                            pendingPlay = false
                            playKeyDown()
                        }
                    } else {
                        Log.w(tag, "Sample $sampleId failed to decode (status=$status)")
                    }
                }
            }
    }

    fun loadProfile(profileFolderName: String) {
        currentProfileFolder = profileFolderName
        val pool = soundPool ?: return

        keySounds.clear()
        readySoundIds.clear()
        spaceSoundId = null
        enterSoundId = null
        backspaceSoundId = null
        pendingPlay = false

        val assetManager = context.assets
        val subDirs = listOf("sounds/$profileFolderName/down", "sounds/$profileFolderName")

        for (dir in subDirs) {
            try {
                val files = assetManager.list(dir) ?: continue
                if (files.isEmpty()) continue

                for (fileName in files) {
                    if (!fileName.endsWith(".wav", ignoreCase = true) &&
                        !fileName.endsWith(".mp3", ignoreCase = true) &&
                        !fileName.endsWith(".ogg", ignoreCase = true)) {
                        continue
                    }

                    val filePath = "$dir/$fileName"
                    var afd: AssetFileDescriptor? = null
                    try {
                        afd = assetManager.openFd(filePath)
                        val soundId = pool.load(afd, 1)
                        keySounds.add(soundId)

                        val lower = fileName.lowercase()
                        when {
                            lower.contains("space") -> spaceSoundId = soundId
                            lower.contains("enter") || lower.contains("return") -> enterSoundId = soundId
                            lower.contains("backspace") || lower.contains("back") -> backspaceSoundId = soundId
                        }
                    } catch (e: IOException) {
                        Log.w(tag, "Failed to load audio asset: $filePath", e)
                    } finally {
                        try {
                            afd?.close()
                        } catch (_: Exception) {}
                    }
                }

                if (keySounds.isNotEmpty()) {
                    break
                }
            } catch (e: Exception) {
                Log.e(tag, "Error reading sounds directory: $dir", e)
            }
        }

        Log.i(tag, "Loaded profile [$profileFolderName] with ${keySounds.size} sounds.")
    }

    fun playKeyDown() {
        val available = keySounds.filter { readySoundIds.contains(it) }
        if (available.isEmpty()) {
            pendingPlay = true
            return
        }
        val soundId = available[Random.nextInt(available.size)]
        playSound(soundId)
    }

    fun playSpace() {
        val soundId = spaceSoundId?.takeIf { readySoundIds.contains(it) }
            ?: keySounds.firstOrNull { readySoundIds.contains(it) }
        soundId?.let { playSound(it) } ?: run { pendingPlay = true }
    }

    fun playEnter() {
        val soundId = enterSoundId?.takeIf { readySoundIds.contains(it) }
            ?: keySounds.firstOrNull { readySoundIds.contains(it) }
        soundId?.let { playSound(it) } ?: run { pendingPlay = true }
    }

    fun playBackspace() {
        val soundId = backspaceSoundId?.takeIf { readySoundIds.contains(it) }
            ?: keySounds.firstOrNull { readySoundIds.contains(it) }
        soundId?.let { playSound(it) } ?: run { pendingPlay = true }
    }

    private fun playSound(soundId: Int) {
        val pool = soundPool ?: return
        try {
            val streamId = pool.play(soundId, volume, volume, 1, 0, 1.0f)
            Log.i(tag, "playSound: id=$soundId, stream=$streamId, vol=$volume")
        } catch (e: Exception) {
            Log.e(tag, "Error playing sound: $soundId", e)
        }
    }

    fun release() {
        soundPool?.release()
        soundPool = null
        keySounds.clear()
        readySoundIds.clear()
    }
}
