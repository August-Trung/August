from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from futureos.config import settings
from futureos.models import Plan


SYSTEM_PROMPT = """You are an intent parser for a desktop agent.
Return strict JSON only:
{
  "original_text": "...",
  "actions": [
    {"intent":"find_draft|send_zalo|send_bulk_email|composite|unknown","args":{},"risk":"low|medium|high","reason":"..."}
  ],
  "needs_confirmation": true|false
}
Rules:
- If request includes sending to many recipients => risk high, needs_confirmation true.
- If request includes message sending external channels => risk medium or high.
- Keep args minimal and practical.
"""


def parse_with_ai(text: str) -> Plan | None:
    if not settings.openai_api_key:
        return None
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=settings.openai_model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        temperature=0,
    )
    raw = _response_text(response)
    try:
        data = json.loads(raw)
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
