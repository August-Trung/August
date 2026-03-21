from __future__ import annotations

import json
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

from openai import OpenAI

from futureos.config import settings

VOICE_PROFILE_FILE = Path("data/voice_profiles.json")


def _normalize_vi(text: str) -> str:
    t = text.strip().lower()
    # Remove accents to make wakeword robust to typed/unaccented input.
    t = "".join(ch for ch in unicodedata.normalize("NFD", t) if unicodedata.category(ch) != "Mn")
    return " ".join(t.split())


class VoiceProfileStore:
    def __init__(self) -> None:
        self.path = VOICE_PROFILE_FILE
        self.data = self._load()

    def enroll(self, actor: str, passphrase: str) -> None:
        self.data[actor] = {"passphrase_norm": _normalize_vi(passphrase)}
        self._save()

    def verify(self, actor: str, spoken_text: str) -> float:
        row = self.data.get(actor)
        if not row:
            return 0.0
        expected = row.get("passphrase_norm", "")
        actual = _normalize_vi(spoken_text)
        return SequenceMatcher(a=expected, b=actual).ratio()

    def _load(self) -> dict:
        if not self.path.exists():
            return {}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")


class VoiceEngine:
    def __init__(self) -> None:
        self.store = VoiceProfileStore()

    def wait_wakeword(self) -> bool:
        print(f"[Voice] Noi wakeword: '{settings.voice_wake_word}' (hoac go).")
        raw = input("> ").strip()
        return _normalize_vi(settings.voice_wake_word) in _normalize_vi(raw)

    def stt(self, audio_path: str | None = None) -> str:
        if settings.use_openai_stt and audio_path:
            try:
                client = OpenAI(api_key=settings.openai_api_key)
                with open(audio_path, "rb") as f:
                    resp = client.audio.transcriptions.create(model="gpt-4o-mini-transcribe", file=f)
                text = getattr(resp, "text", "") or ""
                if text:
                    return text.strip()
            except Exception:
                pass
        print("[Voice->Text] Nói lệnh (MVP dùng nhập tay):")
        return input("> ").strip()

    def tts(self, text: str) -> None:
        if settings.use_openai_tts and settings.openai_api_key:
            try:
                client = OpenAI(api_key=settings.openai_api_key)
                audio = client.audio.speech.create(
                    model="gpt-4o-mini-tts",
                    voice=settings.openai_tts_voice,
                    input=text,
                )
                out = Path("data/tts_last.mp3")
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(audio.read())
                print(f"[TTS] Da tao audio: {out}")
                return
            except Exception:
                pass
        print(f"[TTS] {text}")

    def enroll_actor_voice(self, actor: str, passphrase: str) -> None:
        self.store.enroll(actor, passphrase)

    def verify_actor_voice(self, actor: str, spoken_text: str) -> float:
        return self.store.verify(actor, spoken_text)

    def capture_passphrase(self) -> str:
        print("[Voice] Noi cau xac thuc (hoac go):")
        return input("> ").strip()
