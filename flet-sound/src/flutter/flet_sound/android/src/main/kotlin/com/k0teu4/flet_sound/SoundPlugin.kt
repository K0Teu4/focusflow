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
            // Flet помещает папку assets в flutter_assets внутри APK
            val assetPath = "flutter_assets/assets/sounds/$soundId.wav"
            
            try {
                // Останавливаем и освобождаем предыдущий плеер, если он есть
                mediaPlayer?.stop()
                mediaPlayer?.release()
                
                // Читаем файл из assets APK
                val inputStream = context.assets.open(assetPath)
                // Создаем временный файл в кэше приложения (MediaPlayer не умеет читать из assets напрямую)
                val tempFile = File.createTempFile("ff_sound_", ".wav", context.cacheDir)
                tempFile.deleteOnExit()
                
                FileOutputStream(tempFile).use { output ->
                    inputStream.copyTo(output)
                }
                
                // Настраиваем и запускаем воспроизведение
                mediaPlayer = MediaPlayer().apply {
                    setDataSource(tempFile.absolutePath)
                    prepare()
                    start()
                    setOnCompletionListener {
                        release()
                        mediaPlayer = null
                        // Очищаем временный файл после воспроизведения
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