# HANDOFF

## Release Target
- Milestone: Stable v1 end-to-end (voice vi, role policy, 5 flows)
- Deadline: 2026-04-30

## Current Snapshot
- Date: 2026-03-22
- Active branch: `codex/hardening-sprint-1`
- Last focus: hardening reliability/security controls
- Run status: hardening sprint 1 implemented

## Completed In Latest Session
- Added queue hardening: idempotency, timeout requeue, cancel task.
- Added worker hardening: lock, heartbeat, crash backoff.
- Added tamper-evident hash chain for history/audit.
- Added run gate script: `scripts/run_gate.py`.
- Added tests for queue/safety hardening and updated testcase evidence.

## In Progress
- Hardening Sprint 2 planning

## Open Risks / Blockers
- Real Zalo integration depends on OA/ZNS policy and credentials
- Voice ownership detection still passphrase-based (needs real embedding verifier)
- Queue is still file-based, not built for high-concurrency distributed execution.

## Verify Quickly
```powershell
pip install -r requirements.txt
python run.py "tim ban thao lap trinh trong o D va gui zalo cho sep va gui email hang loat cho team"
```

## Files Changed Recently
- `README.md`
- `.env.example`
- `requirements.txt`
- `run.py`
- `futureos/app.py`
- `futureos/config.py`
- `futureos/models.py`
- `futureos/router.py`
- `futureos/llm.py`
- `futureos/safety.py`
- `futureos/tools.py`
- `futureos/workflows.py`
- `futureos/voice.py`

## Next 3 Priorities
1. Service wrapper for always-on background worker with auto-start.
2. Secure secret storage and admin settings hardening in UI.
3. Real microphone streaming STT + speaker embedding verifier integration.

## Instructions For New Chat
- Ask assistant to read:
  - `HANDOFF.md`
  - `WORKBOARD.md`
  - `README.md`
  - `HISTORY.md`
- Continue from section: `In Progress` + `Next 3 Priorities`.
