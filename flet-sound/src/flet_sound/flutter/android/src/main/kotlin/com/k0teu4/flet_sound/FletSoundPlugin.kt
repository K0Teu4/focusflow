package com.k0teu4.flet_sound

import android.content.Context
import android.media.MediaPlayer
import io.flutter.embedding.engine.plugins.FlutterPlugin
import io.flutter.plugin.common.MethodCall
import io.flutter.plugin.common.MethodChannel
import io.flutter.plugin.common.MethodChannel.MethodCallHandler
import io.flutter.plugin.common.MethodChannel.Result
import java.io.File
import java.io.FileOutputStream

class FletSoundPlugin : FlutterPlugin, MethodCallHandler {
    private lateinit var channel: MethodChannel
    private lateinit var context: Context
    private var mediaPlayer: MediaPlayer? = null

    override fun onAttachedToEngine(flutterPluginBinding: FlutterPlugin.FlutterPluginBinding) {
        channel = MethodChannel(flutterPluginBinding.binaryMessenger, "flet_sound")
        channel.setMethodCallHandler(this)
        context = flutterPluginBinding.applicationContext
    }

    override fun onMethodCall(call: MethodCall, result: Result) {
        if (call.method == "play") {
            val soundId = call.argument<String>("sound") ?: "bell"
            val assetPath = "flutter_assets/assets/sounds/$soundId.wav"
            
            try {
                mediaPlayer?.stop()
                mediaPlayer?.release()
                
                val inputStream = context.assets.open(assetPath)
                val tempFile = File.createTempFile("ff_sound_", ".wav", context.cacheDir)
                tempFile.deleteOnExit()
                
                FileOutputStream(tempFile).use { output ->
                    inputStream.copyTo(output)
                }
                
                mediaPlayer = MediaPlayer().apply {
                    setDataSource(tempFile.absolutePath)
                    prepare()
                    start()
                    setOnCompletionListener {
                        release()
                        mediaPlayer = null
                        tempFile.delete()
                    }
                    setOnErrorListener { _, what, extra ->
                        release()
                        mediaPlayer = null
                        tempFile.delete()
                        true
                    }
                }
                result.success(true)
            } catch (e: Exception) {
                mediaPlayer?.release()
                mediaPlayer = null
                result.error("PLAY_ERROR", "Failed to play sound '$soundId': ${e.message}", null)
            }
        } else {
            result.notImplemented()
        }
    }

    override fun onDetachedFromEngine(binding: FlutterPlugin.FlutterPluginBinding) {
        channel.setMethodCallHandler(null)
        mediaPlayer?.release()
        mediaPlayer = null
    }
}