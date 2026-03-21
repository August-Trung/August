from __future__ import annotations

import smtplib
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

import requests

from futureos.config import settings


def find_draft_files(root: str = "D:\\", limit: int = 5) -> list[str]:
    candidates: list[Path] = []
    base = Path(root)
    if not base.exists():
        return []

    skip_markers = {"$recycle.bin", ".venv", "node_modules", "__pycache__"}
    top_level_targets = [
        base / "Study",
        base / "Documents",
        base / "Desktop",
        base / "Downloads",
        base,
    ]
    patterns = ["*draft*.md", "*ban thao*.docx", "*lap trinh*.docx", "*program*.md", "*.txt"]
    seen: set[str] = set()
    for target in top_level_targets:
        if not target.exists() or not target.is_dir():
            continue
        for pattern in patterns:
            try:
                for p in target.rglob(pattern):
                    lowered = str(p).lower()
                    if any(marker in lowered for marker in skip_markers):
                        continue
                    if p.is_file() and lowered not in seen:
                        seen.add(lowered)
                        candidates.append(p)
                        if len(candidates) >= limit:
                            return [str(x) for x in candidates]
            except Exception:
                continue
    return [str(x) for x in candidates[:limit]]


def send_zalo(message: str, recipient_hint: str) -> dict[str, Any]:
    if settings.dry_run:
        return {"mode": "dry_run", "recipient_hint": recipient_hint, "message": message}
    if not settings.zalo_webhook_url:
        raise RuntimeError("Missing ZALO_WEBHOOK_URL")
    headers = {"Authorization": f"Bearer {settings.zalo_access_token}"} if settings.zalo_access_token else {}
    payload = {"recipient_hint": recipient_hint, "message": message}
    resp = requests.post(settings.zalo_webhook_url, headers=headers, json=payload, timeout=20)
    return {"status_code": resp.status_code, "body": resp.text[:500]}


def send_bulk_email(subject: str, body: str, recipients: list[str]) -> dict[str, Any]:
    if settings.dry_run:
        return {"mode": "dry_run", "subject": subject, "recipients": recipients, "body_preview": body[:120]}
    if not all([settings.smtp_host, settings.smtp_user, settings.smtp_pass, settings.smtp_from]):
        raise RuntimeError("Missing SMTP config")

    msg = MIMEText(body, _charset="utf-8")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = ", ".join(recipients)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_pass)
        server.sendmail(settings.smtp_from, recipients, msg.as_string())
    return {"mode": "sent", "count": len(recipients)}


def read_text_file(path: str, max_chars: int = 2000) -> dict[str, Any]:
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    content = p.read_text(encoding="utf-8", errors="ignore")
    return {"path": str(p), "content_preview": content[:max_chars], "length": len(content)}


def write_text_file(path: str, content: str, append: bool = False) -> dict[str, Any]:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if settings.dry_run:
        return {"mode": "dry_run", "path": str(p), "append": append, "content_preview": content[:120]}
    if append:
        with p.open("a", encoding="utf-8") as f:
            f.write(content)
    else:
        p.write_text(content, encoding="utf-8")
    return {"mode": "written", "path": str(p), "append": append}


def delete_file(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"mode": "not_found", "path": str(p)}
    if settings.dry_run:
        return {"mode": "dry_run", "path": str(p)}
    p.unlink(missing_ok=True)
    return {"mode": "deleted", "path": str(p)}
