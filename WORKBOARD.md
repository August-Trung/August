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
| Session lifecycle (login/logout/whoami) | done | Session-bound execution is mandatory |
| Identity hardening | done | Voice confidence + PIN/secret fallback + lockout |
| Sensitive action rate limit | done | Window-based limit per session |
| UI chat/voice | todo | Planned for Flow 4 |
| Dashboard + settings | todo | Planned for Flow 4 |
| Background runtime | todo | Planned for Flow 5 |
| Test matrix and regression suite | building | Unit tests + testcase gate added |

## This Execution Plan
- Enforce session-bound execution for all commands.
- Implement identity hardening with confidence + secret fallback.
- Add auth lockout and sensitive-action rate limiting.
- Add pre-check gate (xlsx fail scan + unit tests).

## Next Execution Plan
- Flow 03: Vietnamese voice upgrade (wakeword + STT/TTS provider adapters).
- Implement structured voice verifier adapter (real speaker embedding integration point).
- Expand regression tests for session expiration and auth lockout behavior.

## Known Issues
- File finder still broad; relevance ranking should be improved.
- No real speaker embedding verification yet.
- No UI yet (CLI only).

## Upgrade Queue
- Voice diarization + speaker verification confidence thresholds.
- Multi-step workflow planner with retries and rollback hints.
- Queue worker for outbound actions (Zalo/email).
