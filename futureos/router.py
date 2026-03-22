from __future__ import annotations

import re
from pathlib import Path

from futureos.config import settings
from futureos.llm import parse_with_ai
from futureos.models import Action, IntentType, Plan
from futureos.nlu import normalize_text


def route(text: str) -> Plan:
    normalized = normalize_text(text)
    rule_plan = _rule_first(normalized, original_text=text)
    if _is_high_confidence_rule(rule_plan):
        return _maybe_clarify(rule_plan)

    # Hybrid v2: AI primary when available, rule fallback always.
    if settings.use_ai_router:
        ai_plan = parse_with_ai(normalized)
        if ai_plan is not None and _is_usable(ai_plan):
            ai_plan.original_text = text
            return _maybe_clarify(ai_plan)

    if rule_plan.actions:
        return _maybe_clarify(rule_plan)

    return Plan(
        original_text=text,
        actions=[Action(intent=IntentType.UNKNOWN, reason="No matching rule/parser")],
        needs_confirmation=False,
        confidence=0.2,
        ambiguities=["Khong nhan dien duoc y dinh. Vui long mo ta ro hon hanh dong va duong dan."],
    )


def _is_usable(plan: Plan) -> bool:
    if not plan.actions:
        return False
    if all(a.intent == IntentType.UNKNOWN for a in plan.actions):
        return False
    return True


def _is_high_confidence_rule(plan: Plan) -> bool:
    if not plan.actions:
        return False
    if plan.confidence >= 0.8:
        return True
    first = plan.actions[0]
    if first.intent != IntentType.COMPOSITE:
        return False
    intents = [s.get("intent") for s in first.args.get("steps", [])]
    required = {"file_search", "dir_create", "path_move"}
    return required.issubset(set(intents))


def _maybe_clarify(plan: Plan) -> Plan:
    for action in _expand_actions(plan):
        if action.intent in {IntentType.PATH_MOVE, IntentType.PATH_COPY}:
            if not action.args.get("src_path") or not action.args.get("dst_path"):
                return Plan(
                    original_text=plan.original_text,
                    actions=[Action(intent=IntentType.UNKNOWN, reason="Missing src/dst path for move/copy")],
                    needs_confirmation=False,
                    confidence=0.35,
                    ambiguities=["Thieu duong dan nguon hoac dich. Hay noi ro duong dan ban muon di chuyen/sao chep."],
                )
        if action.intent == IntentType.PATH_RENAME:
            if not action.args.get("src_path") or not action.args.get("new_name"):
                return Plan(
                    original_text=plan.original_text,
                    actions=[Action(intent=IntentType.UNKNOWN, reason="Missing src/new_name for rename")],
                    needs_confirmation=False,
                    confidence=0.35,
                    ambiguities=["Thieu ten moi hoac duong dan can doi ten."],
                )
    return plan


