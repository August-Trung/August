from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import streamlit as st

from futureos.auth import authenticate_login
from futureos.config import settings
from futureos.engine import execute_command, resolve_session
from futureos.queue import BackgroundWorker, TaskQueue
from futureos.session import SessionStore
from futureos.voice import VoiceEngine

st.set_page_config(page_title="futureOS Control Center", layout="wide")

session_store = SessionStore()
task_queue = TaskQueue()
worker = BackgroundWorker(task_queue, session_store)
voice = VoiceEngine()


def _load_jsonl(path: Path, limit: int = 200) -> list[dict]:
    if not path.exists():
        return []
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def _run_gate() -> tuple[int, str]:
    cmds = [
        [sys.executable, "scripts/check_testcases.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
    ]
    output = []
    rc = 0
    for cmd in cmds:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(Path.cwd()))
        output.append(f"$ {' '.join(cmd)}\n{proc.stdout}\n{proc.stderr}")
        if proc.returncode != 0:
            rc = proc.returncode
            break
    return rc, "\n".join(output)


st.title("futureOS Control Center")
st.caption("UI shell: chat, voice, dashboard, settings, test gate, and queue worker controls.")

with st.sidebar:
    st.subheader("Session Login")
    role = st.selectbox("Role", ["owner", "dev", "user", "guest"], index=2)
    actor = st.text_input("Actor", value="ui-user")
    secret = st.text_input("Secret/PIN", value="", type="password")
    allow_c = st.checkbox("Allow full C drive (owner only)", value=False)
    voice_conf = st.slider("Voice confidence", min_value=0.0, max_value=1.0, value=0.9, step=0.01)
    if st.button("Login"):
        user_ctx, msg = authenticate_login(
            role_raw=role,
            actor=actor,
            allow_c_drive_full=allow_c,
            secret=secret,
            voice_confidence=voice_conf,
        )
        st.info(msg)
        if user_ctx:
            record = session_store.create_session(user_ctx)
            st.success(f"Session created: {record.session_id}")
    if st.button("Logout Active Session"):
        sid = session_store.get_active()
        if sid and session_store.revoke(sid):
            st.success(f"Revoked session: {sid}")
        else:
            st.warning("No active session.")

tabs = st.tabs(["Chat", "Voice", "Dashboard", "Settings", "Test Gate"])

with tabs[0]:
    st.subheader("Chat Command")
    sid, user_ctx = resolve_session(session_store, None)
    if not sid:
        st.warning("No active session. Login from sidebar first.")
    else:
        st.code(json.dumps({"session_id": sid, "user": user_ctx.model_dump()}, ensure_ascii=False, indent=2))
        cmd = st.text_area("Command", value="tim ban thao lap trinh trong o D")
        auto_confirm = st.checkbox("Auto confirm high-risk actions", value=False)
        col_run, col_queue = st.columns(2)
        if col_run.button("Run Command"):
            result = execute_command(
                raw_text=cmd,
                session_id=sid,
                user_ctx=user_ctx,
                session_store=session_store,
                confirm_func=(lambda: auto_confirm),
            )
            st.json(result)
        if col_queue.button("Enqueue Command"):
            task = task_queue.enqueue(command=cmd, session_id=sid, auto_confirm=auto_confirm)
            st.success(f"Queued task: {task.id}")
            st.json(task.to_dict())

with tabs[1]:
    st.subheader("Voice Profile")
    v_actor = st.text_input("Actor for voice profile", value="ui-user")
    passphrase = st.text_input("Enrollment passphrase (Vietnamese)", value="toi la chu may future")
    if st.button("Enroll Voice"):
        voice.enroll_actor_voice(v_actor, passphrase)
        st.success("Voice profile saved.")
    spoken = st.text_input("Spoken passphrase (simulated)", value="toi la chu may future")
    if st.button("Verify Voice"):
        conf = voice.verify_actor_voice(v_actor, spoken)
        st.metric("Voice confidence", f"{conf:.2f}")

with tabs[2]:
    st.subheader("Dashboard")
    sessions = session_store.list_active()
    st.write(f"Active sessions: {len(sessions)}")
    st.json(
        [
            {
                "session_id": s.session_id,
                "role": s.user.role.value,
                "actor": s.user.actor,
                "expires_at": s.expires_at.isoformat(),
                "allow_c_drive_full": s.user.allow_c_drive_full,
            }
            for s in sessions
        ]
    )
    qstats = task_queue.stats()
    st.markdown("**Queue**")
    st.json({"stats": qstats, "tasks": [t.to_dict() for t in task_queue.list_all()]})
    if st.button("Process One Queued Task"):
        st.json(worker.run_once())
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Recent History**")
        st.json(_load_jsonl(Path("data/history.jsonl"), limit=30))
    with col2:
        st.markdown("**Recent Audit**")
        st.json(_load_jsonl(Path("data/audit.jsonl"), limit=30))

with tabs[3]:
    st.subheader("Settings Snapshot")
    st.json(
        {
            "openai_model": settings.openai_model,
            "dry_run": settings.dry_run,
            "default_role": settings.default_role,
            "voice_language": settings.voice_language,
            "voice_wake_word": settings.voice_wake_word,
            "voice_threshold": settings.voice_profile_threshold,
            "session_ttl_minutes": settings.session_ttl_minutes,
            "rate_limit_count": settings.sensitive_rate_limit_count,
            "rate_limit_window_sec": settings.sensitive_rate_limit_window_sec,
        }
    )
    st.info("To change values, edit .env and restart the app.")

with tabs[4]:
    st.subheader("Test Gate")
    if st.button("Run Gate"):
        code, out = _run_gate()
        if code == 0:
            st.success("Gate passed.")
        else:
            st.error("Gate failed.")
        st.code(out)
    if st.button("Execute TEST_CASES and refresh evidence"):
        proc = subprocess.run([sys.executable, "scripts/execute_testcases.py"], capture_output=True, text=True, cwd=str(Path.cwd()))
        st.code(proc.stdout + "\n" + proc.stderr)
    evidence = Path("data/test_evidence_latest.png")
    if evidence.exists():
        st.image(str(evidence), caption="Latest testcase evidence")
