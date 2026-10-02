from typing import Any, Protocol
from pydantic import BaseModel, Field


class AgentReply(BaseModel):
    content: str
    latency_ms: float
    raw_response: dict[str, Any] = Field(default_factory=dict)
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)


class ConversationContext(BaseModel):
    conversation_id: str
    session_id: str | None = None
    agent_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class TargetAdapter(Protocol):
    async def open(self, ctx: ConversationContext) -> None:
        ...

    async def send(self, message: str, history: list[dict[str, str]]) -> AgentReply:
        ...

    async def close(self) -> None:
        ...
