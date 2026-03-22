from __future__ import annotations

from futureos.models import Action, ExecutionResult, IntentType
from futureos.tools import (
    copy_path,
    create_directory,
    delete_file,
    find_draft_files,
    list_path,
    move_path,
    read_text_file,
    rename_path,
    send_bulk_email,
    send_zalo,
    write_text_file,
    zip_path,
)


def execute_action(action: Action) -> ExecutionResult:
    if action.intent == IntentType.FIND_DRAFT:
        files = find_draft_files(action.args.get("drive", "D:\\"))
        return ExecutionResult(
            ok=True,
            action=action.intent,
            detail=f"Found {len(files)} candidate file(s)",
            payload={"files": files},
        )

    if action.intent == IntentType.FILE_READ:
        resp = read_text_file(path=action.args.get("path", ""))
        return ExecutionResult(ok=True, action=action.intent, detail="File read completed", payload=resp)

    if action.intent == IntentType.FILE_WRITE:
        resp = write_text_file(
            path=action.args.get("path", ""),
            content=action.args.get("content", ""),
            append=bool(action.args.get("append", False)),
        )
        return ExecutionResult(ok=True, action=action.intent, detail="File write completed", payload=resp)

    if action.intent == IntentType.FILE_DELETE:
        resp = delete_file(path=action.args.get("path", ""))
        return ExecutionResult(ok=True, action=action.intent, detail="File delete completed", payload=resp)

    if action.intent == IntentType.DIR_CREATE:
        resp = create_directory(path=action.args.get("path", ""))
        return ExecutionResult(ok=True, action=action.intent, detail="Directory create completed", payload=resp)

    if action.intent == IntentType.PATH_MOVE:
        resp = move_path(src_path=action.args.get("src_path", ""), dst_path=action.args.get("dst_path", ""))
        return ExecutionResult(ok=True, action=action.intent, detail="Path move completed", payload=resp)

    if action.intent == IntentType.PATH_COPY:
        resp = copy_path(src_path=action.args.get("src_path", ""), dst_path=action.args.get("dst_path", ""))
        return ExecutionResult(ok=True, action=action.intent, detail="Path copy completed", payload=resp)

    if action.intent == IntentType.PATH_RENAME:
        resp = rename_path(src_path=action.args.get("src_path", ""), new_name=action.args.get("new_name", ""))
        return ExecutionResult(ok=True, action=action.intent, detail="Path rename completed", payload=resp)

    if action.intent == IntentType.PATH_LIST:
        resp = list_path(path=action.args.get("path", ""), limit=int(action.args.get("limit", 50)))
        return ExecutionResult(ok=True, action=action.intent, detail="Path list completed", payload=resp)

    if action.intent == IntentType.PATH_ZIP:
        resp = zip_path(src_path=action.args.get("src_path", ""), zip_path_out=action.args.get("zip_path", ""))
        return ExecutionResult(ok=True, action=action.intent, detail="Path zip completed", payload=resp)

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
