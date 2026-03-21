# WORKBOARD

## Project Status Overview

| Feature | Status | Notes |
|---|---|---|
| Core CLI orchestration | done | End-to-end dry-run works |
| Rule-first router | done | Composite command supported |
| AI parser fallback | done | OpenAI Responses API path ready |
| Safety confirm/history | done | High-risk action confirmation enabled |
| Voice pipeline | done | VN wakeword normalization + STT/TTS adapter path |
| Zalo integration | building | Current path is dry-run + webhook placeholder |
| Bulk email integration | building | SMTP available but untested in production |
| Permission policy (owner/dev/user/guest) | done | Enforced before execution |
| C drive protection policy | done | Deny-by-default + role-specific delete rules |
| Session lifecycle (login/logout/whoami) | done | Session-bound execution is mandatory |
| Identity hardening | done | Voice profile enroll/login + confidence + fallback + lockout |
| Sensitive action rate limit | done | Window-based limit per session |
| UI chat/voice | done | Streamlit shell with session-bound execution |
| Dashboard + settings | done | Session/log/settings + gate panel |
| Background runtime | done | Queue + worker with retry/backoff + dead-letter |
| Test matrix and regression suite | done | `Not Run` cleanup + automation + evidence image |

## This Execution Plan
- Build Flow 05 background runtime with durable task queue.
- Add CLI/UI integration for queue and worker operations.
- Extend testcase automation for queue/dead-letter coverage.

## Next Execution Plan
- Hardening sprint: optimize file-search latency and unit-test runtime.
- Add UI authentication persistence and secure secret handling.
- Integrate microphone streaming STT and real speaker-embedding verifier.

## Known Issues
- File finder still broad; relevance ranking should be improved.
- No real speaker embedding verification yet.
- No UI yet (CLI only).

## Upgrade Queue
- Voice diarization + speaker verification confidence thresholds.
- Multi-step workflow planner with retries and rollback hints.
- Queue worker for outbound actions (Zalo/email).
