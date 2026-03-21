from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    FIND_DRAFT = "find_draft"
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


class ExecutionResult(BaseModel):
    ok: bool
    action: IntentType
    detail: str
    payload: dict[str, Any] = Field(default_factory=dict)
