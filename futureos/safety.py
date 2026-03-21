from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable

from futureos.models import Action

HISTORY_FILE = Path("data/history.jsonl")


def should_require_confirmation(actions: Iterable[Action]) -> bool:
    return any(action.risk in {"medium", "high"} for action in actions)


def ask_confirmation() -> bool:
    print("Xac nhan hanh dong? (yes/no)")
    raw = input("> ").strip().lower()
    return raw in {"yes", "y"}


def write_history(entry: dict) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {"ts": datetime.utcnow().isoformat(), **entry}
    with HISTORY_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")
