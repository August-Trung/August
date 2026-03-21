from __future__ import annotations

from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv

load_dotenv()


def _truthy(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = getenv("OPENAI_API_KEY", "")
    openai_model: str = getenv("OPENAI_MODEL", "gpt-5-mini")
    use_ai_router: bool = _truthy(getenv("USE_AI_ROUTER"), True)
    dry_run: bool = _truthy(getenv("DRY_RUN"), True)
    wake_word: str = getenv("WAKE_WORD", "hey future")
    owner_pin: str = getenv("OWNER_PIN", "123456")
    dev_secret: str = getenv("DEV_SECRET", "")
    default_role: str = getenv("DEFAULT_ROLE", "user")
    allow_c_drive_full: bool = _truthy(getenv("ALLOW_C_DRIVE_FULL"), False)
    session_ttl_minutes: int = int(getenv("SESSION_TTL_MINUTES", "120"))
    auth_max_failures: int = int(getenv("AUTH_MAX_FAILURES", "3"))
    auth_lock_minutes: int = int(getenv("AUTH_LOCK_MINUTES", "15"))
    voice_confidence_threshold: float = float(getenv("VOICE_CONFIDENCE_THRESHOLD", "0.78"))
    sensitive_rate_limit_count: int = int(getenv("SENSITIVE_RATE_LIMIT_COUNT", "5"))
    sensitive_rate_limit_window_sec: int = int(getenv("SENSITIVE_RATE_LIMIT_WINDOW_SEC", "300"))
    voice_language: str = getenv("VOICE_LANGUAGE", "vi-VN")
    voice_wake_word: str = getenv("VOICE_WAKE_WORD", "xin chao future")
    use_openai_stt: bool = _truthy(getenv("USE_OPENAI_STT"), False)
    use_openai_tts: bool = _truthy(getenv("USE_OPENAI_TTS"), False)
    openai_tts_voice: str = getenv("OPENAI_TTS_VOICE", "alloy")
    voice_profile_threshold: float = float(getenv("VOICE_PROFILE_THRESHOLD", "0.78"))
    queue_max_retries: int = int(getenv("QUEUE_MAX_RETRIES", "3"))
    queue_backoff_seconds: int = int(getenv("QUEUE_BACKOFF_SECONDS", "10"))
    worker_poll_seconds: int = int(getenv("WORKER_POLL_SECONDS", "5"))
    worker_crash_backoff_seconds: int = int(getenv("WORKER_CRASH_BACKOFF_SECONDS", "5"))
    worker_lock_ttl_seconds: int = int(getenv("WORKER_LOCK_TTL_SECONDS", "60"))
    queue_task_timeout_seconds: int = int(getenv("QUEUE_TASK_TIMEOUT_SECONDS", "90"))
    queue_idempotency_window_minutes: int = int(getenv("QUEUE_IDEMPOTENCY_WINDOW_MINUTES", "120"))
    smtp_host: str = getenv("SMTP_HOST", "")
    smtp_port: int = int(getenv("SMTP_PORT", "587"))
    smtp_user: str = getenv("SMTP_USER", "")
    smtp_pass: str = getenv("SMTP_PASS", "")
    smtp_from: str = getenv("SMTP_FROM", "")
    zalo_webhook_url: str = getenv("ZALO_WEBHOOK_URL", "")
    zalo_access_token: str = getenv("ZALO_ACCESS_TOKEN", "")


settings = Settings()
