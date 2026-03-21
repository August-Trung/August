from __future__ import annotations

import unittest

from futureos.models import Action, IntentType, Role, UserContext
from futureos.policy import evaluate_action


class PolicyTests(unittest.TestCase):
    def test_user_c_drive_delete_denied(self) -> None:
        action = Action(intent=IntentType.FILE_DELETE, args={"path": "C:\\tmp\\a.txt"})
        user = UserContext(role=Role.USER, allow_c_drive_full=False, actor="u")
        decision = evaluate_action(action, user)
        self.assertFalse(decision.allowed)

    def test_owner_c_drive_delete_needs_toggle(self) -> None:
        action = Action(intent=IntentType.FILE_DELETE, args={"path": "C:\\tmp\\a.txt"})
        owner = UserContext(role=Role.OWNER, allow_c_drive_full=False, actor="o")
        decision = evaluate_action(action, owner)
        self.assertFalse(decision.allowed)

    def test_dev_c_drive_delete_allowed(self) -> None:
        action = Action(intent=IntentType.FILE_DELETE, args={"path": "C:\\tmp\\a.txt"})
        dev = UserContext(role=Role.DEV, allow_c_drive_full=True, actor="d")
        decision = evaluate_action(action, dev)
        self.assertTrue(decision.allowed)

    def test_guest_bulk_email_denied(self) -> None:
        action = Action(intent=IntentType.SEND_BULK_EMAIL, args={"recipients": ["a@b.com"]})
        guest = UserContext(role=Role.GUEST, allow_c_drive_full=False, actor="g")
        decision = evaluate_action(action, guest)
        self.assertFalse(decision.allowed)


if __name__ == "__main__":
    unittest.main()
