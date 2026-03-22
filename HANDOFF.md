# HANDOFF

## Release Target
- Milestone: Stable v1 end-to-end (voice vi, role policy, 5 flows)
- Deadline: 2026-04-30

## Current Snapshot
- Date: 2026-03-22
- Active branch: `develop`
- Last focus: Core fileops reliability hardening (router priority + UTF-8 CLI + regression gate)
- Run status: Unit tests and testcase gate passing

## Completed In Latest Session
- Added `futureos/__main__.py` for `python -m futureos`.
- Added app direct execution guard and UTF-8 stream reconfigure in CLI main.
- Updated routing policy to prioritize high-confidence rule plan before AI parse.
- Expanded normalization replacements and refreshed UTF-8 VN parsing tests.
- Added `tests/test_cli_entrypoint.py` and fixed Windows decode handling in subprocess test.
- Re-ran `run_gate.py` successfully.

## In Progress
- Disambiguation design for multi-result file search (choose/confirm policy)

## Open Risks / Blockers
- Real Zalo integration depends on OA/ZNS policy and credentials
- Voice ownership detection still passphrase-based (needs real embedding verifier)
- Queue is still file-based, not built for high-concurrency distributed execution.
- Path entity extraction still heuristic-heavy for deeply ambiguous commands.

## Verify Quickly
```powershell
pip install -r requirements.txt
python -m futureos --help
python scripts/run_gate.py
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
