from __future__ import annotations

from futureos.config import settings


class VoiceEngine:
    """
    MVP voice bridge.
    Real engines (wakeword/STT/TTS/speaker verification) should replace these methods.
    """

    def wait_wakeword(self) -> bool:
        print(f"[Voice] Say wake word: '{settings.wake_word}' (or type it).")
        raw = input("> ").strip().lower()
        return raw == settings.wake_word.lower()

    def verify_owner(self) -> bool:
        print("[Voice] Owner verification required. Enter PIN:")
        raw = input("> ").strip()
        return raw == settings.owner_pin

    def stt(self) -> str:
        print("[Voice->Text] Speak command (type for MVP):")
        return input("> ").strip()

    def tts(self, text: str) -> None:
        print(f"[TTS] {text}")
