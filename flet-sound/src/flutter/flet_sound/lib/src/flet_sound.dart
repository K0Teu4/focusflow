import 'package:flet/flet.dart';
import 'package:flutter/services.dart';

class FletSoundService extends FletService {
  FletSoundService({required super.control});

  static const MethodChannel _channel = MethodChannel('flet_sound');

  @override
  void init() {
    super.init();
    control.addInvokeMethodListener(_onInvokeMethod);
  }

  Future<dynamic> _onInvokeMethod(String name, dynamic args) async {
    if (name == "play") {
      final soundId = args["sound"] as String? ?? "bell";
      try {
        await _channel.invokeMethod("play", {"sound": soundId});
      } on PlatformException catch (e) {
        print("[FletSound] play error: ${e.code} ${e.message}");
      }
    }
  }

  @override
  void dispose() {
    control.removeInvokeMethodListener(_onInvokeMethod);
    super.dispose();
  }
}