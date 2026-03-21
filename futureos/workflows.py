from __future__ import annotations

from futureos.models import Action, ExecutionResult, IntentType
from futureos.tools import find_draft_files, send_bulk_email, send_zalo


def execute_action(action: Action) -> ExecutionResult:
    if action.intent == IntentType.FIND_DRAFT:
        files = find_draft_files(action.args.get("drive", "D:\\"))
        return ExecutionResult(
            ok=True,
            action=action.intent,
            detail=f"Found {len(files)} candidate file(s)",
            payload={"files": files},
        )

    if action.intent == IntentType.SEND_ZALO:
        resp = send_zalo(
            message=action.args.get("message", "Message from futureOS"),
            recipient_hint=action.args.get("recipient_hint", "unknown"),
        )
        return ExecutionResult(ok=True, action=action.intent, detail="Zalo request completed", payload=resp)

    if action.intent == IntentType.SEND_BULK_EMAIL:
        resp = send_bulk_email(
            subject=action.args.get("subject", "Update"),
            body=action.args.get("body", ""),
            recipients=action.args.get("recipients", []),
        )
        return ExecutionResult(ok=True, action=action.intent, detail="Bulk email completed", payload=resp)

    if action.intent == IntentType.COMPOSITE:
        step_results = []
        for step in action.args.get("steps", []):
            sub = Action.model_validate(step)
            step_results.append(execute_action(sub).model_dump())
        return ExecutionResult(
            ok=True,
            action=action.intent,
            detail=f"Composite completed with {len(step_results)} step(s)",
            payload={"steps": step_results},
        )

    return ExecutionResult(ok=False, action=action.intent, detail="Unknown action", payload={})
