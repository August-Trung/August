# HANDOFF

## Release Target
- Milestone: Stable v1 end-to-end (voice vi, role policy, 5 flows)
- Deadline: 2026-04-30

## Current Snapshot
- Date: 2026-03-21
- Active branch: `develop`
- Last focus: Build Python MVP core pipeline
- Run status: `python run.py` works in dry-run

## Completed In Latest Session
- Created core app scaffold (`futureos/*`)
- Added rule-first router + optional AI parser
- Added safety confirm + action history log
- Added workflow actions (find draft, send Zalo, bulk email)
- Added voice MVP interface (wakeword/pin/stt/tts stubs)

## In Progress
- Project management operating model (git flow + tracking docs)
- Permission matrix and policy engine (owner/dev/user/guest)

## Open Risks / Blockers
- Real Zalo integration depends on OA/ZNS policy and credentials
- Voice owner verification is still MVP-level (PIN fallback)
- Full production hardening not done yet

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
1. Define and implement permission/policy matrix (especially C drive guard).
2. Build Flow 1 production baseline: router + Vietnamese intent robustness + audit events.
3. Add UI shell (chat + dashboard + settings) and background runner skeleton.

## Instructions For New Chat
- Ask assistant to read:
  - `HANDOFF.md`
  - `WORKBOARD.md`
  - `README.md`
  - `HISTORY.md`
- Continue from section: `In Progress` + `Next 3 Priorities`.