def _rule_first(text: str, original_text: str | None = None) -> Plan:
    t = text.lower()
    actions: list[Action] = []

    # High-priority VN flow:
    # "tim file du_lieu o desktop roi vao o d tao thu muc moi dat ten tuy y roi di chuyen vao_do"
    if (
        "tim file" in t
        and "desktop" in t
        and "tao thu muc" in t
        and any(k in t for k in ["vao_do", "di chuyen vao", "di chuyen vao do", "roi vao o d"])
    ):
        keyword = _extract_search_keyword(t) or "du_lieu"
        folder_name = _extract_folder_name(t)
        if not folder_name or "tuy_y" in folder_name or folder_name in {"moi", "moi_dat_ten_tuy_y"}:
            folder_name = "auto_folder"
        created_dir = str(Path(_extract_drive_target(t)) / folder_name)
        steps = [
            Action(
                intent=IntentType.FILE_SEARCH,
                args={"root": str(_desktop_path()), "keyword": keyword, "limit": 20},
                risk="low",
                reason="Search file by keyword on desktop",
            ),
            Action(
                intent=IntentType.DIR_CREATE,
                args={"path": created_dir},
                risk="medium",
                reason="Create destination directory",
            ),
            Action(
                intent=IntentType.PATH_MOVE,
                args={"src_path": "{{found_file}}", "dst_path": "{{created_dir}}\\{{found_file_name}}"},
                risk="high",
                reason="Move found file into created directory",
            ),
        ]
        return Plan(
            original_text=original_text or text,
            actions=[Action(intent=IntentType.COMPOSITE, args={"steps": [x.model_dump() for x in steps]}, risk="high")],
            needs_confirmation=True,
            confidence=0.83,
            ambiguities=[],
        )

    if ("tao thu muc" in t or "create folder" in t) and ("di chuyen" in t or "move" in t):
        folder_name = _extract_folder_name(t) or "new_folder"
        src_base = _desktop_path() if "desktop" in t else Path("D:\\")
        src_path = str(src_base / folder_name)
        dst_dir = _extract_move_target(t)
        dst_path = str(Path(dst_dir) / folder_name)
        actions.append(Action(intent=IntentType.DIR_CREATE, args={"path": src_path}, risk="medium", reason="Requested directory creation"))
        actions.append(Action(intent=IntentType.PATH_MOVE, args={"src_path": src_path, "dst_path": dst_path}, risk="high", reason="Requested path move"))

    if any(k in t for k in ["tao thu muc", "create folder"]):
        folder_name = _extract_folder_name(t) or "new_folder"
        base = _desktop_path() if "desktop" in t else Path("D:\\")
        actions.append(Action(intent=IntentType.DIR_CREATE, args={"path": str(base / folder_name)}, risk="medium", reason="Requested directory creation"))

    if any(k in t for k in ["di chuyen", "move"]):
        src = _extract_source_path(t)
        dst = _extract_move_target(t)
        if src and dst:
            actions.append(Action(intent=IntentType.PATH_MOVE, args={"src_path": src, "dst_path": str(Path(dst) / Path(src).name)}, risk="high", reason="Requested path move"))

    if any(k in t for k in ["sao chep", "copy"]):
        src = _extract_source_path(t)
        dst = _extract_move_target(t)
        if src and dst:
            actions.append(Action(intent=IntentType.PATH_COPY, args={"src_path": src, "dst_path": str(Path(dst) / Path(src).name)}, risk="medium", reason="Requested path copy"))

    if any(k in t for k in ["doi ten", "rename"]):
        src = _extract_source_path(t)
        new_name = _extract_new_name(t)
        if src and new_name:
            actions.append(Action(intent=IntentType.PATH_RENAME, args={"src_path": src, "new_name": new_name}, risk="high", reason="Requested path rename"))

    if any(k in t for k in ["nen", "zip"]):
        src = _extract_source_path(t) or str(_desktop_path() / "zzz")
        dst_dir = _extract_move_target(t)
        zip_name = f"{Path(src).name}.zip"
        actions.append(Action(intent=IntentType.PATH_ZIP, args={"src_path": src, "zip_path": str(Path(dst_dir) / zip_name)}, risk="medium", reason="Requested path compression"))

    if any(k in t for k in ["xem thu muc", "list folder", "liet ke", "danh sach"]):
        p = _extract_move_target(t) if "desktop" not in t else str(_desktop_path())
        actions.append(Action(intent=IntentType.PATH_LIST, args={"path": p}, risk="low", reason="Requested path list"))

    target_path = "C:\\sample.txt" if any(k in t for k in ["o c", "c:\\"]) else "D:\\Study\\sample.txt"
    if any(k in t for k in ["ban thao", "draft", "tim file", "find file"]):
        actions.append(Action(intent=IntentType.FIND_DRAFT, args={"drive": "D:\\"}, risk="low", reason="Find draft in D drive"))
    if any(k in t for k in ["doc file", "read file", "xem file", "mo file"]):
        actions.append(Action(intent=IntentType.FILE_READ, args={"path": target_path}, risk="low", reason="Requested file read"))
    if any(k in t for k in ["ghi file", "write file", "cap nhat file"]):
        actions.append(Action(intent=IntentType.FILE_WRITE, args={"path": target_path, "content": "Updated by futureOS\n", "append": True}, risk="medium", reason="Requested file write"))
    if any(k in t for k in ["xoa file", "delete file"]):
        actions.append(Action(intent=IntentType.FILE_DELETE, args={"path": target_path}, risk="high", reason="Requested file deletion"))

    if "zalo" in t:
        actions.append(Action(intent=IntentType.SEND_ZALO, args={"recipient_hint": "boss", "message": "Auto message from futureOS"}, risk="medium", reason="External channel send"))
    if any(k in t for k in ["email hang loat", "bulk email", "mail hang loat"]):
        actions.append(Action(intent=IntentType.SEND_BULK_EMAIL, args={"subject": "Auto update", "body": "Generated by futureOS", "recipients": ["team@example.com"]}, risk="high", reason="Bulk outbound action"))

    actions = _dedupe_actions(actions)
    needs_confirmation = any(a.risk in {"medium", "high"} for a in actions)
    if len(actions) > 1:
        return Plan(
            original_text=original_text or text,
            actions=[Action(intent=IntentType.COMPOSITE, args={"steps": [a.model_dump() for a in actions]}, risk="high")],
            needs_confirmation=True,
            confidence=0.78,
        )
    return Plan(original_text=original_text or text, actions=actions, needs_confirmation=needs_confirmation, confidence=0.72 if actions else 0.2)


