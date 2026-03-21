from __future__ import annotations

from typing import Callable

from futureos.models import Action, IntentType, UserContext
from futureos.policy import evaluate_plan, flatten_actions, should_confirm_from_policy
from futureos.router import route
from futureos.safety import should_require_confirmation, write_audit, write_history
from futureos.session import SessionStore
from futureos.workflows import execute_action


def is_sensitive(actions: list[Action]) -> bool:
    sensitive_intents = {
        IntentType.SEND_ZALO,
        IntentType.SEND_BULK_EMAIL,
        IntentType.FILE_DELETE,
        IntentType.FILE_WRITE,
    }
    return any(action.intent in sensitive_intents for action in flatten_actions(actions))


def resolve_session(session_store: SessionStore, required_session_id: str | None) -> tuple[str, UserContext] | tuple[None, None]:
    session_id = required_session_id or session_store.get_active()
    if not session_id:
        return None, None
    session = session_store.get(session_id)
    if session is None:
        return None, None
    return session_id, session.user


def execute_command(
    *,
    raw_text: str,
    session_id: str,
    user_ctx: UserContext,
    session_store: SessionStore,
    confirm_func: Callable[[], bool] | None = None,
) -> dict:
    plan = route(raw_text)
    actions: list[Action] = plan.actions
    if not actions:
        return {"ok": False, "error": "Khong co hanh dong nao duoc tao.", "plan": plan.model_dump(), "results": []}

    allowed, checks = evaluate_plan(actions, user_ctx)
    write_audit(
        {"event": "policy_check", "session_id": session_id, "user": user_ctx.model_dump(), "text": raw_text, "checks": checks}
    )
    if not allowed:
        write_history(
            {"event": "policy_denied", "session_id": session_id, "text": raw_text, "user": user_ctx.model_dump(), "checks": checks}
        )
        return {"ok": False, "error": "Policy denied this request.", "plan": plan.model_dump(), "policy": checks, "results": []}

    if is_sensitive(actions):
        if not session_store.within_sensitive_rate_limit(session_id):
            write_history({"event": "rate_limited", "session_id": session_id, "text": raw_text})
            return {"ok": False, "error": "Rate limit exceeded for sensitive actions.", "plan": plan.model_dump(), "policy": checks, "results": []}
        session_store.touch_sensitive(session_id)

    need_confirm = plan.needs_confirmation or should_require_confirmation(actions) or should_confirm_from_policy(actions, user_ctx)
    if need_confirm:
        if confirm_func is None:
            return {
                "ok": False,
                "error": "Confirmation required.",
                "plan": plan.model_dump(),
                "policy": checks,
                "needs_confirmation": True,
                "results": [],
            }
        if not confirm_func():
            write_history({"event": "cancelled", "session_id": session_id, "text": raw_text, "plan": plan.model_dump()})
            return {"ok": False, "error": "Cancelled by user.", "plan": plan.model_dump(), "policy": checks, "results": []}

    out = []
    for action in actions:
        result = execute_action(action)
        out.append(result.model_dump())
        write_history(
            {
                "event": "action_executed",
                "session_id": session_id,
                "text": raw_text,
                "action": action.model_dump(),
                "result": result.model_dump(),
            }
        )
    return {"ok": True, "plan": plan.model_dump(), "policy": checks, "results": out}
