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
| Permission policy (owner/dev/user/guest) | todo | Critical for v1 |
| C drive protection policy | todo | Must be deny-by-default unless allowed |
| UI chat/voice | todo | Planned for Flow 4 |
| Dashboard + settings | todo | Planned for Flow 4 |
| Background runtime | todo | Planned for Flow 5 |
| Test matrix and regression suite | building | Need formalized test cases |

## This Execution Plan
- Add `HANDOFF.md` for context continuity across chats.
- Establish project management files and workflow.
- Prepare test-case workbook template.

## Next Execution Plan
- Implement role-based permission matrix and policy middleware.
- Add policy checks before any filesystem CRUD.
- Add explicit C-drive guard with elevated toggle only for owner/dev.
- Add structured audit logs for all sensitive actions.

## Known Issues
- File finder still broad; relevance ranking should be improved.
- No real speaker embedding verification yet.
- No UI yet (CLI only).

## Upgrade Queue
- Voice diarization + speaker verification confidence thresholds.
- Multi-step workflow planner with retries and rollback hints.
- Queue worker for outbound actions (Zalo/email).
