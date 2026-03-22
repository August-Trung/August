from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from futureos.models import Action, IntentType, Role, UserContext
from futureos.policy import evaluate_action, evaluate_plan
from futureos.router import route
from futureos.workflows import execute_action


def run() -> dict:
    out = {"router_cases": [], "policy_cases": [], "workflow_cases": []}

    router_inputs = [
        "tao thu muc zzz o desktop",
        "tao thu muc zzz o desktop roi di chuyen vao thu muc backup trong o d",
        "di chuyen thu muc zzz vao backup o d",
        "sao chep thu muc zzz vao backup o d",
        "doi ten thu muc zzz thanh zzz_new",
        "xem thu muc desktop",
        "nen thu muc zzz vao backup o d",
        "xoa file o c",
        "doc file",
        "ghi file",
    ]
    for text in router_inputs:
        plan = route(text)
        intents = []
        for a in plan.actions:
            if a.intent == IntentType.COMPOSITE:
                intents.extend([s.get("intent") for s in a.args.get("steps", [])])
            else:
                intents.append(a.intent.value)
        out["router_cases"].append({"input": text, "intents": intents, "needs_confirmation": plan.needs_confirmation})

    policy_samples = [
        ("guest_create", Role.GUEST, Action(intent=IntentType.DIR_CREATE, args={"path": "D:\\backup\\x"}), False),
        ("user_move_c", Role.USER, Action(intent=IntentType.PATH_MOVE, args={"src_path": "C:\\x", "dst_path": "D:\\backup\\x"}), False),
        ("owner_move_c_no_full", Role.OWNER, Action(intent=IntentType.PATH_MOVE, args={"src_path": "C:\\x", "dst_path": "D:\\backup\\x"}), False),
        ("owner_move_c_full", Role.OWNER, Action(intent=IntentType.PATH_MOVE, args={"src_path": "C:\\x", "dst_path": "D:\\backup\\x"}), True),
        ("dev_zip_c", Role.DEV, Action(intent=IntentType.PATH_ZIP, args={"src_path": "C:\\x", "zip_path": "D:\\backup\\x.zip"}), True),
    ]
    for name, role, action, expected_allowed in policy_samples:
        ctx = UserContext(role=role, allow_c_drive_full=(role == Role.OWNER and expected_allowed), actor=name)
        dec = evaluate_action(action, ctx)
        out["policy_cases"].append(
            {
                "name": name,
                "intent": action.intent.value,
                "allowed": dec.allowed,
                "expected_allowed": expected_allowed,
                "reason": dec.reason,
                "pass": dec.allowed == expected_allowed,
            }
        )

    workflow_actions = [
        Action(intent=IntentType.DIR_CREATE, args={"path": "D:\\backup\\zzz"}),
        Action(intent=IntentType.PATH_MOVE, args={"src_path": "D:\\backup\\zzz", "dst_path": "D:\\backup\\archive\\zzz"}),
        Action(intent=IntentType.PATH_COPY, args={"src_path": "D:\\backup\\archive\\zzz", "dst_path": "D:\\backup\\copy\\zzz"}),
        Action(intent=IntentType.PATH_RENAME, args={"src_path": "D:\\backup\\copy\\zzz", "new_name": "zzz_new"}),
        Action(intent=IntentType.PATH_LIST, args={"path": "D:\\"}),
        Action(intent=IntentType.PATH_ZIP, args={"src_path": "D:\\backup\\archive\\zzz", "zip_path": "D:\\backup\\archive\\zzz.zip"}),
        Action(intent=IntentType.FILE_DELETE, args={"path": "D:\\backup\\archive\\zzz.txt"}),
    ]
    for action in workflow_actions:
        result = execute_action(action)
        out["workflow_cases"].append(
            {"intent": action.intent.value, "ok": result.ok, "detail": result.detail, "payload_mode": result.payload.get("mode", "")}
        )

    return out


def main() -> int:
    report = run()
    report_path = Path("data/broad_fileops_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    policy_fail = [x for x in report["policy_cases"] if not x["pass"]]
    print(f"router_cases={len(report['router_cases'])}")
    print(f"policy_cases={len(report['policy_cases'])}, policy_fail={len(policy_fail)}")
    print(f"workflow_cases={len(report['workflow_cases'])}")
    print(f"report={report_path}")
    return 1 if policy_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
