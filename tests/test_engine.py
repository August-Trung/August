from __future__ import annotations

import unittest

from futureos.engine import execute_command
from futureos.models import Role, UserContext
from futureos.session import SessionStore


class EngineTests(unittest.TestCase):
    def test_requires_confirmation_without_callback(self) -> None:
        store = SessionStore()
        rec = store.create_session(UserContext(role=Role.OWNER, allow_c_drive_full=False, actor="eng-owner"))
        out = execute_command(
            raw_text="xoa file",
            session_id=rec.session_id,
            user_ctx=rec.user,
            session_store=store,
            confirm_func=None,
        )
        self.assertFalse(out["ok"])
        self.assertTrue(out.get("needs_confirmation", False))


if __name__ == "__main__":
    unittest.main()
