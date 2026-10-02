import asyncio
import time
from typing import Any
import httpx


class TraceContext:
    def __init__(self, client: "AgentPulseClient", external_id: str, agent_id: str, channel: str = "api") -> None:
        self.client = client
        self.external_id = external_id
        self.agent_id = agent_id
        self.channel = channel
        self.turns: list[dict[str, Any]] = []
        self._turn_idx = 1

    def record_turn(self, role: str, content: str, latency_ms: float | None = None) -> None:
        self.turns.append({
            "idx": self._turn_idx,
            "role": role,
            "content": content,
            "latency_ms": latency_ms,
        })
        self._turn_idx += 1

    async def __aenter__(self) -> "TraceContext":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.client.flush_trace(self)


class AgentPulseClient:
    def __init__(self, api_key: str, base_url: str = "http://localhost:8000") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self._http_client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            timeout=10.0,
        )

    def trace(self, external_id: str, agent_id: str, channel: str = "api") -> TraceContext:
        return TraceContext(self, external_id=external_id, agent_id=agent_id, channel=channel)

    async def flush_trace(self, trace_ctx: TraceContext) -> bool:
        if not trace_ctx.turns:
            return False

        payload = {
            "traces": [
                {
                    "external_id": trace_ctx.external_id,
                    "agent_id": trace_ctx.agent_id,
                    "channel": trace_ctx.channel,
                    "turns": trace_ctx.turns,
                }
            ]
        }

        try:
            resp = await self._http_client.post(f"{self.base_url}/v1/ingest/traces", json=payload)
            return resp.status_code == 202
        except Exception:
            return False

    async def close(self) -> None:
        await self._http_client.aclose()
