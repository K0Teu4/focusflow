# services/sound_service.py
import wave
from pathlib import Path
from typing import Optional

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

SOUNDS = {
    "bell":    {"name": "🔔 Колокольчик", "file": "bell.wav",    "premium": False},
    "chime":   {"name": "🎐 Перезвон",    "file": "chime.wav",   "premium": True},
    "digital": {"name": "📟 Цифровой",    "file": "digital.wav", "premium": True},
    "soft":    {"name": "🎵 Мягкий",      "file": "soft.wav",    "premium": True},
}


class SoundService:
    def __init__(self):
        self.sounds_dir = Path(__file__).parent.parent / "assets" / "sounds"

    def bind_page(self, page):
        """Заглушка: на mobile звук временно отключён (см. план сборки)."""
        pass

    def play(self, sound_id: Optional[str] = None):
        if sound_id is None or sound_id not in SOUNDS:
            sound_id = "bell"
        file = SOUNDS[sound_id].get("file")
        if not file:
            return

        if HAS_WINSOUND:
            sound_path = self.sounds_dir / file
            if sound_path.exists() and self._is_valid_wav(sound_path):
                try:
                    winsound.PlaySound(
                        str(sound_path),
                        winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
                    )
                    return
                except Exception:
                    pass
            self._fallback()
        else:
            # Mobile: звук будет добавлен через CI-сборку с flet-audio
            print(f"🔊 [mobile-stub] {file}")

    def _fallback(self):
        if not HAS_WINSOUND:
            return
        bell = self.sounds_dir / "bell.wav"
        if bell.exists() and self._is_valid_wav(bell):
            try:
                winsound.PlaySound(
                    str(bell),
                    winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
                )
                return
            except Exception:
                pass
        winsound.MessageBeep(winsound.MB_OK)

    @staticmethod
    def _is_valid_wav(path: Path) -> bool:
        try:
            with wave.open(str(path), "rb") as w:
                if w.getcomptype() != "NONE":
                    return False
                if w.getnchannels() not in (1, 2):
                    return False
                if w.getsampwidth() not in (1, 2):
                    return False
                return True
        except Exception:
            return False

    def play_bell(self):
        self.play("bell")

    def get_sound_file_path(self, sound_id: str) -> Optional[Path]:
        file = SOUNDS.get(sound_id, SOUNDS["bell"]).get("file")
        return (self.sounds_dir / file) if file else None

    def diagnose_sound(self, sound_id: str) -> dict:
        info = SOUNDS.get(sound_id, SOUNDS["bell"])
        file = info.get("file")
        result = {"id": sound_id, "name": info.get("name"),
                  "premium": info.get("premium"), "file": file}
        if not file:
            result["status"] = "no_file"
            return result
        path = self.sounds_dir / file
        result["path"] = str(path)
        result["exists"] = path.exists()
        if not path.exists():
            result["status"] = "not_found"
            return result
        result["size_kb"] = round(path.stat().st_size / 1024, 1)
        try:
            with wave.open(str(path), "rb") as w:
                result.update({
                    "channels": w.getnchannels(),
                    "sample_width": w.getsampwidth(),
                    "framerate": w.getframerate(),
                    "frames": w.getnframes(),
                    "duration_sec": round(w.getnframes() / w.getframerate(), 2),
                    "comptype": w.getcomptype(),
                    "is_pcm": w.getcomptype() == "NONE",
                    "is_valid": self._is_valid_wav(path),
                })
                result["status"] = "ok" if result["is_valid"] else "invalid_format"
        except Exception as e:
            result["status"] = f"error: {e}"
            result["is_valid"] = False
        return result

    @staticmethod
    def get_all_sounds(is_premium: bool = False) -> dict:
        result = {}
        for sid, info in SOUNDS.items():
            result[sid] = (f"🔒 {info['name']} (Premium)"
                           if info["premium"] and not is_premium else info["name"])
        return result

    @staticmethod
    def is_premium_required(sound_id: str) -> bool:
        return SOUNDS.get(sound_id, {}).get("premium", False)