import 'package:flet/flet.dart';
import 'flet_sound.dart';

class Extension extends FletExtension {
  @override
  FletService? createService(Control control) {
    switch (control.type) {
      case "flet_sound":
        return FletSoundService(control: control);
      default:
        return null;
    }
  }
}