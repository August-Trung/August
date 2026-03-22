from __future__ import annotations

import unittest

from futureos.models import Action, IntentType
from futureos.router import route
from futureos.workflows import execute_action


class CoreFileOpsTests(unittest.TestCase):
    def test_vietnamese_create_and_move_plan(self) -> None:
        text = "tao thu muc zzz o desktop roi di chuyen vao thu muc backup trong o d"
        plan = route(text)
        self.assertEqual(len(plan.actions), 1)
        self.assertEqual(plan.actions[0].intent, IntentType.COMPOSITE)
        steps = plan.actions[0].args["steps"]
        intents = [s["intent"] for s in steps]
        self.assertIn("dir_create", intents)
        self.assertIn("path_move", intents)

    def test_dir_create_dry_run(self) -> None:
        action = Action(intent=IntentType.DIR_CREATE, args={"path": "D:\\backup\\zzz"})
        result = execute_action(action)
        self.assertTrue(result.ok)
        self.assertEqual(result.payload.get("mode"), "dry_run")

    def test_path_move_dry_run(self) -> None:
        action = Action(intent=IntentType.PATH_MOVE, args={"src_path": "D:\\a", "dst_path": "D:\\backup\\a"})
        result = execute_action(action)
        self.assertTrue(result.ok)
        self.assertEqual(result.payload.get("mode"), "dry_run")

    def test_path_zip_dry_run(self) -> None:
        action = Action(intent=IntentType.PATH_ZIP, args={"src_path": "D:\\a", "zip_path": "D:\\backup\\a.zip"})
        result = execute_action(action)
        self.assertTrue(result.ok)
        self.assertEqual(result.payload.get("mode"), "dry_run")


if __name__ == "__main__":
    unittest.main()
