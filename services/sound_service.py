# services/sound_service.py
import wave
from pathlib import Path
from typing import Optional
import flet as ft

# Desktop: winsound (работает на Windows)
try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False

# Mobile: нативный звук через Flet-extension (Kotlin MediaPlayer).
# В Flet 0.85.3 нет ft.Audio, поэтому мобильный звук идёт только через extension.
# На десктопе пакет может быть не установлен — это нормально, там winsound.
try:
    from flet_sound import FletSound
    HAS_FLET_SOUND = True
except ImportError:
    HAS_FLET_SOUND = False

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
        self._flet_sound = None   # экземпляр FletSound на mobile (None на desktop)

    def bind_page(self, page: ft.Page):
        """Привязка к page. Desktop -> winsound (ничего не регистрируем).
        Mobile -> FletSound-сервис (один раз на page, защита от смены темы)."""
        self._page = page
        platform = str(getattr(page, "platform", "")).lower()
        is_mobile = ("android" in platform) or ("ios" in platform)
        print(f"[FF-SOUND] bind_page platform={platform!r} is_mobile={is_mobile}")

        # Desktop: winsound, extension не нужен
        if not is_mobile:
            return

        if not HAS_FLET_SOUND:
            print("[FF-SOUND] flet_sound extension не установлен — звук на mobile отключён")
            return

        # Защита от дубликатов: при смене темы экраны пересоздаются и bind_page
        # вызывается снова — переиспользуем уже зарегистрированный сервис.
        existing = getattr(page, "_ff_flet_sound", None)
        if existing is not None:
            self._flet_sound = existing
            print("[FF-SOUND] FletSound переиспользован из page")
            return

        try:
            svc = FletSound()
            page.services.append(svc)
            page._ff_flet_sound = svc
            self._flet_sound = svc
            try:
                page.update()
            except Exception:
                pass
            print("[FF-SOUND] FletSound сервис зарегистрирован")
        except Exception as ex:
            print(f"[FF-SOUND] не удалось зарегистрировать FletSound: {ex!r}")
            self._flet_sound = None

    # ------------------------------------------------------------------ #
    def play(self, sound_id: Optional[str] = None):
        if sound_id is None or sound_id not in SOUNDS:
            sound_id = "bell"
        file = SOUNDS[sound_id].get("file")
        if not file:
            return

        # Mobile: через FletSound (Python _invoke_method -> Dart -> Kotlin MediaPlayer)
        if self._flet_sound is not None and self._page is not None:
            try:
                self._flet_sound.play(sound_id)
                print(f"[FF-SOUND] play({sound_id}) через FletSound")
            except Exception as ex:
                print(f"[FF-SOUND] FletSound.play error: {ex!r}")
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
            print(f"[FF-SOUND] mobile-no-audio fallback for {file}")

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