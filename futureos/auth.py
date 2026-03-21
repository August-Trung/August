from __future__ import annotations

from futureos.config import settings
from futureos.models import Role, UserContext


def build_user_context(role_raw: str, allow_c_drive_full: bool, actor: str) -> UserContext:
    role = _parse_role(role_raw)
    # C drive full access flag is only meaningful for owner.
    effective_c_full = allow_c_drive_full and role == Role.OWNER
    return UserContext(role=role, allow_c_drive_full=effective_c_full, actor=actor)


def resolve_interactive_identity() -> UserContext | None:
    print("Login role (owner/dev/user/guest):")
    role_raw = input("> ").strip().lower()
    role = _parse_role(role_raw)
    if role == Role.OWNER:
        print("Enter owner PIN:")
        if input("> ").strip() != settings.owner_pin:
            return None
        return UserContext(role=Role.OWNER, allow_c_drive_full=False, actor="voice-owner")

    if role == Role.DEV:
        print("Enter dev secret:")
        if not settings.dev_secret or input("> ").strip() != settings.dev_secret:
            return None
        return UserContext(role=Role.DEV, allow_c_drive_full=True, actor="voice-dev")

    if role == Role.USER:
        return UserContext(role=Role.USER, allow_c_drive_full=False, actor="voice-user")
    return UserContext(role=Role.GUEST, allow_c_drive_full=False, actor="voice-guest")


def _parse_role(value: str) -> Role:
    try:
        return Role(value)
    except Exception:
        return Role.USER
