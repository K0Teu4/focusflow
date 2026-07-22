# services/sound_service.py
import winsound
import wave
from pathlib import Path
from typing import Optional

SOUNDS = {
    "bell": {
        "name": "🔔 Колокольчик",
        "file": "bell.wav",
        "premium": False,
    },
    "chime": {
        "name": "🎐 Перезвон",
        "file": "chime.wav",
        "premium": True,
    },
    "digital": {
        "name": "📟 Цифровой",
        "file": "digital.wav",
        "premium": True,
    },
    "soft": {
        "name": "🎵 Мягкий",
        "file": "soft.wav",
        "premium": True,
    },
    # "none" убран — беззвучный режим теперь через Switch "Звук при завершении"
}


class SoundService:
    def __init__(self):
        self.sounds_dir = Path(__file__).parent.parent / "assets" / "sounds"

    def play(self, sound_id: Optional[str] = None):
        if sound_id is None or sound_id not in SOUNDS:
            sound_id = "bell"

        sound_info = SOUNDS.get(sound_id, SOUNDS["bell"])
        file_name = sound_info.get("file")

        if not file_name:
            return

        sound_path = self.sounds_dir / file_name
        if not sound_path.exists():
            self._fallback()
            return

        if not self._is_valid_wav(sound_path):
            print(f"⚠ {file_name}: несовместимый формат, нужен PCM WAV")
            self._fallback()
            return

        try:
            winsound.PlaySound(
                str(sound_path),
                winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT,
            )
        except Exception as e:
            print(f"⚠ Ошибка воспроизведения {file_name}: {e}")
            self._fallback()

    def _fallback(self):
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
        sound_info = SOUNDS.get(sound_id, SOUNDS["bell"])
        file_name = sound_info.get("file")
        if not file_name:
            return None
        return self.sounds_dir / file_name

    def diagnose_sound(self, sound_id: str) -> dict:
        sound_info = SOUNDS.get(sound_id, SOUNDS["bell"])
        file_name = sound_info.get("file")
        result = {
            "id": sound_id,
            "name": sound_info.get("name"),
            "premium": sound_info.get("premium"),
            "file": file_name,
        }

        if not file_name:
            result["status"] = "no_file"
            return result

        path = self.sounds_dir / file_name
        result["path"] = str(path)
        result["exists"] = path.exists()

        if not path.exists():
            result["status"] = "not_found"
            return result

        result["size_kb"] = round(path.stat().st_size / 1024, 1)

        try:
            with wave.open(str(path), "rb") as w:
                result["channels"] = w.getnchannels()
                result["sample_width"] = w.getsampwidth()
                result["framerate"] = w.getframerate()
                result["frames"] = w.getnframes()
                result["duration_sec"] = round(w.getnframes() / w.getframerate(), 2)
                result["comptype"] = w.getcomptype()
                result["is_pcm"] = w.getcomptype() == "NONE"
                result["is_valid"] = self._is_valid_wav(path)
                result["status"] = "ok" if result["is_valid"] else "invalid_format"
        except wave.Error as e:
            result["status"] = f"not_wav: {e}"
            result["is_valid"] = False
        except Exception as e:
            result["status"] = f"error: {e}"
            result["is_valid"] = False

        return result

    @staticmethod
    def get_all_sounds(is_premium: bool = False) -> dict:
        result = {}
        for sid, info in SOUNDS.items():
            if info["premium"] and not is_premium:
                result[sid] = f"🔒 {info['name']} (Premium)"
            else:
                result[sid] = info["name"]
        return result

    @staticmethod
    def is_premium_required(sound_id: str) -> bool:
        return SOUNDS.get(sound_id, {}).get("premium", False)