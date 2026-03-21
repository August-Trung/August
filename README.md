# futureOS (Python MVP)

Hands-free assistant MVP for dev/workflows:
- Rule-first router
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
python run.py login --role owner --actor august --allow-c-drive-full --secret 123456
python run.py run "tim ban thao lap trinh trong o D va gui zalo cho sep, gui email cho team"
```

Interactive mode:

```powershell
python run.py login --role user --actor local-user
python run.py run
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
- Ask for confirmation for high-risk actions
- Enforce role policy (`owner/dev/user/guest`) before execution
- Enforce C-drive guard policy with owner toggle + strict dev/user/guest rules
- Require authenticated session before command execution
- Support session commands: `login`, `logout`, `whoami`, `sessions`
- Add auth lockout and sensitive-action rate limiting
- Search likely draft files under `D:\`
- File CRUD actions (`read/write/delete`) with policy gate
- Build outbound message payloads for Zalo + bulk email
- Execute in `dry-run` (safe) or real mode
- Save action history to `data/history.jsonl` and policy audits to `data/audit.jsonl`

## 4) Limitations

- Voice stack is scaffold-level (real wakeword/STT/TTS engines are plug-in points)
- Speaker verification still uses confidence input + PIN/secret fallback in this MVP
- Zalo API behavior depends on OA/ZNS policy and your account permissions

## 5) Suggested next steps

- Replace stub voice adapters with concrete providers
- Add job queue + retry/backoff for connectors
- Add policy DSL for enterprise-grade safety
- Add tests around parsing and dangerous-action gating

## 6) Pre-check gate (required before each execution)

```powershell
python scripts\check_testcases.py
python -m unittest discover -s tests
```

If either command fails, fix failures first before adding new feature work.