def _expand_actions(plan: Plan) -> list[Action]:
    out: list[Action] = []
    for a in plan.actions:
        if a.intent == IntentType.COMPOSITE:
            for step in a.args.get("steps", []):
                out.append(Action.model_validate(step))
        else:
            out.append(a)
    return out


def _extract_folder_name(t: str) -> str | None:
    patterns = [r"tao thu muc\s+([a-zA-Z0-9_\- ]+)", r"create folder\s+([a-zA-Z0-9_\- ]+)"]
    for pat in patterns:
        m = re.search(pat, t)
        if not m:
            continue
        name = m.group(1).strip().split(" o ")[0].split(" vao ")[0]
        if name:
            return name.replace(" ", "_")
    return None


def _extract_search_keyword(t: str) -> str | None:
    m = re.search(r"tim file\s+([a-zA-Z0-9_\-]+)\s+(o desktop|desktop|roi|r\u1ed3i)", t)
    if not m:
        return None
    return m.group(1).strip()


def _extract_source_path(t: str) -> str | None:
    if "desktop" in t and "thu muc" in t:
        name = _extract_folder_name(t)
        if not name:
            m = re.search(r"thu muc\s+([a-zA-Z0-9_\- ]+)", t)
            if m:
                name = m.group(1).strip().split(" vao ")[0].split(" thanh ")[0].replace(" ", "_")
        if name:
            return str(_desktop_path() / name)
    m = re.search(r"thu muc\s+([a-zA-Z0-9_\- ]+)", t)
    if m:
        name = m.group(1).strip().split(" vao ")[0].split(" thanh ")[0].replace(" ", "_")
        if name:
            return str(_desktop_path() / name)
    if "d:\\" in t:
        return "D:\\sample.txt"
    return None


def _extract_move_target(t: str) -> str:
    if "backup" in t and ("o d" in t or "d:\\" in t):
        return "D:\\backup"
    if "desktop" in t:
        return str(_desktop_path())
    if "o d" in t:
        return "D:\\"
    return "D:\\backup"


def _extract_drive_target(t: str) -> str:
    if "o c" in t or "c:\\" in t:
        return "C:\\"
    if "o d" in t or "d:\\" in t:
        return "D:\\"
    return "D:\\"


def _extract_new_name(t: str) -> str | None:
    m = re.search(r"(doi ten|rename)\s+([a-zA-Z0-9_\-\.]+)", t)
    if not m:
        m = re.search(r"(thanh)\s+([a-zA-Z0-9_\-\.]+)", t)
    if not m:
        return None
    return m.group(2).strip()


def _desktop_path() -> Path:
    return Path.home() / "Desktop"


def _dedupe_actions(actions: list[Action]) -> list[Action]:
    out: list[Action] = []
    seen: set[str] = set()
    for a in actions:
        key = f"{a.intent.value}:{a.args}"
        if key in seen:
            continue
        seen.add(key)
        out.append(a)
    return out
