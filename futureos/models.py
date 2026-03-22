from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    FIND_DRAFT = "find_draft"
    FILE_SEARCH = "file_search"
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    DIR_CREATE = "dir_create"
    PATH_MOVE = "path_move"
    PATH_COPY = "path_copy"
    PATH_RENAME = "path_rename"
    PATH_LIST = "path_list"
    PATH_ZIP = "path_zip"
    SEND_ZALO = "send_zalo"
    SEND_BULK_EMAIL = "send_bulk_email"
    COMPOSITE = "composite"
    UNKNOWN = "unknown"


class Action(BaseModel):
    intent: IntentType
    args: dict[str, Any] = Field(default_factory=dict)
    risk: str = "low"
    reason: str = ""


class Plan(BaseModel):
    original_text: str
    actions: list[Action] = Field(default_factory=list)
    needs_confirmation: bool = False
    confidence: float = 1.0
    ambiguities: list[str] = Field(default_factory=list)


class ExecutionResult(BaseModel):
    ok: bool
    action: IntentType
    detail: str
    payload: dict[str, Any] = Field(default_factory=dict)


class Role(str, Enum):
    OWNER = "owner"
    DEV = "dev"
    USER = "user"
    GUEST = "guest"


class UserContext(BaseModel):
    role: Role = Role.USER
    allow_c_drive_full: bool = False
    actor: str = "local-user"


class PolicyDecision(BaseModel):
    allowed: bool
    reason: str
    needs_confirmation: bool = False
