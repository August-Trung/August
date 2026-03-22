from __future__ import annotations

import unittest

from futureos.nlu import normalize_text
from futureos.router import route


class NluTests(unittest.TestCase):
    def test_normalize_abbrev_and_typo(self) -> None:
        text = "tao tm zzz o desktp roi dc vao backup o d"
        norm = normalize_text(text)
        self.assertIn("thu muc", norm)
        self.assertIn("desktop", norm)
        self.assertIn("di chuyen", norm)

    def test_route_handles_abbrev_typo(self) -> None:
        text = "tao tm zzz o desktp roi dc vao backup o d"
        plan = route(text)
        intents = []
        for a in plan.actions:
            if a.intent.value == "composite":
                intents.extend([s.get("intent") for s in a.args.get("steps", [])])
            else:
                intents.append(a.intent.value)
        self.assertIn("dir_create", intents)
        self.assertIn("path_move", intents)


if __name__ == "__main__":
    unittest.main()
