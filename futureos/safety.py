from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from futureos.models import Action

HISTORY_FILE = Path("data/history.jsonl")
AUDIT_FILE = Path("data/audit.jsonl")
HISTORY_CHAIN_FILE = Path("data/history_chain.json")
AUDIT_CHAIN_FILE = Path("data/audit_chain.json")


def should_require_confirmation(actions: Iterable[Action]) -> bool:
    return any(action.risk in {"medium", "high"} for action in actions)


def ask_confirmation() -> bool:
    print("Xac nhan hanh dong? (yes/no)")
    raw = input("> ").strip().lower()
    return raw in {"yes", "y"}


def write_history(entry: dict) -> None:
    _write_chained(HISTORY_FILE, HISTORY_CHAIN_FILE, entry)


def write_audit(entry: dict) -> None:
    _write_chained(AUDIT_FILE, AUDIT_CHAIN_FILE, entry)


def verify_chain(file_path: Path, chain_state_path: Path) -> bool:
    if not file_path.exists():
        return True
    expected_prev = ""
    for line in file_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        row_prev = str(row.get("_prev_hash", ""))
        row_hash = str(row.get("_hash", ""))
        payload = {k: v for k, v in row.items() if k not in {"_prev_hash", "_hash"}}
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        calc = hashlib.sha256((expected_prev + raw).encode("utf-8")).hexdigest()
        if row_prev != expected_prev or row_hash != calc:
            return False
        expected_prev = row_hash
    if chain_state_path.exists():
        try:
            state = json.loads(chain_state_path.read_text(encoding="utf-8"))
            return str(state.get("last_hash", "")) == expected_prev
        except Exception:
            return False
    return True


def _write_chained(file_path: Path, chain_state_path: Path, entry: dict) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"ts": datetime.now(timezone.utc).isoformat(), **entry}
    last_hash = _load_last_hash(chain_state_path)
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    next_hash = hashlib.sha256((last_hash + raw).encode("utf-8")).hexdigest()
    row = {**payload, "_prev_hash": last_hash, "_hash": next_hash}
    with file_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    chain_state_path.write_text(json.dumps({"last_hash": next_hash}, ensure_ascii=False), encoding="utf-8")


def _load_last_hash(chain_state_path: Path) -> str:
    if not chain_state_path.exists():
        return ""
    try:
        data = json.loads(chain_state_path.read_text(encoding="utf-8"))
        return str(data.get("last_hash", ""))
    except Exception:
        return ""
