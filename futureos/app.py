from __future__ import annotations

import json
from typing import Optional

import typer

from futureos.auth import authenticate_login, resolve_interactive_identity
from futureos.config import settings
from futureos.models import Action, IntentType, UserContext
from futureos.policy import evaluate_plan, flatten_actions, should_confirm_from_policy
from futureos.router import route
from futureos.safety import ask_confirmation, should_require_confirmation, write_audit, write_history
from futureos.session import SessionStore
from futureos.voice import VoiceEngine
from futureos.workflows import execute_action

app = typer.Typer(add_completion=False)
session_store = SessionStore()


def _is_sensitive(actions: list[Action]) -> bool:
    sensitive_intents = {
        IntentType.SEND_ZALO,
        IntentType.SEND_BULK_EMAIL,
        IntentType.FILE_DELETE,
        IntentType.FILE_WRITE,
    }
    return any(action.intent in sensitive_intents for action in flatten_actions(actions))


def _run_command(raw_text: str, user_ctx: UserContext, session_id: str, voice: VoiceEngine | None = None) -> None:
    plan = route(raw_text)
    actions: list[Action] = plan.actions
    if not actions:
        print("Khong co hanh dong nao duoc tao.")
        return

    print("=== Plan ===")
    print(plan.model_dump_json(indent=2))

    allowed, checks = evaluate_plan(actions, user_ctx)
    print("=== Policy ===")
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    write_audit(
        {"event": "policy_check", "session_id": session_id, "user": user_ctx.model_dump(), "text": raw_text, "checks": checks}
    )
    if not allowed:
        print("Policy denied this request.")
        write_history(
            {"event": "policy_denied", "session_id": session_id, "text": raw_text, "user": user_ctx.model_dump(), "checks": checks}
        )
        return

    if _is_sensitive(actions):
        if not session_store.within_sensitive_rate_limit(session_id):
            print("Rate limit exceeded for sensitive actions.")
            write_history({"event": "rate_limited", "session_id": session_id, "text": raw_text})
            return
        session_store.touch_sensitive(session_id)

    need_confirm = (
        plan.needs_confirmation or should_require_confirmation(actions) or should_confirm_from_policy(actions, user_ctx)
    )
    if need_confirm:
        allowed_confirm = ask_confirmation()
        if not allowed_confirm:
            print("Da huy theo xac nhan nguoi dung.")
            write_history({"event": "cancelled", "session_id": session_id, "text": raw_text, "plan": plan.model_dump()})
            return

    for action in actions:
        result = execute_action(action)
        print("=== Result ===")
        print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
        write_history(
            {
                "event": "action_executed",
                "session_id": session_id,
                "text": raw_text,
                "action": action.model_dump(),
                "result": result.model_dump(),
            }
        )
        if voice:
            voice.tts(result.detail)


def _resolve_session(required_session_id: str | None) -> tuple[str, UserContext] | tuple[None, None]:
    session_id = required_session_id or session_store.get_active()
    if not session_id:
        print("No active session. Please run login first.")
        return None, None
    session = session_store.get(session_id)
    if session is None:
        print("Session is missing/expired. Please login again.")
        return None, None
    return session_id, session.user


@app.command()
def login(
    role: str = typer.Option(settings.default_role, help="owner/dev/user/guest"),
    actor: str = typer.Option("cli-user", help="Actor id"),
    allow_c_drive_full: bool = typer.Option(settings.allow_c_drive_full, help="Enable full C drive for owner"),
    secret: str = typer.Option("", help="PIN or DEV secret when required"),
    voice_confidence: Optional[float] = typer.Option(None, help="Voice confidence from verifier (0..1)"),
) -> None:
    user_ctx, message = authenticate_login(
        role_raw=role,
        actor=actor,
        allow_c_drive_full=allow_c_drive_full,
        secret=secret,
        voice_confidence=voice_confidence,
    )
    print(message)
    if user_ctx is None:
        return
    record = session_store.create_session(user_ctx)
    print(f"session_id={record.session_id}")
    print("Session is now active.")


@app.command()
def logout(session_id: Optional[str] = typer.Option(None, help="Session id to revoke (default: active session)")) -> None:
    sid = session_id or session_store.get_active()
    if not sid:
        print("No active session.")
        return
    if session_store.revoke(sid):
        print(f"Revoked session: {sid}")
    else:
        print("Session not found.")


@app.command("whoami")
def whoami(session_id: Optional[str] = typer.Option(None, help="Session id (default: active session)")) -> None:
    sid, user_ctx = _resolve_session(session_id)
    if not sid or not user_ctx:
        return
    print(json.dumps({"session_id": sid, "user": user_ctx.model_dump()}, ensure_ascii=False, indent=2))


@app.command("sessions")
def sessions_cmd() -> None:
    records = session_store.list_active()
    output = [
        {
            "session_id": s.session_id,
            "role": s.user.role.value,
            "actor": s.user.actor,
            "expires_at": s.expires_at.isoformat(),
            "allow_c_drive_full": s.user.allow_c_drive_full,
        }
        for s in records
    ]
    print(json.dumps(output, ensure_ascii=False, indent=2))


@app.command()
def run(
    command: Optional[str] = typer.Argument(None, help="Natural language command"),
    session_id: Optional[str] = typer.Option(None, help="Session id (default: active session)"),
) -> None:
    voice = VoiceEngine()
    sid, user_ctx = _resolve_session(session_id)
    if not sid or not user_ctx:
        return

    if command:
        _run_command(command, user_ctx=user_ctx, session_id=sid)
        return

    print("futureOS interactive mode")
    print("Type 'exit' to quit.")
    while True:
        wake_ok = voice.wait_wakeword()
        if not wake_ok:
            print("Wake word mismatch.")
            continue

        # Optional voice identity re-check. If it fails, keep current session and continue.
        print("Re-verify identity before command? (yes/no)")
        verify = input("> ").strip().lower() in {"yes", "y"}
        if verify:
            re_ctx = resolve_interactive_identity()
            if re_ctx is None:
                print("Identity verification failed.")
                continue
            # Keep strict session binding by opening a fresh session for new identity.
            rec = session_store.create_session(re_ctx)
            sid = rec.session_id
            user_ctx = rec.user
            print(f"Switched session: {sid}")

        text = voice.stt()
        if text.strip().lower() in {"exit", "quit"}:
            break
        _run_command(text, user_ctx=user_ctx, session_id=sid, voice=voice)


def main() -> None:
    app()
