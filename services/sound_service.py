# services/sound_service.py
import asyncio
import wave
from pathlib import Path
from typing import Optional

# Desktop: winsound
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

# Mobile: flet-audio
try:
    import flet_audio as fta
    HAS_FLET_AUDIO = True
except ImportError:
    HAS_FLET_AUDIO = False

import flet as ft

SOUNDS = {
    "bell":    {"name": "🔔 Колокольчик", "file": "bell.wav",    "premium": False},
    "chime":   {"name": "🎐 Перезвон",    "file": "chime.wav",   "premium": True},
    "digital": {"name": "📟 Цифровой",    "file": "digital.wav", "premium": True},
    "soft":    {"name": "🎵 Мягкий",      "file": "soft.wav",    "premium": True},
}


class SoundService:
    def __init__(self):
        self.sounds_dir = Path(__file__).parent.parent / "assets" / "sounds"
        self._page = None
        self._use_audio = False
        self._audios = {}

    def bind_page(self, page: ft.Page):
        """Привязка к page. На mobile создаёт flet_audio.Audio для каждого звука."""
        self._page = page
        platform = str(getattr(page, "platform", "")).lower()
        is_mobile = ("android" in platform) or ("ios" in platform)

        if is_mobile and HAS_FLET_AUDIO:
            self._use_audio = True
            for sid, info in SOUNDS.items():
                file = info.get("file")
                if not file:
                    continue
                # Относительный путь от assets_dir="assets"
                src = f"sounds/{file}"
                print(f"🔊 [bind] {sid} -> src={src}")
                try:
                    audio = fta.Audio(
                        src=src,
                        volume=1.0,
                        release_mode=fta.ReleaseMode.STOP,
                    )
                    self._audios[sid] = audio
                    page.services.append(audio)
                except Exception as ex:
                    print(f"⚠ Не удалось создать Audio для {sid}: {ex}")
            try:
                page.update()
            except Exception:
                pass
        elif is_mobile and not HAS_FLET_AUDIO:
            print("⚠ flet-audio не установлен — звук на mobile недоступен")

    def play(self, sound_id: Optional[str] = None):
        if sound_id is None or sound_id not in SOUNDS:
            sound_id = "bell"
        file = SOUNDS[sound_id].get("file")
        if not file:
            return

        # Mobile: через flet_audio (асинхронно)
        if self._use_audio and self._page:
            audio = self._audios.get(sound_id)
            if audio:
                try:
                    asyncio.create_task(audio.play())
                except Exception as ex:
                    print(f"⚠ Audio.play error: {ex}")
            return

        # Desktop: через winsound
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
            print(f"🔊 [no-backend] {file}")

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