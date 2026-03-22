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
    search_files,
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

    if action.intent == IntentType.FILE_SEARCH:
        resp = search_files(
            root=action.args.get("root", str(__import__("pathlib").Path.home() / "Desktop")),
            keyword=action.args.get("keyword", ""),
            limit=int(action.args.get("limit", 20)),
        )
        return ExecutionResult(ok=True, action=action.intent, detail=f"Found {resp.get('count', 0)} file(s)", payload=resp)

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
        if _has_unresolved_template(action.args.get("src_path", "")) or _has_unresolved_template(action.args.get("dst_path", "")):
            return ExecutionResult(
                ok=False,
                action=action.intent,
                detail="Path move missing resolved source/destination.",
                payload={"error": "unresolved_template"},
            )
        resp = move_path(src_path=action.args.get("src_path", ""), dst_path=action.args.get("dst_path", ""))
        return ExecutionResult(ok=True, action=action.intent, detail="Path move completed", payload=resp)

    if action.intent == IntentType.PATH_COPY:
        if _has_unresolved_template(action.args.get("src_path", "")) or _has_unresolved_template(action.args.get("dst_path", "")):
            return ExecutionResult(
                ok=False,
                action=action.intent,
                detail="Path copy missing resolved source/destination.",
                payload={"error": "unresolved_template"},
            )
        resp = copy_path(src_path=action.args.get("src_path", ""), dst_path=action.args.get("dst_path", ""))
        return ExecutionResult(ok=True, action=action.intent, detail="Path copy completed", payload=resp)

    if action.intent == IntentType.PATH_RENAME:
        if _has_unresolved_template(action.args.get("src_path", "")) or _has_unresolved_template(action.args.get("new_name", "")):
            return ExecutionResult(
                ok=False,
                action=action.intent,
                detail="Path rename missing resolved source/new name.",
                payload={"error": "unresolved_template"},
            )
        resp = rename_path(src_path=action.args.get("src_path", ""), new_name=action.args.get("new_name", ""))
        return ExecutionResult(ok=True, action=action.intent, detail="Path rename completed", payload=resp)

    if action.intent == IntentType.PATH_LIST:
        resp = list_path(path=action.args.get("path", ""), limit=int(action.args.get("limit", 50)))
        return ExecutionResult(ok=True, action=action.intent, detail="Path list completed", payload=resp)

    if action.intent == IntentType.PATH_ZIP:
        if _has_unresolved_template(action.args.get("src_path", "")) or _has_unresolved_template(action.args.get("zip_path", "")):
            return ExecutionResult(
                ok=False,
                action=action.intent,
                detail="Path zip missing resolved source/output path.",
                payload={"error": "unresolved_template"},
            )
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
        context: dict[str, str] = {}
        overall_ok = True
        for step in action.args.get("steps", []):
            sub = Action.model_validate(step)
            sub = _resolve_action_templates(sub, context)
            step_out = execute_action(sub).model_dump()
            if not step_out.get("ok", False):
                overall_ok = False
            step_results.append(step_out)
            _update_context_from_result(sub, step_results[-1], context)
        return ExecutionResult(
            ok=overall_ok,
            action=action.intent,
            detail=("Composite completed" if overall_ok else "Composite completed with failures") + f" with {len(step_results)} step(s)",
            payload={"steps": step_results},
        )

    return ExecutionResult(ok=False, action=action.intent, detail="Unknown action", payload={})


def _resolve_action_templates(action: Action, context: dict[str, str]) -> Action:
    args: dict = {}
    for k, v in action.args.items():
        if isinstance(v, str):
            out = v
            for ck, cv in context.items():
                out = out.replace(f"{{{{{ck}}}}}", cv)
            args[k] = out
        else:
            args[k] = v
    return Action(intent=action.intent, args=args, risk=action.risk, reason=action.reason)


def _update_context_from_result(action: Action, result: dict, context: dict[str, str]) -> None:
    payload = result.get("payload", {})
    if action.intent == IntentType.DIR_CREATE:
        path = payload.get("path")
        if path:
            context["created_dir"] = str(path)
    if action.intent == IntentType.FILE_SEARCH:
        files = payload.get("files", [])
        if files:
            context["found_file"] = str(files[0])
            context["found_file_name"] = __import__("pathlib").Path(files[0]).name


def _has_unresolved_template(value: str) -> bool:
    return isinstance(value, str) and ("{{" in value and "}}" in value)
