from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from futureos.config import settings
from futureos.engine import execute_command, resolve_session
from futureos.safety import write_history
from futureos.session import SessionStore

QUEUE_FILE = Path("data/task_queue.json")
DEAD_LETTER_FILE = Path("data/dead_letter.jsonl")
PROCESSED_KEYS_FILE = Path("data/processed_keys.json")
WORKER_LOCK_FILE = Path("data/worker.lock")
WORKER_HEARTBEAT_FILE = Path("data/worker_heartbeat.json")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _dt(raw: str) -> datetime:
    return datetime.fromisoformat(raw)


@dataclass
class Task:
    id: str
    command: str
    session_id: str
    idempotency_key: str
    created_at: str
    available_at: str
    started_at: str
    retries: int
    max_retries: int
    timeout_seconds: int
    auto_confirm: bool
    status: str
    cancelled: bool
    last_error: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "command": self.command,
            "session_id": self.session_id,
            "idempotency_key": self.idempotency_key,
            "created_at": self.created_at,
            "available_at": self.available_at,
            "started_at": self.started_at,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "auto_confirm": self.auto_confirm,
            "status": self.status,
            "cancelled": self.cancelled,
            "last_error": self.last_error,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Task":
        return Task(
            id=str(data["id"]),
            command=str(data["command"]),
            session_id=str(data["session_id"]),
            idempotency_key=str(data.get("idempotency_key", "")),
            created_at=str(data["created_at"]),
            available_at=str(data["available_at"]),
            started_at=str(data.get("started_at", "")),
            retries=int(data.get("retries", 0)),
            max_retries=int(data.get("max_retries", settings.queue_max_retries)),
            timeout_seconds=int(data.get("timeout_seconds", settings.queue_task_timeout_seconds)),
            auto_confirm=bool(data.get("auto_confirm", False)),
            status=str(data.get("status", "queued")),
            cancelled=bool(data.get("cancelled", False)),
            last_error=str(data.get("last_error", "")),
        )


class TaskQueue:
    def __init__(self) -> None:
        self.path = QUEUE_FILE
        self.tasks: list[Task] = self._load()
        self.processed_keys = self._load_processed_keys()
        self._cleanup_processed_keys()

    def enqueue(
        self,
        command: str,
        session_id: str,
        auto_confirm: bool = False,
        max_retries: int | None = None,
        timeout_seconds: int | None = None,
        idempotency_key: str | None = None,
    ) -> Task:
        key = idempotency_key or _default_idempotency_key(command, session_id)
        existing = self.find_active_by_key(key)
        if existing is not None:
            return existing
        if key in self.processed_keys:
            # Same command was recently done. Return a synthetic task-shaped row.
            return Task(
                id="processed:" + key,
                command=command,
                session_id=session_id,
                idempotency_key=key,
                created_at=self.processed_keys[key],
                available_at=self.processed_keys[key],
                started_at=self.processed_keys[key],
                retries=0,
                max_retries=max_retries if max_retries is not None else settings.queue_max_retries,
                timeout_seconds=timeout_seconds if timeout_seconds is not None else settings.queue_task_timeout_seconds,
                auto_confirm=auto_confirm,
                status="already_processed",
                cancelled=False,
                last_error="idempotency key already processed",
            )

        task = Task(
            id=str(uuid.uuid4()),
            command=command,
            session_id=session_id,
            idempotency_key=key,
            created_at=_utcnow().isoformat(),
            available_at=_utcnow().isoformat(),
            started_at="",
            retries=0,
            max_retries=max_retries if max_retries is not None else settings.queue_max_retries,
            timeout_seconds=timeout_seconds if timeout_seconds is not None else settings.queue_task_timeout_seconds,
            auto_confirm=auto_confirm,
            status="queued",
            cancelled=False,
            last_error="",
        )
        self.tasks.append(task)
        self._save()
        return task

    def cancel(self, task_id: str) -> bool:
        for task in self.tasks:
            if task.id == task_id and task.status in {"queued", "processing"}:
                task.cancelled = True
                task.status = "cancelled"
                self._save()
                return True
        return False

    def list_all(self) -> list[Task]:
        return list(self.tasks)

    def find_active_by_key(self, idempotency_key: str) -> Task | None:
        for task in self.tasks:
            if task.idempotency_key == idempotency_key and task.status in {"queued", "processing"}:
                return task
        return None

    def pop_ready(self) -> Task | None:
        now = _utcnow()
        self._requeue_timed_out_processing(now)
        for task in self.tasks:
            if task.status != "queued":
                continue
            if task.cancelled:
                task.status = "cancelled"
                continue
            if _dt(task.available_at) <= now:
                task.status = "processing"
                task.started_at = now.isoformat()
                self._save()
                return task
        self._save()
        return None

    def mark_done(self, task_id: str) -> None:
        now = _utcnow().isoformat()
        for task in self.tasks:
            if task.id == task_id:
                task.status = "done"
                if task.idempotency_key:
                    self.processed_keys[task.idempotency_key] = now
        self.tasks = [t for t in self.tasks if t.status not in {"done", "cancelled"}]
        self._save()
        self._save_processed_keys()

    def mark_retry_or_dead(self, task: Task, error: str) -> None:
        for row in self.tasks:
            if row.id != task.id:
                continue
            row.retries += 1
            row.last_error = error
            row.started_at = ""
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
        cancelled = sum(1 for t in self.tasks if t.status == "cancelled")
        return {"queued": queued, "processing": processing, "cancelled": cancelled}

    def _requeue_timed_out_processing(self, now: datetime) -> None:
        changed = False
        for task in self.tasks:
            if task.status != "processing" or not task.started_at:
                continue
            if _dt(task.started_at) + timedelta(seconds=task.timeout_seconds) < now:
                task.status = "queued"
                task.last_error = "processing timeout; requeued"
                task.started_at = ""
                task.available_at = now.isoformat()
                changed = True
        if changed:
            self._save()

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

    def _load_processed_keys(self) -> dict[str, str]:
        if not PROCESSED_KEYS_FILE.exists():
            return {}
        try:
            data = json.loads(PROCESSED_KEYS_FILE.read_text(encoding="utf-8"))
            return {str(k): str(v) for k, v in data.items()}
        except Exception:
            return {}

    def _save_processed_keys(self) -> None:
        PROCESSED_KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)
        PROCESSED_KEYS_FILE.write_text(json.dumps(self.processed_keys, ensure_ascii=False, indent=2), encoding="utf-8")

    def _cleanup_processed_keys(self) -> None:
        cutoff = _utcnow() - timedelta(minutes=settings.queue_idempotency_window_minutes)
        changed = False
        for key in list(self.processed_keys.keys()):
            try:
                if _dt(self.processed_keys[key]) < cutoff:
                    del self.processed_keys[key]
                    changed = True
            except Exception:
                del self.processed_keys[key]
                changed = True
        if changed:
            self._save_processed_keys()


