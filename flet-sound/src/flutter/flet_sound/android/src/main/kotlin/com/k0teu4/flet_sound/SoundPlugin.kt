package com.k0teu4.flet_sound

import android.content.Context
import android.media.MediaPlayer
import io.flutter.embedding.engine.plugins.FlutterPlugin
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import io.flutter.plugin.common.MethodChannel.MethodCallHandler
import io.flutter.plugin.common.MethodChannel.Result

class SoundPlugin : FlutterPlugin, MethodCallHandler {
    private lateinit var channel: MethodChannel
    private lateinit var context: Context
    private var mediaPlayer: MediaPlayer? = null

    override fun onAttachedToEngine(binding: FlutterPlugin.FlutterPluginBinding) {
        context = binding.applicationContext
        channel = MethodChannel(binding.binaryMessenger, "com.k0teu4.flet_sound/sound")
        channel.setMethodCallHandler(this)
    }

    override fun onMethodCall(call: MethodCall, result: Result) {
        when (call.method) {
            "play" -> {
                val soundId = call.argument<String>("sound") ?: "bell"
                playSound(soundId)
                result.success(null)
            }
            else -> result.notImplemented()
        }
    }

    private fun playSound(soundId: String) {
        val fileName = when (soundId) {
            "bell" -> "sounds/bell.wav"
            "chime" -> "sounds/chime.wav"
            "digital" -> "sounds/digital.wav"
            "soft" -> "sounds/soft.wav"
            else -> "sounds/bell.wav"
        }

        try {
            mediaPlayer?.release()
            mediaPlayer = MediaPlayer().apply {
                val assetFd = context.assets.openFd(fileName)
                setDataSource(assetFd.fileDescriptor, assetFd.startOffset, assetFd.length)
                assetFd.close()
                prepare()
                start()
                setOnCompletionListener { mp ->
                    mp.release()
                    mediaPlayer = null
                }
            }
        } catch (e: Exception) {
            println("[SoundPlugin] play error: ${e.message}")
        }
    }

    override fun onDetachedFromEngine(binding: FlutterPlugin.FlutterPluginBinding) {
        channel.setMethodCallHandler(null)
        mediaPlayer?.release()
        mediaPlayer = null
    }
}