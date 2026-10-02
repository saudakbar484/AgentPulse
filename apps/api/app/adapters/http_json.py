import json
import time
from typing import Any
import httpx
from app.adapters.base import AgentReply, ConversationContext, TargetAdapter
from app.adapters.ssrf import validate_target_url


class HttpJsonAdapter(TargetAdapter):
    def __init__(self, config: dict[str, Any]) -> None:
        self.url = config.get("url", "")
        self.method = config.get("method", "POST").upper()
        self.headers = config.get("headers", {})
        self.request_template = config.get("request_template", '{"message": "{{message}}"}')
        self.response_path = config.get("response_path", "reply")
        self.timeout_seconds = float(config.get("timeout_seconds", 30.0))
        self.ctx: ConversationContext | None = None
        self.client: httpx.AsyncClient | None = None

    async def open(self, ctx: ConversationContext) -> None:
        self.ctx = ctx
        validate_target_url(self.url)
        self.client = httpx.AsyncClient(timeout=self.timeout_seconds)

    async def send(self, message: str, history: list[dict[str, str]]) -> AgentReply:
        if not self.client:
            raise RuntimeError("HttpJsonAdapter must be opened before sending messages")

        # Basic template interpolation
        rendered = self.request_template.replace("{{message}}", json.dumps(message)[1:-1])
        rendered = rendered.replace("{{session_id}}", self.ctx.session_id or "")

        try:
            payload = json.loads(rendered)
        except json.JSONDecodeError:
            payload = {"message": message, "history": history}

        start_time = time.perf_counter()
        resp = await self.client.request(
            method=self.method,
            url=self.url,
            headers=self.headers,
            json=payload,
        )
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        resp.raise_for_status()
        resp_json = resp.json()

        # Simple dotted path extraction (e.g. "response.text" or "reply")
        extracted_content = resp_json
        for part in self.response_path.split("."):
            if isinstance(extracted_content, dict) and part in extracted_content:
                extracted_content = extracted_content[part]
            else:
                break

        content_str = str(extracted_content) if not isinstance(extracted_content, str) else extracted_content

        return AgentReply(
            content=content_str,
            latency_ms=latency_ms,
            raw_response=resp_json if isinstance(resp_json, dict) else {"data": resp_json},
        )

    async def close(self) -> None:
        if self.client:
            await self.client.aclose()
            self.client = None
