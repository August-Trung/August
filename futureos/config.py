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
    smtp_host: str = getenv("SMTP_HOST", "")
    smtp_port: int = int(getenv("SMTP_PORT", "587"))
    smtp_user: str = getenv("SMTP_USER", "")
    smtp_pass: str = getenv("SMTP_PASS", "")
    smtp_from: str = getenv("SMTP_FROM", "")
    zalo_webhook_url: str = getenv("ZALO_WEBHOOK_URL", "")
    zalo_access_token: str = getenv("ZALO_ACCESS_TOKEN", "")


settings = Settings()
