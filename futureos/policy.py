from __future__ import annotations

from pathlib import Path
from typing import Iterable

from futureos.models import Action, IntentType, PolicyDecision, Role, UserContext


def flatten_actions(actions: Iterable[Action]) -> list[Action]:
    flat: list[Action] = []
    for action in actions:
        if action.intent == IntentType.COMPOSITE:
            for step in action.args.get("steps", []):
                flat.extend(flatten_actions([Action.model_validate(step)]))
        else:
            flat.append(action)
    return flat


def evaluate_action(action: Action, user: UserContext) -> PolicyDecision:
    if action.intent == IntentType.UNKNOWN:
        return PolicyDecision(allowed=False, reason="Unknown intent is not executable.")

    if action.intent in {IntentType.SEND_ZALO, IntentType.SEND_BULK_EMAIL} and user.role == Role.GUEST:
        return PolicyDecision(allowed=False, reason="Guest cannot send external messages.")

    if action.intent == IntentType.SEND_BULK_EMAIL and user.role in {Role.USER, Role.GUEST}:
        return PolicyDecision(allowed=False, reason="Bulk email is restricted to owner/dev.")

    if action.intent in {
        IntentType.FILE_WRITE,
        IntentType.FILE_DELETE,
        IntentType.DIR_CREATE,
        IntentType.PATH_MOVE,
        IntentType.PATH_COPY,
        IntentType.PATH_RENAME,
        IntentType.PATH_ZIP,
    } and user.role == Role.GUEST:
        return PolicyDecision(allowed=False, reason="Guest cannot modify files.")

    for key in ["path", "src_path", "dst_path"]:
        path = action.args.get(key)
        if path:
            c_drive_decision = _check_c_drive_policy(path, action.intent, user)
            if c_drive_decision is not None:
                return c_drive_decision

    if action.intent in {IntentType.FILE_DELETE, IntentType.PATH_MOVE, IntentType.PATH_RENAME}:
        return PolicyDecision(
            allowed=True,
            reason="Destructive path operation allowed with confirmation.",
            needs_confirmation=True,
        )

    if action.intent in {IntentType.FILE_WRITE, IntentType.DIR_CREATE, IntentType.PATH_COPY, IntentType.PATH_ZIP}:
        return PolicyDecision(
            allowed=True,
            reason="Path write operation allowed with confirmation.",
            needs_confirmation=True,
        )

    # Force confirmation for risky outbound actions even when allowed.
    if action.intent in {IntentType.SEND_ZALO, IntentType.SEND_BULK_EMAIL}:
        return PolicyDecision(allowed=True, reason="Outbound action allowed with confirmation.", needs_confirmation=True)

    return PolicyDecision(allowed=True, reason="Allowed by role policy.")


def evaluate_plan(actions: list[Action], user: UserContext) -> tuple[bool, list[dict]]:
    checks: list[dict] = []
    allowed = True
    for action in flatten_actions(actions):
        decision = evaluate_action(action, user)
        checks.append(
            {
                "intent": action.intent.value,
                "allowed": decision.allowed,
                "reason": decision.reason,
                "needs_confirmation": decision.needs_confirmation,
            }
        )
        if not decision.allowed:
            allowed = False
    return allowed, checks


def should_confirm_from_policy(actions: list[Action], user: UserContext) -> bool:
    return any(evaluate_action(action, user).needs_confirmation for action in flatten_actions(actions))


def _check_c_drive_policy(path: str, intent: IntentType, user: UserContext) -> PolicyDecision | None:
    normalized = _normalize_path(path)
    if not normalized.startswith("c:\\"):
        return None

    if user.role == Role.DEV:
        return PolicyDecision(allowed=True, reason="Dev full access on C drive.")

    if user.role == Role.OWNER:
        if user.allow_c_drive_full:
            return PolicyDecision(allowed=True, reason="Owner enabled full C drive access.")
        if intent in {IntentType.FILE_DELETE, IntentType.PATH_MOVE, IntentType.PATH_RENAME}:
            return PolicyDecision(allowed=False, reason="Owner must enable full C access to delete in C drive.")
        return PolicyDecision(allowed=True, reason="Owner limited C drive access (non-delete).")

    if user.role == Role.USER:
        if intent in {IntentType.FILE_DELETE, IntentType.PATH_MOVE, IntentType.PATH_RENAME}:
            return PolicyDecision(allowed=False, reason="User cannot delete on C drive.")
        return PolicyDecision(allowed=True, reason="User has basic C drive access (non-delete).")

    if user.role == Role.GUEST:
        if intent in {
            IntentType.FILE_WRITE,
            IntentType.FILE_DELETE,
            IntentType.DIR_CREATE,
            IntentType.PATH_MOVE,
            IntentType.PATH_COPY,
            IntentType.PATH_RENAME,
            IntentType.PATH_ZIP,
        }:
            return PolicyDecision(allowed=False, reason="Guest cannot modify C drive.")
        return PolicyDecision(allowed=True, reason="Guest read-only access on C drive.")

    return None


def _normalize_path(path: str) -> str:
    try:
        p = str(Path(path))
    except Exception:
        p = path
    return p.strip().lower().replace("/", "\\")
