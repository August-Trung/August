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
