# HANDOFF

## Release Target
- Milestone: Stable v1 end-to-end (voice vi, role policy, 5 flows)
- Deadline: 2026-04-30

## Current Snapshot
- Date: 2026-03-21
- Active branch: `codex/flow-05-background-worker`
- Last focus: background queue and worker runtime
- Run status: queue/worker commands available

## Completed In Latest Session
- Added durable queue: `futureos/queue.py`
- Added retry/backoff + dead-letter behavior
- Added CLI commands: `enqueue`, `queue-status`, `worker`
- Added UI queue actions (enqueue and process-one)
- Added Flow 05 test coverage and updated evidence image

## In Progress
- Hardening sprint planning

## Open Risks / Blockers
- Real Zalo integration depends on OA/ZNS policy and credentials
- Voice ownership detection still passphrase-based (needs real embedding verifier)
- Queue file storage needs lock strategy for high-concurrency scenarios

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
1. Add service wrapper for always-on background worker.
2. Optimize file-search latency and reduce long-running tests.
3. Integrate real mic streaming STT + speaker embedding verifier.

## Instructions For New Chat
- Ask assistant to read:
  - `HANDOFF.md`
  - `WORKBOARD.md`
  - `README.md`
  - `HISTORY.md`
- Continue from section: `In Progress` + `Next 3 Priorities`.
