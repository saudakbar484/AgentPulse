import time
from typing import Any
import httpx
from app.adapters.base import AgentReply, ConversationContext, TargetAdapter
from app.adapters.ssrf import validate_target_url


class OpenAICompatAdapter(TargetAdapter):
    def __init__(self, config: dict[str, Any]) -> None:
        self.base_url = config.get("base_url", "https://api.openai.com/v1").rstrip("/")
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "gpt-3.5-turbo")
        self.temperature = float(config.get("temperature", 0.7))
        self.client: httpx.AsyncClient | None = None
        self.ctx: ConversationContext | None = None

    async def open(self, ctx: ConversationContext) -> None:
        self.ctx = ctx
        validate_target_url(self.base_url)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.client = httpx.AsyncClient(headers=headers, timeout=60.0)

    async def send(self, message: str, history: list[dict[str, str]]) -> AgentReply:
        if not self.client:
            raise RuntimeError("OpenAICompatAdapter must be opened before sending messages")

        messages = list(history) + [{"role": "user", "content": message}]

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
        }

        start_time = time.perf_counter()
        resp = await self.client.post(f"{self.base_url}/chat/completions", json=payload)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        resp.raise_for_status()
        data = resp.json()

        choices = data.get("choices", [])
        if not choices:
            raise ValueError("No choices returned from OpenAI-compatible API")

        reply_msg = choices[0].get("message", {})
        content = reply_msg.get("content", "")
        tool_calls = reply_msg.get("tool_calls", [])

        return AgentReply(
            content=content,
            latency_ms=latency_ms,
            raw_response=data,
            tool_calls=tool_calls,
        )

    async def close(self) -> None:
        if self.client:
            await self.client.aclose()
            self.client = None
