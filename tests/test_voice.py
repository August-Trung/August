from __future__ import annotations

import unittest
from unittest.mock import patch

from futureos.voice import VoiceEngine, _normalize_vi


class VoiceTests(unittest.TestCase):
    def test_normalize_vi_removes_accents(self) -> None:
        self.assertEqual(_normalize_vi("Xin Chào  Future"), "xin chao future")

    def test_wakeword_match_with_unaccented_input(self) -> None:
        v = VoiceEngine()
        with patch("builtins.input", return_value="xin chao future"):
            self.assertTrue(v.wait_wakeword())

    def test_voice_profile_enroll_and_verify(self) -> None:
        v = VoiceEngine()
        actor = "voice-test-actor"
        v.enroll_actor_voice(actor, "Tôi là chủ máy")
        conf = v.verify_actor_voice(actor, "toi la chu may")
        self.assertGreaterEqual(conf, 0.9)


if __name__ == "__main__":
    unittest.main()
