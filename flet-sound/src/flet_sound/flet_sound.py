import flet as ft


@ft.control("flet_sound")
class FletSound(ft.Service):
    """Native sound playback service for Android (via Kotlin MediaPlayer)."""

    def play(self, sound_id: str = "bell"):
        """Play a sound by ID (bell, chime, digital, soft)."""
        self._invoke_method("play", {"sound": sound_id})