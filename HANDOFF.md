# HANDOFF

## Release Target
- Milestone: Stable v1 end-to-end (voice vi, role policy, 5 flows)
- Deadline: 2026-04-30

## Current Snapshot
- Date: 2026-03-21
- Active branch: `codex/flow-01-permission-policy`
- Last focus: Permission and policy foundation
- Run status: policy checks + audit logging enabled

## Completed In Latest Session
- Added role model: `owner/dev/user/guest`
- Added policy middleware before execution
- Added C-drive protection logic by role
- Added `data/audit.jsonl` logging
- Added file CRUD intents and execution handlers

## In Progress
- Flow 02 session and identity hardening

## Open Risks / Blockers
- Real Zalo integration depends on OA/ZNS policy and credentials
- Voice ownership detection is still MVP-level (PIN/secret fallback)
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
1. Flow 02: session + identity lifecycle (role login + stronger verification path).
2. Add stricter confirm rules for file delete/write in sensitive locations.
3. Build UI shell skeleton (chat + dashboard + settings) for Flow 04 staging.

## Instructions For New Chat
- Ask assistant to read:
  - `HANDOFF.md`
  - `WORKBOARD.md`
  - `README.md`
  - `HISTORY.md`
- Continue from section: `In Progress` + `Next 3 Priorities`.
