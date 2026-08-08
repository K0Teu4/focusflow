import flet as ft

@ft.control("flet_sound")
class FletSound(ft.Service):
    def play(self, sound_id: str = "bell"):
        self._invoke_method("play", {"sound": sound_id})