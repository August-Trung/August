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

    def test_route_handles_user_sentence_variant(self) -> None:
        text = "tim file dư liueeju ở màn hình desk rồi vào ổ D tạo thư mục mới đặt tên tùy ý rồi di chuyển vào đó được không?"
        plan = route(text)
        intents = []
        for a in plan.actions:
            if a.intent.value == "composite":
                intents.extend([s.get("intent") for s in a.args.get("steps", [])])
            else:
                intents.append(a.intent.value)
        self.assertIn("file_search", intents)
        self.assertIn("dir_create", intents)
        self.assertIn("path_move", intents)

    def test_route_handles_unaccented_variant(self) -> None:
        text = "tim file du lieu o man hinh desk roi vao o d tao thu muc moi dat ten tuy y roi di chuyen vao do"
        plan = route(text)
        intents = []
        for a in plan.actions:
            if a.intent.value == "composite":
                intents.extend([s.get("intent") for s in a.args.get("steps", [])])
            else:
                intents.append(a.intent.value)
        self.assertEqual(intents[:3], ["file_search", "dir_create", "path_move"])


if __name__ == "__main__":
    unittest.main()
