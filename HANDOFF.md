# HANDOFF

## Release Target
- Milestone: Stable v1 end-to-end (voice vi, role policy, 5 flows)
- Deadline: 2026-04-30

## Current Snapshot
- Date: 2026-03-21
- Active branch: `codex/flow-04-ui-shell`
- Last focus: UI shell + shared engine refactor
- Run status: Streamlit UI available

## Completed In Latest Session
- Added `futureos/ui_app.py` with Chat/Voice/Dashboard/Settings/Test Gate
- Added shared command executor `futureos/engine.py`
- Added Flow 04 test cases and re-executed full testcase matrix
- Updated latest evidence image at `data/test_evidence_latest.png`

## In Progress
- Flow 05 planning (background runtime/queue)

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
1. Flow 05: build background worker mode with task queue and retries.
2. Bind UI actions to durable queue for outbound sends.
3. Add real microphone streaming STT path into UI voice tab.

## Instructions For New Chat
- Ask assistant to read:
  - `HANDOFF.md`
  - `WORKBOARD.md`
  - `README.md`
  - `HISTORY.md`
- Continue from section: `In Progress` + `Next 3 Priorities`.
