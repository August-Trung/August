from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from futureos.config import settings
from futureos.models import Role, UserContext

AUTH_STATE_FILE = Path("data/auth_state.json")


def build_user_context(role_raw: str, allow_c_drive_full: bool, actor: str) -> UserContext:
    role = _parse_role(role_raw)
    effective_c_full = allow_c_drive_full and role == Role.OWNER
    return UserContext(role=role, allow_c_drive_full=effective_c_full, actor=actor)


def authenticate_login(
    role_raw: str,
    actor: str,
    allow_c_drive_full: bool,
    secret: str | None = None,
    voice_confidence: float | None = None,
) -> tuple[UserContext | None, str]:
    role = _parse_role(role_raw)
    state = _load_auth_state()

    locked, message = _is_locked(actor, state)
    if locked:
        return None, message

    if role == Role.OWNER:
        if not _is_high_confidence(voice_confidence) and (secret or "") != settings.owner_pin:
            _record_failure(actor, state)
            return None, "Owner authentication failed."
        _record_success(actor, state)
        return UserContext(role=Role.OWNER, allow_c_drive_full=allow_c_drive_full, actor=actor), "Authenticated as owner."

    if role == Role.DEV:
        if not settings.dev_secret:
            _record_failure(actor, state)
            return None, "DEV_SECRET is missing in environment."
        if not _is_high_confidence(voice_confidence) and (secret or "") != settings.dev_secret:
            _record_failure(actor, state)
            return None, "Dev authentication failed."
        _record_success(actor, state)
        return UserContext(role=Role.DEV, allow_c_drive_full=True, actor=actor), "Authenticated as dev."

    # user/guest are intentionally lower friction, but still tracked.
    _record_success(actor, state)
    if role == Role.USER:
        return UserContext(role=Role.USER, allow_c_drive_full=False, actor=actor), "Authenticated as user."
    return UserContext(role=Role.GUEST, allow_c_drive_full=False, actor=actor), "Authenticated as guest."


def resolve_interactive_identity() -> UserContext | None:
    print("Login role (owner/dev/user/guest):")
    role_raw = input("> ").strip().lower()
    print("Actor id:")
    actor = input("> ").strip() or "voice-user"
    print("Voice confidence 0..1 (optional, press enter to skip):")
    conf_raw = input("> ").strip()
    voice_conf = _try_float(conf_raw) if conf_raw else None
    secret = ""

    role = _parse_role(role_raw)
    if role == Role.OWNER:
        print("Owner PIN (required when confidence is low/empty):")
        secret = input("> ").strip()
    elif role == Role.DEV:
        print("Dev secret (required when confidence is low/empty):")
        secret = input("> ").strip()

    allow_c = False
    if role == Role.OWNER:
        print("Enable full C drive? (yes/no)")
        allow_c = input("> ").strip().lower() in {"yes", "y"}

    ctx, msg = authenticate_login(
        role_raw=role_raw,
        actor=actor,
        allow_c_drive_full=allow_c,
        secret=secret,
        voice_confidence=voice_conf,
    )
    print(msg)
    return ctx


def _is_high_confidence(confidence: float | None) -> bool:
    if confidence is None:
        return False
    return confidence >= settings.voice_confidence_threshold


def _parse_role(value: str) -> Role:
    try:
        return Role(value)
    except Exception:
        return Role.USER


def _try_float(raw: str) -> float | None:
    try:
        return float(raw)
    except Exception:
        return None


def _load_auth_state() -> dict[str, Any]:
    if not AUTH_STATE_FILE.exists():
        return {}
    try:
        return json.loads(AUTH_STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_auth_state(state: dict[str, Any]) -> None:
    AUTH_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    AUTH_STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _is_locked(actor: str, state: dict[str, Any]) -> tuple[bool, str]:
    row = state.get(actor, {})
    locked_until = row.get("locked_until")
    if not locked_until:
        return False, ""
    until = datetime.fromisoformat(locked_until)
    if until <= datetime.now(timezone.utc):
        row["locked_until"] = None
        row["failures"] = 0
        state[actor] = row
        _save_auth_state(state)
        return False, ""
    return True, f"Actor is locked until {until.isoformat()}."


def _record_failure(actor: str, state: dict[str, Any]) -> None:
    row = state.get(actor, {"failures": 0, "locked_until": None})
    row["failures"] = int(row.get("failures", 0)) + 1
    if row["failures"] >= settings.auth_max_failures:
        lock_until = datetime.now(timezone.utc) + timedelta(minutes=settings.auth_lock_minutes)
        row["locked_until"] = lock_until.isoformat()
    state[actor] = row
    _save_auth_state(state)


def _record_success(actor: str, state: dict[str, Any]) -> None:
    state[actor] = {"failures": 0, "locked_until": None}
    _save_auth_state(state)
