# WORKBOARD

## Project Status Overview

| Feature | Status | Notes |
|---|---|---|
| Core CLI orchestration | done | End-to-end dry-run works |
| Rule-first router | done | Composite command supported |
| AI parser fallback | done | OpenAI Responses API path ready |
| Safety confirm/history | done | High-risk action confirmation enabled |
| Voice pipeline | building | Stub engines, need real wakeword/STT/TTS |
| Zalo integration | building | Current path is dry-run + webhook placeholder |
| Bulk email integration | building | SMTP available but untested in production |
| Permission policy (owner/dev/user/guest) | done | Enforced before execution |
| C drive protection policy | done | Deny-by-default + role-specific delete rules |
| UI chat/voice | todo | Planned for Flow 4 |
| Dashboard + settings | todo | Planned for Flow 4 |
| Background runtime | todo | Planned for Flow 5 |
| Test matrix and regression suite | building | Need formalized test cases |

## This Execution Plan
- Implement role-based permission matrix and policy middleware.
- Add C-drive guard controls and audit logging.
- Extend workflow surface with file CRUD actions gated by policy.

## Next Execution Plan
- Flow 02: Session + identity hardening (role login lifecycle + voice identity path).
- Add stricter confirmation strategy for destructive local file actions.
- Add unit tests for policy matrix and C-drive scenarios.

## Known Issues
- File finder still broad; relevance ranking should be improved.
- No real speaker embedding verification yet.
- No UI yet (CLI only).

## Upgrade Queue
- Voice diarization + speaker verification confidence thresholds.
- Multi-step workflow planner with retries and rollback hints.
- Queue worker for outbound actions (Zalo/email).
