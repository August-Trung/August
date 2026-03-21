# HANDOFF

## Release Target
- Milestone: Stable v1 end-to-end (voice vi, role policy, 5 flows)
- Deadline: 2026-04-30

## Current Snapshot
- Date: 2026-03-21
- Active branch: `codex/flow-03-voice-upgrade`
- Last focus: Vietnamese voice upgrade + testcase execution cleanup
- Run status: voice-enroll/voice-login enabled

## Completed In Latest Session
- Cleared all `Not Run` testcase rows by execution automation
- Added evidence image output for testcase run
- Added voice profile store + wakeword normalization
- Added `voice-enroll` and `voice-login` commands
- Added voice unit tests

## In Progress
- Flow 04 planning (UI shell + dashboard + settings)

## Open Risks / Blockers
- Real Zalo integration depends on OA/ZNS policy and credentials
- Voice ownership detection still passphrase-based (needs real embedding verifier)
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
1. Flow 04: implement UI shell (chat + dashboard + settings).
2. Add runtime panel to display session role and policy decisions.
3. Prepare real speaker-embedding verifier adapter integration point.

## Instructions For New Chat
- Ask assistant to read:
  - `HANDOFF.md`
  - `WORKBOARD.md`
  - `README.md`
  - `HISTORY.md`
- Continue from section: `In Progress` + `Next 3 Priorities`.
