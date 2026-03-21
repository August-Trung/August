from __future__ import annotations

import json
from typing import Optional

import typer

from futureos.models import Action
from futureos.router import route
from futureos.safety import ask_confirmation, should_require_confirmation, write_history
from futureos.voice import VoiceEngine
from futureos.workflows import execute_action

app = typer.Typer(add_completion=False)


def _run_command(raw_text: str, voice: VoiceEngine | None = None) -> None:
    plan = route(raw_text)
    actions: list[Action] = plan.actions
    if not actions:
        print("Khong co hanh dong nao duoc tao.")
        return

    print("=== Plan ===")
    print(plan.model_dump_json(indent=2))

    need_confirm = plan.needs_confirmation or should_require_confirmation(actions)
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
def run(command: Optional[str] = typer.Argument(None, help="Natural language command")) -> None:
    voice = VoiceEngine()
    if command:
        _run_command(command)
        return

    print("futureOS interactive mode")
    print("Type 'exit' to quit.")
    while True:
        wake_ok = voice.wait_wakeword()
        if not wake_ok:
            print("Wake word mismatch.")
            continue
        if not voice.verify_owner():
            print("Owner verification failed.")
            continue
        text = voice.stt()
        if text.strip().lower() in {"exit", "quit"}:
            break
        _run_command(text, voice=voice)


def main() -> None:
    app()
