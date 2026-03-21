# HANDOFF

## Release Target
- Milestone: Stable v1 end-to-end (voice vi, role policy, 5 flows)
- Deadline: 2026-04-30

## Current Snapshot
- Date: 2026-03-21
- Active branch: `codex/flow-02-session-identity`
- Last focus: Session lifecycle + identity hardening
- Run status: login/session-bound run is active

## Completed In Latest Session
- Added session lifecycle (`login/logout/whoami/sessions`)
- Enforced session-bound command execution
- Added auth hardening (voice confidence + secret fallback + lockout)
- Added sensitive-action rate limiting
- Added test gate scripts and baseline unit tests

## In Progress
- Flow 03 voice provider upgrade planning

## Open Risks / Blockers
- Real Zalo integration depends on OA/ZNS policy and credentials
- Voice ownership detection still placeholder (needs real embedding verifier)
- Path extraction and CRUD safety prompts need hardening

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
1. Flow 03: wire real Vietnamese STT/TTS adapter interfaces.
2. Add real speaker verification adapter and confidence calibration.
3. Start UI shell skeleton (chat + dashboard + settings) for Flow 04 staging.

## Instructions For New Chat
- Ask assistant to read:
  - `HANDOFF.md`
  - `WORKBOARD.md`
  - `README.md`
  - `HISTORY.md`
- Continue from section: `In Progress` + `Next 3 Priorities`.