class WorkerLock:
    def __init__(self) -> None:
        self.path = WORKER_LOCK_FILE
        self.hb_path = WORKER_HEARTBEAT_FILE
        self.holder = f"{os.getpid()}"
        self.acquired = False

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                ts = _dt(str(data.get("ts", "")))
                if _utcnow() - ts > timedelta(seconds=settings.worker_lock_ttl_seconds):
                    self.path.unlink(missing_ok=True)
                else:
                    return False
            except Exception:
                self.path.unlink(missing_ok=True)
        payload = {"holder": self.holder, "ts": _utcnow().isoformat()}
        self.path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        self.acquired = True
        self.heartbeat()
        return True

    def heartbeat(self) -> None:
        if not self.acquired:
            return
        now = _utcnow().isoformat()
        self.path.write_text(json.dumps({"holder": self.holder, "ts": now}, ensure_ascii=False), encoding="utf-8")
        self.hb_path.write_text(json.dumps({"holder": self.holder, "ts": now}, ensure_ascii=False), encoding="utf-8")

    def release(self) -> None:
        if self.acquired and self.path.exists():
            self.path.unlink(missing_ok=True)
        self.acquired = False


class BackgroundWorker:
    def __init__(self, queue: TaskQueue, session_store: SessionStore) -> None:
        self.queue = queue
        self.session_store = session_store
        self.lock = WorkerLock()

    def run_once(self) -> dict[str, Any]:
        task = self.queue.pop_ready()
        if task is None:
            return {"ok": True, "message": "No ready tasks."}
        if task.cancelled:
            self.queue.mark_done(task.id)
            return {"ok": True, "task_id": task.id, "message": "Task cancelled and removed."}

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
        if not self.lock.acquire():
            raise RuntimeError("Another worker instance appears to be running.")
        processed = 0
        try:
            while True:
                try:
                    out = self.run_once()
                except Exception as e:
                    write_history({"event": "worker_crash", "error": str(e)})
                    time.sleep(settings.worker_crash_backoff_seconds)
                    continue
                self.lock.heartbeat()
                if out.get("message") == "No ready tasks.":
                    time.sleep(settings.worker_poll_seconds)
                else:
                    processed += 1
                if stop_after is not None and processed >= stop_after:
                    break
        finally:
            self.lock.release()


def _default_idempotency_key(command: str, session_id: str) -> str:
    return f"{session_id}:{command.strip().lower()}"
