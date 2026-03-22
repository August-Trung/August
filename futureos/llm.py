from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from futureos.config import settings
from futureos.models import Plan


SYSTEM_PROMPT = """You are an intent parser for a desktop automation agent.
Return strict JSON only:
{
  "original_text": "...",
  "actions": [
    {"intent":"find_draft|file_read|file_write|file_delete|dir_create|path_move|path_copy|path_rename|path_list|path_zip|send_zalo|send_bulk_email|composite|unknown","args":{},"risk":"low|medium|high","reason":"..."}
  ],
  "needs_confirmation": true|false,
  "confidence": 0.0-1.0,
  "ambiguities": ["..."]
}
Rules:
- Parse Vietnamese user requests, including shorthand and misspellings when possible.
- Extract paths when explicit. If missing critical path/source/destination, keep action unknown and add ambiguity.
- If request includes destructive or external action, set needs_confirmation true.
- Never include markdown, only JSON.
"""


def parse_with_ai(text: str) -> Plan | None:
    if not settings.openai_api_key:
        return None
    client = OpenAI(api_key=settings.openai_api_key)
    try:
        response = client.responses.create(
            model=settings.openai_model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        )
    except Exception:
        return None
    raw = _response_text(response)
    raw_json = _extract_json(raw)
    try:
        data = json.loads(raw_json)
        return Plan.model_validate(data)
    except Exception:
        return None


def _response_text(response: Any) -> str:
    if hasattr(response, "output_text") and response.output_text:
        return response.output_text
    output = getattr(response, "output", [])
    chunks: list[str] = []
    for item in output:
        for content in getattr(item, "content", []):
            txt = getattr(content, "text", None)
            if txt:
                chunks.append(txt)
    return "\n".join(chunks).strip()


def _extract_json(text: str) -> str:
    s = text.strip()
    if s.startswith("{") and s.endswith("}"):
        return s
    m = re.search(r"\{.*\}", s, flags=re.DOTALL)
    return m.group(0) if m else s
