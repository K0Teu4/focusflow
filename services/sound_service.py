# services/sound_service.py
import winsound
from pathlib import Path

class SoundService:
    def __init__(self):
        self.sounds_dir = Path(__file__).parent.parent / "assets" / "sounds"
        
    def play_bell(self):
        sound_path = self.sounds_dir / "bell.wav"
        if sound_path.exists():
            winsound.PlaySound(str(sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            winsound.MessageBeep(winsound.MB_OK)