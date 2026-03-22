# futureOS (Python MVP)

Hands-free assistant MVP for dev/workflows:
- Hybrid NLU router (AI primary + rule fallback)
- Optional AI parser (OpenAI) with strict schema
- Safety guard (confirm/high-risk policy/history)
- Voice pipeline interface (wakeword, STT, TTS, owner check stubs)
- Workflow actions (find draft in `D:`, send Zalo, send bulk email)

This repo is a stable MVP scaffold for your 5-phase plan, not a final production agent.

## Project management protocol

- Main integration branch: `develop`
- Feature branch naming: `codex/flow-xx-short-name`
- Required tracking artifacts:
  - `README.md` (always updated)
  - `WORKBOARD.md` (status + next execution plan)
  - `HISTORY.md` (execution log + decisions)
  - `HANDOFF.md` (context handoff for new chats)
  - `TEST_CASES.xlsx` (test matrix and results)

## 1) Quick start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python run.py voice-enroll --actor august --passphrase "toi la chu may future"
python run.py voice-login --role owner --actor august --allow-c-drive-full --secret 123456
python run.py login --role owner --actor august --allow-c-drive-full --secret 123456
python run.py run "tim ban thao lap trinh trong o D va gui zalo cho sep, gui email cho team"
python run.py run "tao thu muc zzz o desktop roi di chuyen vao thu muc backup trong o d"
python -m futureos --help
```

Interactive mode:

```powershell
python run.py login --role user --actor local-user
python run.py run
```

UI mode:

```powershell
streamlit run futureos/ui_app.py
```

Background worker mode:

```powershell
python run.py enqueue "tim file o d" --auto-confirm
python run.py queue-status
python run.py cancel-task <task_id>
python run.py worker --once
python run.py worker --stop-after 10
python run.py verify-logs
```

## 2) Environment

Edit `.env`:

```env
# Core
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5-mini
USE_AI_ROUTER=true
DRY_RUN=true

# Wakeword / owner
WAKE_WORD=hey future
OWNER_PIN=123456
DEV_SECRET=
DEFAULT_ROLE=user
ALLOW_C_DRIVE_FULL=false
SESSION_TTL_MINUTES=120
AUTH_MAX_FAILURES=3
AUTH_LOCK_MINUTES=15
VOICE_CONFIDENCE_THRESHOLD=0.78
SENSITIVE_RATE_LIMIT_COUNT=5
SENSITIVE_RATE_LIMIT_WINDOW_SEC=300
VOICE_LANGUAGE=vi-VN
VOICE_WAKE_WORD=xin chao future
USE_OPENAI_STT=false
USE_OPENAI_TTS=false
OPENAI_TTS_VOICE=alloy
VOICE_PROFILE_THRESHOLD=0.78
QUEUE_MAX_RETRIES=3
QUEUE_BACKOFF_SECONDS=10
WORKER_POLL_SECONDS=5
WORKER_CRASH_BACKOFF_SECONDS=5
WORKER_LOCK_TTL_SECONDS=60
QUEUE_TASK_TIMEOUT_SECONDS=90
QUEUE_IDEMPOTENCY_WINDOW_MINUTES=120

# Email (optional when DRY_RUN=false)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
SMTP_FROM=

# Zalo (optional when DRY_RUN=false)
ZALO_WEBHOOK_URL=
ZALO_ACCESS_TOKEN=
```

## 3) What works now

- Parse command by rule-first and optionally AI fallback
- Parse command with Hybrid NLU v2:
  - Vietnamese normalization (accent, abbreviation, typo tolerance)
  - High-confidence deterministic rule parser (priority)
  - AI parser (schema-based) for flexible fallback
  - clarify fallback for missing critical args
- Ask for confirmation for high-risk actions
- Enforce role policy (`owner/dev/user/guest`) before execution
- Enforce C-drive guard policy with owner toggle + strict dev/user/guest rules
- Require authenticated session before command execution
- Support session commands: `login`, `logout`, `whoami`, `sessions`
- Support voice identity commands: `voice-enroll`, `voice-login`
- Add auth lockout and sensitive-action rate limiting
- Vietnamese wakeword normalization and voice profile matching
- UI shell with tabs: `Chat`, `Voice`, `Dashboard`, `Settings`, `Test Gate`
- Durable task queue + background worker (`enqueue`, `queue-status`, `worker`)
- Retry/backoff and dead-letter fallback for failed queued tasks
- Idempotency key support, task timeout, and task cancel command
- Worker single-instance lock + heartbeat
- Tamper-evident hash chain for history/audit logs (`verify-logs`)
- Search likely draft files under `D:\`
- File/path operations with policy gate:
  - `read/write/delete`
  - `create directory`
  - `move/copy/rename`
  - `list folder`
- Build outbound message payloads for Zalo + bulk email
- Execute in `dry-run` (safe) or real mode
- Save action history to `data/history.jsonl` and policy audits to `data/audit.jsonl`

## 4) Limitations

- Voice stack is scaffold-level (real wakeword/STT/TTS engines are plug-in points)
- Speaker verification uses passphrase similarity + fallback PIN/secret in this MVP
- Zalo API behavior depends on OA/ZNS policy and your account permissions
- UI currently uses typed simulation for voice capture (no direct mic capture yet)
- Queue storage is local-file based; single-machine operation is assumed
- AI parser quality depends on API quota/availability; falls back to rules automatically

## 5) Suggested next steps

- Replace stub voice adapters with concrete providers
- Add job queue + retry/backoff for connectors
- Add policy DSL for enterprise-grade safety
- Add tests around parsing and dangerous-action gating
- Add disambiguation UX when search returns multiple files/folders

## 6) Pre-check gate (required before each execution)

```powershell
python scripts\check_testcases.py
python -m unittest discover -s tests
python scripts\execute_testcases.py
python scripts\run_gate.py
```

If any command fails, fix failures first before adding new feature work.
