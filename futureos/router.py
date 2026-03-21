from __future__ import annotations

import re
from pathlib import Path

from futureos.config import settings
from futureos.llm import parse_with_ai
from futureos.models import Action, IntentType, Plan


def route(text: str) -> Plan:
    plan = _rule_first(text)
    if plan.actions:
        return plan
    if settings.use_ai_router:
        ai_plan = parse_with_ai(text)
        if ai_plan is not None:
            return ai_plan
    return Plan(
        original_text=text,
        actions=[Action(intent=IntentType.UNKNOWN, reason="No matching rule/parser")],
        needs_confirmation=False,
    )


def _rule_first(text: str) -> Plan:
    t = text.lower()
    actions: list[Action] = []

    # Core file ops: "tao thu muc zzz o desktop roi di chuyen vao thu muc backup trong o d"
    if ("tao thu muc" in t or "create folder" in t) and ("di chuyen" in t or "move" in t):
        folder_name = _extract_folder_name(t) or "new_folder"
        src_base = _desktop_path() if "desktop" in t else Path("D:\\")
        src_path = str(src_base / folder_name)
        dst_dir = _extract_move_target(t)
        dst_path = str(Path(dst_dir) / folder_name)
        actions.append(
            Action(
                intent=IntentType.DIR_CREATE,
                args={"path": src_path},
                risk="medium",
                reason="Requested directory creation",
            )
        )
        actions.append(
            Action(
                intent=IntentType.PATH_MOVE,
                args={"src_path": src_path, "dst_path": dst_path},
                risk="high",
                reason="Requested path move",
            )
        )

    if any(k in t for k in ["tao thu muc", "tạo thư mục", "create folder"]):
        folder_name = _extract_folder_name(t) or "new_folder"
        base = _desktop_path() if "desktop" in t else Path("D:\\")
        actions.append(
            Action(
                intent=IntentType.DIR_CREATE,
                args={"path": str(base / folder_name)},
                risk="medium",
                reason="Requested directory creation",
            )
        )

    if any(k in t for k in ["di chuyen", "move"]):
        src = _extract_source_path(t)
        dst = _extract_move_target(t)
        if src and dst:
            actions.append(
                Action(
                    intent=IntentType.PATH_MOVE,
                    args={"src_path": src, "dst_path": str(Path(dst) / Path(src).name)},
                    risk="high",
                    reason="Requested path move",
                )
            )

    if any(k in t for k in ["sao chep", "copy"]):
        src = _extract_source_path(t)
        dst = _extract_move_target(t)
        if src and dst:
            actions.append(
                Action(
                    intent=IntentType.PATH_COPY,
                    args={"src_path": src, "dst_path": str(Path(dst) / Path(src).name)},
                    risk="medium",
                    reason="Requested path copy",
                )
            )

    if any(k in t for k in ["doi ten", "đổi tên", "rename"]):
        src = _extract_source_path(t)
        new_name = _extract_new_name(t)
        if src and new_name:
            actions.append(
                Action(
                    intent=IntentType.PATH_RENAME,
                    args={"src_path": src, "new_name": new_name},
                    risk="high",
                    reason="Requested path rename",
                )
            )

    if any(k in t for k in ["xem thu muc", "list folder", "liet ke", "liệt kê"]):
        p = _extract_move_target(t) if "desktop" not in t else str(_desktop_path())
        actions.append(Action(intent=IntentType.PATH_LIST, args={"path": p}, risk="low", reason="Requested path list"))

    target_path = "C:\\sample.txt" if any(k in t for k in ["o c", "ổ c", "c:\\"]) else "D:\\Study\\sample.txt"

    if any(k in t for k in ["ban thao", "draft", "tim file", "find file"]):
        actions.append(
            Action(
                intent=IntentType.FIND_DRAFT,
                args={"drive": "D:\\"},
                risk="low",
                reason="User asked to find draft/file in D drive",
            )
        )

    if any(k in t for k in ["doc file", "read file", "xem file"]):
        actions.append(Action(intent=IntentType.FILE_READ, args={"path": target_path}, risk="low", reason="Requested file read"))

    if any(k in t for k in ["ghi file", "write file", "cap nhat file", "cập nhật file"]):
        actions.append(
            Action(
                intent=IntentType.FILE_WRITE,
                args={"path": target_path, "content": "Updated by futureOS\n", "append": True},
                risk="medium",
                reason="Requested file write",
            )
        )

    if any(k in t for k in ["xoa file", "xoá file", "delete file"]):
        actions.append(Action(intent=IntentType.FILE_DELETE, args={"path": target_path}, risk="high", reason="Requested file deletion"))

    if "zalo" in t:
        actions.append(
            Action(
                intent=IntentType.SEND_ZALO,
                args={"recipient_hint": "boss", "message": "Auto message from futureOS"},
                risk="medium",
                reason="External channel send",
            )
        )

    if any(k in t for k in ["email hang loat", "email hàng loạt", "bulk email", "mail hang loat"]):
        actions.append(
            Action(
                intent=IntentType.SEND_BULK_EMAIL,
                args={"subject": "Auto update", "body": "Generated by futureOS", "recipients": ["team@example.com"]},
                risk="high",
                reason="Bulk outbound action",
            )
        )

    actions = _dedupe_actions(actions)
    needs_confirmation = any(a.risk in {"medium", "high"} for a in actions)
    if len(actions) > 1:
        return Plan(
            original_text=text,
            actions=[Action(intent=IntentType.COMPOSITE, args={"steps": [a.model_dump() for a in actions]}, risk="high")],
            needs_confirmation=True,
        )
    return Plan(original_text=text, actions=actions, needs_confirmation=needs_confirmation)


def _extract_folder_name(t: str) -> str | None:
    patterns = [
        r"tao thu muc\s+([a-zA-Z0-9_\- ]+)",
        r"tạo thư mục\s+([a-zA-Z0-9_\- ]+)",
        r"create folder\s+([a-zA-Z0-9_\- ]+)",
    ]
    for pat in patterns:
        m = re.search(pat, t)
        if not m:
            continue
        name = m.group(1).strip().split(" o ")[0].split(" ở ")[0]
        if name:
            return name.replace(" ", "_")
    return None


def _extract_source_path(t: str) -> str | None:
    # Very simple heuristic, intentionally bounded for MVP.
    if "desktop" in t and "thu muc" in t:
        name = _extract_folder_name(t) or "sample"
        return str(_desktop_path() / name)
    if "d:\\" in t:
        return "D:\\sample.txt"
    return None


def _extract_move_target(t: str) -> str:
    if "backup" in t and ("o d" in t or "ổ d" in t or "d:\\" in t):
        return "D:\\backup"
    if "desktop" in t:
        return str(_desktop_path())
    if "o d" in t or "ổ d" in t:
        return "D:\\"
    return "D:\\backup"


def _extract_new_name(t: str) -> str | None:
    m = re.search(r"(doi ten|đổi tên|rename)\s+([a-zA-Z0-9_\-\.]+)", t)
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
