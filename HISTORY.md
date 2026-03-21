# HISTORY

## 2026-03-21

### Delivered
- Built MVP Python project scaffold for futureOS.
- Added router, optional AI parser, safety confirmation, and workflow execution.
- Added dry-run integration for Zalo and bulk email.
- Added interactive voice shell stubs and command mode.
- Added `HANDOFF.md`, `WORKBOARD.md`, `HISTORY.md` management system.
- Initialized Git repository and created `develop` branch.

### Decisions
- Use rule-first routing for reliability; AI parser is fallback.
- Enforce confirmation for medium/high-risk actions.
- Keep outbound integrations dry-run by default.
- Adopt documentation-first management for continuity across chat token limits.

### Risks
- Production connectors require credential/policy setup.
- Voice ownership detection is not yet production-grade.
- Permission model is not yet implemented.

### Next Step
- Implement role-based access and C-drive safety controls.

## 2026-03-21 (Flow 01 update)

### Delivered
- Created branch `codex/flow-01-permission-policy`.
- Added role model: `owner/dev/user/guest`.
- Implemented policy engine with execution-time checks.
- Added C-drive guard rules:
  - owner: full only when `allow_c_drive_full=true`, delete blocked otherwise
  - dev: full access
  - user: non-delete only on C
  - guest: read-only on C and no external outbound
- Added audit log stream in `data/audit.jsonl`.
- Added file CRUD intents and workflow handlers (read/write/delete) with policy gate.

### Decisions
- Policy is enforced before confirmation and execution.
- Composite actions are flattened for per-step policy evaluation.
- Keep default role as `user` unless explicitly set.

### Risks
- Router file CRUD uses placeholder paths; NLP extraction of user-specific paths still basic.
- Dev role currently guarded by `DEV_SECRET`, needs stronger auth in Flow 02.

### Next Step
- Flow 02: session lifecycle + stronger identity binding (voice/session mapping).

## 2026-03-21 (Flow 02 update)

### Delivered
- Created branch `codex/flow-02-session-identity`.
- Added session manager with persisted records (`data/sessions.json`) and active session pointer.
- Added CLI commands: `login`, `logout`, `whoami`, `sessions`, and session-bound `run`.
- Added identity hardening with:
  - voice confidence threshold
  - PIN/secret fallback
  - auth failure lockout policy
- Added sensitive-action rate limiting per session window.
- Added test gate tools:
  - `scripts/check_testcases.py` (fails if any testcase row has `Status=Fail`)
  - unit tests in `tests/`

### Decisions
- Every command execution now requires a valid session.
- Identity re-check in interactive mode can open a switched session.
- Pre-check rule is enforced: testcase-fail scan + unit tests before feature work.

### Risks
- Voice confidence is still input-based placeholder, not yet real speaker embedding.
- Session store is file-based; concurrency and multi-device sync are not yet addressed.

### Next Step
- Flow 03: replace voice placeholders with provider adapters and Vietnamese STT/TTS wiring.

## 2026-03-21 (Flow 03 update)

### Delivered
- Created branch `codex/flow-03-voice-upgrade`.
- Cleared all `Not Run` rows in `TEST_CASES.xlsx` via executable checks.
- Added testcase execution automation: `scripts/execute_testcases.py`.
- Added evidence image generation: `data/test_evidence_flow03.png`.
- Upgraded voice module:
  - Vietnamese wakeword normalization
  - voice profile enroll/verify store
  - STT/TTS adapter path (console + optional OpenAI)
- Added commands:
  - `voice-enroll`
  - `voice-login`
- Added voice unit tests.

### Decisions
- Test gate now blocks both `Fail` and `Not Run`.
- Voice profile matching uses passphrase similarity in this stage; speaker-embedding engine remains next.

### Risks
- Passphrase similarity is weaker than true biometric speaker verification.
- OpenAI STT/TTS paths need credential and runtime environment checks for production.

### Next Step
- Flow 04: build UI shell and dashboard/settings with session-aware controls.

## 2026-03-21 (Flow 04 update)

### Delivered
- Created branch `codex/flow-04-ui-shell`.
- Added shared execution module `futureos/engine.py` for CLI/UI parity.
- Built Streamlit UI shell `futureos/ui_app.py` with tabs:
  - Chat
  - Voice profile
  - Dashboard
  - Settings
  - Test Gate
- Added functional Flow 04 test rows (F-004, F-005) and executed all testcases.
- Updated testcase evidence image to `data/test_evidence_latest.png`.

### Decisions
- UI execution uses the same policy/session engine as CLI.
- Test gate in UI runs `check_testcases` + `unittest` directly.
- `Not Run` is treated as blocking status.

### Risks
- Streamlit UI currently simulates voice input by typed passphrase.
- UI secret entry is plain form input; production needs hardened secret vault pattern.

### Next Step
- Flow 05: background runtime and queue worker for durable task automation.

## 2026-03-21 (Flow 05 update)

### Delivered
- Created branch `codex/flow-05-background-worker`.
- Added durable queue module `futureos/queue.py`.
- Implemented background worker with:
  - `run_once`
  - loop mode with poll interval
  - retry/backoff policy
  - dead-letter fallback
- Added CLI commands:
  - `enqueue`
  - `queue-status`
  - `worker`
- Integrated queue controls into UI Dashboard and Chat enqueue flow.
- Added queue unit tests and Flow 05 testcase coverage (F-006, F-007).

### Decisions
- Queue persists locally in `data/task_queue.json`.
- Dead-letter entries persist in `data/dead_letter.jsonl`.
- Worker reuses the same execution engine and policy/session controls as CLI/UI direct runs.

### Risks
- Local-file queue is not multi-process safe under heavy parallel write load.
- Worker loop currently runs in foreground process; service wrapper remains future work.

### Next Step
- Hardening and productionization: service wrapper, locking strategy, and faster file search.

## 2026-03-22 (Hardening Sprint 1)

### Delivered
- Added queue reliability controls:
  - idempotency keys
  - task timeout/requeue
  - task cancel API
- Added worker runtime safety:
  - single-instance lock (`data/worker.lock`)
  - heartbeat (`data/worker_heartbeat.json`)
  - crash backoff loop
- Added tamper-evident log chain for history/audit (`_hash`, `_prev_hash`).
- Added CLI command: `verify-logs`.
- Added gate script: `scripts/run_gate.py`.
- Extended tests:
  - queue hardening tests
  - safety chain tests
- Extended testcase automation with Hardening S1 cases (F-008, F-009).

### Decisions
- Keep queue store file-based for Sprint 1, with clear limitations documented.
- Treat `Not Run` as blocking in all gates.

### Risks
- File-based queue/lock remains limited for multi-process high-throughput scenarios.
- Speaker verification still passphrase-similarity based.

### Next Step
- Hardening Sprint 2: service wrapper, stronger locking, and microphone streaming voice path.
