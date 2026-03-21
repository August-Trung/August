from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from futureos.config import settings
from futureos.models import UserContext

SESSIONS_FILE = Path("data/sessions.json")
ACTIVE_SESSION_FILE = Path("data/active_session.txt")


@dataclass
class SessionRecord:
    session_id: str
    user: UserContext
    created_at: datetime
    expires_at: datetime
    revoked: bool
    sensitive_events: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user": self.user.model_dump(),
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "revoked": self.revoked,
            "sensitive_events": self.sensitive_events,
        }

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "SessionRecord":
        return SessionRecord(
            session_id=str(data["session_id"]),
            user=UserContext.model_validate(data["user"]),
            created_at=_parse_dt(str(data["created_at"])),
            expires_at=_parse_dt(str(data["expires_at"])),
            revoked=bool(data.get("revoked", False)),
            sensitive_events=[str(x) for x in data.get("sensitive_events", [])],
        )


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, SessionRecord] = {}
        self._load()

    def create_session(self, user: UserContext) -> SessionRecord:
        now = _utcnow()
        record = SessionRecord(
            session_id=str(uuid.uuid4()),
            user=user,
            created_at=now,
            expires_at=now + timedelta(minutes=settings.session_ttl_minutes),
            revoked=False,
            sensitive_events=[],
        )
        self._sessions[record.session_id] = record
        self._save()
        self.set_active(record.session_id)
        return record

    def get(self, session_id: str) -> SessionRecord | None:
        self._cleanup_expired()
        record = self._sessions.get(session_id)
        if not record or record.revoked:
            return None
        if record.expires_at <= _utcnow():
            return None
        return record

    def list_active(self) -> list[SessionRecord]:
        self._cleanup_expired()
        return [s for s in self._sessions.values() if not s.revoked and s.expires_at > _utcnow()]

    def revoke(self, session_id: str) -> bool:
        record = self._sessions.get(session_id)
        if not record:
            return False
        record.revoked = True
        self._save()
        if self.get_active() == session_id:
            self.clear_active()
        return True

    def touch_sensitive(self, session_id: str) -> None:
        record = self._sessions.get(session_id)
        if not record:
            return
        record.sensitive_events.append(_utcnow().isoformat())
        self._save()

    def within_sensitive_rate_limit(self, session_id: str) -> bool:
        record = self._sessions.get(session_id)
        if not record:
            return False
        cutoff = _utcnow() - timedelta(seconds=settings.sensitive_rate_limit_window_sec)
        filtered = [x for x in record.sensitive_events if _parse_dt(x) >= cutoff]
        record.sensitive_events = filtered
        self._save()
        return len(filtered) < settings.sensitive_rate_limit_count

    def set_active(self, session_id: str) -> None:
        ACTIVE_SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        ACTIVE_SESSION_FILE.write_text(session_id, encoding="utf-8")

    def get_active(self) -> str | None:
        if not ACTIVE_SESSION_FILE.exists():
            return None
        sid = ACTIVE_SESSION_FILE.read_text(encoding="utf-8").strip()
        return sid if sid else None

    def clear_active(self) -> None:
        if ACTIVE_SESSION_FILE.exists():
            ACTIVE_SESSION_FILE.unlink(missing_ok=True)

    def _load(self) -> None:
        if not SESSIONS_FILE.exists():
            self._sessions = {}
            return
        try:
            data = json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
            self._sessions = {k: SessionRecord.from_dict(v) for k, v in data.items()}
        except Exception:
            self._sessions = {}

    def _save(self) -> None:
        SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        payload = {sid: rec.to_dict() for sid, rec in self._sessions.items()}
        SESSIONS_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _cleanup_expired(self) -> None:
        now = _utcnow()
        changed = False
        for record in self._sessions.values():
            if record.expires_at <= now and not record.revoked:
                record.revoked = True
                changed = True
        if changed:
            self._save()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _parse_dt(raw: str) -> datetime:
    return datetime.fromisoformat(raw)
