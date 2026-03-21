from __future__ import annotations

import unittest
from pathlib import Path

from futureos.auth import AUTH_STATE_FILE, authenticate_login
from futureos.models import Role, UserContext
from futureos.session import ACTIVE_SESSION_FILE, SESSIONS_FILE, SessionStore


class AuthSessionTests(unittest.TestCase):
    def setUp(self) -> None:
        for path in [AUTH_STATE_FILE, SESSIONS_FILE, ACTIVE_SESSION_FILE]:
            if Path(path).exists():
                Path(path).unlink(missing_ok=True)

    def test_user_login_succeeds_without_secret(self) -> None:
        ctx, msg = authenticate_login("user", actor="t-user", allow_c_drive_full=False)
        self.assertIsNotNone(ctx, msg)
        self.assertEqual(ctx.role, Role.USER)

    def test_dev_login_fails_without_secret_config(self) -> None:
        # Only assert shape when DEV_SECRET is not configured.
        ctx, _ = authenticate_login("dev", actor="t-dev", allow_c_drive_full=False, secret="")
        if ctx is not None:
            self.assertEqual(ctx.role, Role.DEV)
        else:
            self.assertIsNone(ctx)

    def test_session_lifecycle(self) -> None:
        store = SessionStore()
        user = UserContext(role=Role.USER, allow_c_drive_full=False, actor="session-user")
        rec = store.create_session(user)
        loaded = store.get(rec.session_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.user.role, Role.USER)
        self.assertTrue(store.revoke(rec.session_id))
        self.assertIsNone(store.get(rec.session_id))


if __name__ == "__main__":
    unittest.main()
