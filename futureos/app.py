from __future__ import annotations

import json
from typing import Optional

import typer

from futureos.auth import build_user_context, resolve_interactive_identity
from futureos.config import settings
from futureos.models import Action, UserContext
from futureos.policy import evaluate_plan, should_confirm_from_policy
from futureos.router import route
from futureos.safety import ask_confirmation, should_require_confirmation, write_audit, write_history
from futureos.voice import VoiceEngine
from futureos.workflows import execute_action

app = typer.Typer(add_completion=False)


def _run_command(raw_text: str, user_ctx: UserContext, voice: VoiceEngine | None = None) -> None:
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
    write_audit({"event": "policy_check", "user": user_ctx.model_dump(), "text": raw_text, "checks": checks})
    if not allowed:
        print("Policy denied this request.")
        write_history({"event": "policy_denied", "text": raw_text, "user": user_ctx.model_dump(), "checks": checks})
        return

    need_confirm = (
        plan.needs_confirmation or should_require_confirmation(actions) or should_confirm_from_policy(actions, user_ctx)
    )
    if need_confirm:
        allowed = ask_confirmation()
        if not allowed:
            print("Da huy theo xac nhan nguoi dung.")
            write_history({"event": "cancelled", "text": raw_text, "plan": plan.model_dump()})
            return

    for action in actions:
        result = execute_action(action)
        print("=== Result ===")
        print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
        write_history(
            {
                "event": "action_executed",
                "text": raw_text,
                "action": action.model_dump(),
                "result": result.model_dump(),
            }
        )
        if voice:
            voice.tts(result.detail)


@app.command()
def run(
    command: Optional[str] = typer.Argument(None, help="Natural language command"),
    role: str = typer.Option(settings.default_role, help="owner/dev/user/guest"),
    actor: str = typer.Option("cli-user", help="Actor id for audit logs"),
    allow_c_drive_full: bool = typer.Option(settings.allow_c_drive_full, help="Enable full C drive access for owner"),
) -> None:
    voice = VoiceEngine()
    user_ctx = build_user_context(role_raw=role, allow_c_drive_full=allow_c_drive_full, actor=actor)
    if command:
        _run_command(command, user_ctx=user_ctx)
        return

    print("futureOS interactive mode")
    print("Type 'exit' to quit.")
    while True:
        wake_ok = voice.wait_wakeword()
        if not wake_ok:
            print("Wake word mismatch.")
            continue
        interactive_ctx = resolve_interactive_identity()
        if interactive_ctx is None:
            print("Identity verification failed.")
            continue
        text = voice.stt()
        if text.strip().lower() in {"exit", "quit"}:
            break
        _run_command(text, user_ctx=interactive_ctx, voice=voice)


def main() -> None:
    app()
