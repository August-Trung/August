# HANDOFF

## Release Target
- Milestone: Stable v1 end-to-end (voice vi, role policy, 5 flows)
- Deadline: 2026-04-30

## Current Snapshot
- Date: 2026-03-22
- Active branch: `codex/fileops-broad-testing`
- Last focus: Hybrid NLU v2 and broad fileops testing
- Run status: VN shorthand/typo parsing supported

## Completed In Latest Session
- Added `futureos/nlu.py` normalization (abbr + typo + accent handling).
- Upgraded router to Hybrid NLU v2 (AI primary + rule fallback + clarify fallback).
- Added broad fileops test script and report output.
- Extended functional testcases (F-011..F-015) for VN command variants.
- Fixed AI fallback robustness on API quota/errors.

## In Progress
- Sprint 2 parser/entity hardening planning

## Open Risks / Blockers
- Real Zalo integration depends on OA/ZNS policy and credentials
- Voice ownership detection still passphrase-based (needs real embedding verifier)
- Queue is still file-based, not built for high-concurrency distributed execution.
- Path entity extraction still heuristic-heavy for deeply ambiguous commands.

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
3. Richer path/entity extraction for Vietnamese commands.

## Instructions For New Chat
- Ask assistant to read:
  - `HANDOFF.md`
  - `WORKBOARD.md`
  - `README.md`
  - `HISTORY.md`
- Continue from section: `In Progress` + `Next 3 Priorities`.
