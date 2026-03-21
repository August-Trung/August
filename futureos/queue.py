from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from futureos.config import settings
from futureos.engine import execute_command, resolve_session
from futureos.safety import write_history
from futureos.session import SessionStore

QUEUE_FILE = Path("data/task_queue.json")
DEAD_LETTER_FILE = Path("data/dead_letter.jsonl")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Task:
    id: str
    command: str
    session_id: str
    created_at: str
    available_at: str
    retries: int
    max_retries: int
    auto_confirm: bool
    status: str
    last_error: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "command": self.command,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "available_at": self.available_at,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "auto_confirm": self.auto_confirm,
            "status": self.status,
            "last_error": self.last_error,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Task":
        return Task(
            id=str(data["id"]),
            command=str(data["command"]),
            session_id=str(data["session_id"]),
            created_at=str(data["created_at"]),
            available_at=str(data["available_at"]),
            retries=int(data.get("retries", 0)),
            max_retries=int(data.get("max_retries", settings.queue_max_retries)),
            auto_confirm=bool(data.get("auto_confirm", False)),
            status=str(data.get("status", "queued")),
            last_error=str(data.get("last_error", "")),
        )


class TaskQueue:
    def __init__(self) -> None:
        self.path = QUEUE_FILE
        self.tasks: list[Task] = self._load()

    def enqueue(self, command: str, session_id: str, auto_confirm: bool = False, max_retries: int | None = None) -> Task:
        task = Task(
            id=str(uuid.uuid4()),
            command=command,
            session_id=session_id,
            created_at=_utcnow().isoformat(),
            available_at=_utcnow().isoformat(),
            retries=0,
            max_retries=max_retries if max_retries is not None else settings.queue_max_retries,
            auto_confirm=auto_confirm,
            status="queued",
            last_error="",
        )
        self.tasks.append(task)
        self._save()
        return task

    def list_all(self) -> list[Task]:
        return list(self.tasks)

    def pop_ready(self) -> Task | None:
        now = _utcnow()
        for task in self.tasks:
            if task.status != "queued":
                continue
            if datetime.fromisoformat(task.available_at) <= now:
                task.status = "processing"
                self._save()
                return task
        return None

    def mark_done(self, task_id: str) -> None:
        for task in self.tasks:
            if task.id == task_id:
                task.status = "done"
        self.tasks = [t for t in self.tasks if t.status != "done"]
        self._save()

    def mark_retry_or_dead(self, task: Task, error: str) -> None:
        for row in self.tasks:
            if row.id != task.id:
                continue
            row.retries += 1
            row.last_error = error
            if row.retries > row.max_retries:
                row.status = "dead"
                self._append_dead_letter(row)
            else:
                row.status = "queued"
                delay = settings.queue_backoff_seconds * row.retries
                row.available_at = (_utcnow() + timedelta(seconds=delay)).isoformat()
        self.tasks = [t for t in self.tasks if t.status != "dead"]
        self._save()

    def stats(self) -> dict[str, int]:
        queued = sum(1 for t in self.tasks if t.status == "queued")
        processing = sum(1 for t in self.tasks if t.status == "processing")
        return {"queued": queued, "processing": processing}

    def _append_dead_letter(self, task: Task) -> None:
        DEAD_LETTER_FILE.parent.mkdir(parents=True, exist_ok=True)
        with DEAD_LETTER_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(task.to_dict(), ensure_ascii=False) + "\n")

    def _load(self) -> list[Task]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return [Task.from_dict(x) for x in data]
        except Exception:
            return []

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([t.to_dict() for t in self.tasks], ensure_ascii=False, indent=2), encoding="utf-8")


class BackgroundWorker:
    def __init__(self, queue: TaskQueue, session_store: SessionStore) -> None:
        self.queue = queue
        self.session_store = session_store

    def run_once(self) -> dict[str, Any]:
        task = self.queue.pop_ready()
        if task is None:
            return {"ok": True, "message": "No ready tasks."}

        sid, user_ctx = resolve_session(self.session_store, task.session_id)
        if not sid or not user_ctx:
            err = "Session missing/expired for queued task."
            self.queue.mark_retry_or_dead(task, err)
            write_history({"event": "task_failed", "task_id": task.id, "error": err})
            return {"ok": False, "task_id": task.id, "error": err}

        result = execute_command(
            raw_text=task.command,
            session_id=sid,
            user_ctx=user_ctx,
            session_store=self.session_store,
            confirm_func=(lambda: True) if task.auto_confirm else None,
        )
        if result.get("ok"):
            self.queue.mark_done(task.id)
            write_history({"event": "task_done", "task_id": task.id, "command": task.command})
            return {"ok": True, "task_id": task.id, "result": result}

        err = result.get("error", "Task execution failed.")
        self.queue.mark_retry_or_dead(task, err)
        write_history({"event": "task_failed", "task_id": task.id, "error": err})
        return {"ok": False, "task_id": task.id, "error": err}

    def run_loop(self, stop_after: int | None = None) -> None:
        processed = 0
        while True:
            out = self.run_once()
            if out.get("message") == "No ready tasks.":
                time.sleep(settings.worker_poll_seconds)
            else:
                processed += 1
            if stop_after is not None and processed >= stop_after:
                break
