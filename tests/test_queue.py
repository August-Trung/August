from __future__ import annotations

import unittest
from pathlib import Path

from futureos.models import Role, UserContext
from futureos.queue import DEAD_LETTER_FILE, QUEUE_FILE, BackgroundWorker, TaskQueue
from futureos.session import ACTIVE_SESSION_FILE, SESSIONS_FILE, SessionStore


class QueueTests(unittest.TestCase):
    def setUp(self) -> None:
        for p in [QUEUE_FILE, DEAD_LETTER_FILE, SESSIONS_FILE, ACTIVE_SESSION_FILE]:
            Path(p).unlink(missing_ok=True)

    def test_enqueue_and_process_success(self) -> None:
        store = SessionStore()
        rec = store.create_session(UserContext(role=Role.OWNER, allow_c_drive_full=False, actor="q-owner"))
        queue = TaskQueue()
        worker = BackgroundWorker(queue, store)
        task = queue.enqueue("tim file o d", rec.session_id, auto_confirm=False, max_retries=1)
        self.assertEqual(queue.stats()["queued"], 1)
        out = worker.run_once()
        self.assertTrue(out["ok"])
        self.assertEqual(queue.stats()["queued"], 0)
        self.assertEqual(task.id, out["task_id"])

    def test_dead_letter_when_session_missing(self) -> None:
        queue = TaskQueue()
        store = SessionStore()
        worker = BackgroundWorker(queue, store)
        queue.enqueue("tim file o d", "missing-session-id", auto_confirm=False, max_retries=0)
        out = worker.run_once()
        self.assertFalse(out["ok"])
        self.assertTrue(Path(DEAD_LETTER_FILE).exists())


if __name__ == "__main__":
    unittest.main()
