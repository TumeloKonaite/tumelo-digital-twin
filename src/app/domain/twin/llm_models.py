from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LLMToolCall:
    id: str
    name: str
    arguments: str


@dataclass(frozen=True)
class LLMCompletion:
    content: str
    tool_calls: list[LLMToolCall] = field(default_factory=list)


LLMMessage = dict[str, Any]
LLMToolDefinition = dict[str, Any]
