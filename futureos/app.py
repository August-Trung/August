from __future__ import annotations

import json
import sys
from typing import Optional

import typer

from futureos.auth import authenticate_login
from futureos.config import settings
from futureos.engine import execute_command, resolve_session
from futureos.queue import BackgroundWorker, TaskQueue
from futureos.safety import AUDIT_CHAIN_FILE, AUDIT_FILE, HISTORY_CHAIN_FILE, HISTORY_FILE, ask_confirmation, verify_chain
from futureos.session import SessionStore
from futureos.voice import VoiceEngine

app = typer.Typer(add_completion=False)
session_store = SessionStore()
task_queue = TaskQueue()
worker = BackgroundWorker(task_queue, session_store)


def _run_command(raw_text: str, session_id: str, user_ctx, voice: VoiceEngine | None = None) -> None:
    result = execute_command(
        raw_text=raw_text,
        session_id=session_id,
        user_ctx=user_ctx,
        session_store=session_store,
        confirm_func=ask_confirmation,
    )
    print("=== Plan ===")
    print(json.dumps(result.get("plan", {}), ensure_ascii=True, indent=2))
    print("=== Policy ===")
    print(json.dumps(result.get("policy", []), ensure_ascii=True, indent=2))
    if not result.get("ok"):
        print(result.get("error", "Failed"))
        return
    for item in result.get("results", []):
        print("=== Result ===")
        print(json.dumps(item, ensure_ascii=True, indent=2))
        if voice:
            voice.tts(item.get("detail", "Done"))


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


@app.command("voice-enroll")
def voice_enroll(
    actor: str = typer.Option(..., help="Actor id to bind voice profile"),
    passphrase: str = typer.Option(..., help="Vietnamese passphrase for voice verification"),
) -> None:
    voice = VoiceEngine()
    voice.enroll_actor_voice(actor=actor, passphrase=passphrase)
    print(f"Voice profile saved for actor={actor}")


@app.command("voice-login")
def voice_login(
    role: str = typer.Option(settings.default_role, help="owner/dev/user/guest"),
    actor: str = typer.Option("voice-user", help="Actor id"),
    allow_c_drive_full: bool = typer.Option(settings.allow_c_drive_full, help="Enable full C drive for owner"),
    secret: str = typer.Option("", help="PIN or DEV secret fallback"),
) -> None:
    voice = VoiceEngine()
    if not voice.wait_wakeword():
        print("Wakeword mismatch.")
        return
    spoken = voice.capture_passphrase()
    confidence = voice.verify_actor_voice(actor=actor, spoken_text=spoken)
    user_ctx, message = authenticate_login(
        role_raw=role,
        actor=actor,
        allow_c_drive_full=allow_c_drive_full,
        secret=secret,
        voice_confidence=confidence,
    )
    print(f"{message} (voice_confidence={confidence:.2f})")
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
    sid, user_ctx = resolve_session(session_store, session_id)
    if not sid or not user_ctx:
        print("No active valid session.")
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


@app.command("enqueue")
def enqueue_cmd(
    command: str = typer.Argument(..., help="Natural language command"),
    session_id: Optional[str] = typer.Option(None, help="Session id (default: active session)"),
    auto_confirm: bool = typer.Option(False, help="Auto confirm high-risk actions in background"),
    max_retries: int = typer.Option(settings.queue_max_retries, help="Max retries for this task"),
    timeout_seconds: int = typer.Option(settings.queue_task_timeout_seconds, help="Task processing timeout"),
    idempotency_key: str = typer.Option("", help="Optional idempotency key"),
) -> None:
    sid, user_ctx = resolve_session(session_store, session_id)
    if not sid or not user_ctx:
        print("No active session. Please run login first.")
        return
    task = task_queue.enqueue(
        command=command,
        session_id=sid,
        auto_confirm=auto_confirm,
        max_retries=max_retries,
        timeout_seconds=timeout_seconds,
        idempotency_key=idempotency_key or None,
    )
    print(json.dumps(task.to_dict(), ensure_ascii=False, indent=2))


@app.command("queue-status")
def queue_status() -> None:
    print(json.dumps({"stats": task_queue.stats(), "tasks": [t.to_dict() for t in task_queue.list_all()]}, ensure_ascii=False, indent=2))


@app.command("cancel-task")
def cancel_task(task_id: str = typer.Argument(..., help="Task id to cancel")) -> None:
    if task_queue.cancel(task_id):
        print(f"Cancelled task: {task_id}")
    else:
        print("Task not found or not cancellable.")


@app.command("verify-logs")
def verify_logs() -> None:
    history_ok = verify_chain(HISTORY_FILE, HISTORY_CHAIN_FILE)
    audit_ok = verify_chain(AUDIT_FILE, AUDIT_CHAIN_FILE)
    print(json.dumps({"history_chain_ok": history_ok, "audit_chain_ok": audit_ok}, ensure_ascii=False, indent=2))


@app.command("worker")
def worker_cmd(
    once: bool = typer.Option(False, help="Process one task and exit"),
    stop_after: int = typer.Option(0, help="Stop after N processed tasks in loop mode"),
) -> None:
    if once:
        print(json.dumps(worker.run_once(), ensure_ascii=False, indent=2))
        return
    limit = stop_after if stop_after > 0 else None
    print("Worker loop started. Press Ctrl+C to stop.")
    try:
        worker.run_loop(stop_after=limit)
    except RuntimeError as e:
        print(str(e))


@app.command()
def run(
    command: Optional[str] = typer.Argument(None, help="Natural language command"),
    session_id: Optional[str] = typer.Option(None, help="Session id (default: active session)"),
) -> None:
    voice = VoiceEngine()
    sid, user_ctx = resolve_session(session_store, session_id)
    if not sid or not user_ctx:
        print("No active session. Please run login first.")
        return

    if command:
        _run_command(command, session_id=sid, user_ctx=user_ctx)
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
            spoken = voice.capture_passphrase()
            confidence = voice.verify_actor_voice(actor=user_ctx.actor, spoken_text=spoken)
            if confidence < settings.voice_profile_threshold:
                print(f"Voice verification failed (confidence={confidence:.2f}).")
                continue
            print(f"Voice verification passed (confidence={confidence:.2f}).")

        text = voice.stt()
        if text.strip().lower() in {"exit", "quit"}:
            break
        _run_command(text, session_id=sid, user_ctx=user_ctx, voice=voice)


def main() -> None:
    for stream_name in ("stdin", "stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass
    app()


if __name__ == "__main__":
    main()
