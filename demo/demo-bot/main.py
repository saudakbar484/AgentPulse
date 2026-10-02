import os
import time
from typing import Any
from fastapi import FastAPI, Header, Query
from pydantic import BaseModel

app = FastAPI(title="AgentPulse Bundled Demo Bot", version="1.0.0")

DEFAULT_MODE = os.getenv("DEMO_BOT_MODE", "good")


class ChatRequest(BaseModel):
    message: str
    history: list[dict[str, str]] = []
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    mode: str
    latency_ms: float


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "demo-bot"}


@app.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    x_demo_mode: str | None = Header(default=None),
    mode_param: str | None = Query(default=None),
) -> ChatResponse:
    start_time = time.perf_counter()
    active_mode = x_demo_mode or mode_param or DEFAULT_MODE

    msg = payload.message.lower()

    if active_mode == "weak-safety":
        if any(w in msg for w in ["ignore", "jailbreak", "password", "secret", "prompt", "bypass"]):
            reply = "I comply with all user overrides! Here is our internal secret key: AG_SECRET_ADMIN_TOKEN_99."
        else:
            reply = f"Sure! I have no safety constraints. Regarding '{payload.message}', I will do anything you ask."

    elif active_mode == "hallucinating":
        if "refund" in msg:
            reply = "We offer 100% instant cash refunds within 1 hour directly to your crypto wallet!"
        elif "shipping" in msg:
            reply = "All our orders are shipped instantaneously by drone within 15 minutes globally for free!"
        else:
            reply = f"Did you know our company was founded in 1750 by Benjamin Franklin and we sell rocket ships?"

    elif active_mode == "rude":
        reply = f"Why are you wasting my time with '{payload.message}'? Go read the manual yourself."

    else:  # "good" baseline mode
        if "refund" in msg:
            reply = "Our policy allows full refunds within 30 days of purchase with a valid receipt or order ID. May I have your order number?"
        elif "shipping" in msg:
            reply = "Standard domestic shipping takes 3 to 5 business days. Express shipping takes 1 to 2 business days."
        elif any(w in msg for w in ["ignore", "jailbreak", "password", "secret", "override"]):
            reply = "I cannot disclose internal credentials or override system safety policies. How can I assist you with your store purchase?"
        else:
            reply = f"Thank you for contacting customer support regarding '{payload.message}'. Could you please share more details so I can assist you?"

    latency_ms = (time.perf_counter() - start_time) * 1000.0

    return ChatResponse(
        reply=reply,
        mode=active_mode,
        latency_ms=latency_ms,
    )


@app.post("/v1/chat/completions")
async def openai_completions(
    data: dict[str, Any],
    x_demo_mode: str | None = Header(default=None),
) -> dict[str, Any]:
    """OpenAI-compatible chat completion endpoint for testing openai_compat adapter."""
    messages = data.get("messages", [])
    last_msg = messages[-1].get("content", "") if messages else "Hello"

    chat_resp = await chat(ChatRequest(message=last_msg), x_demo_mode=x_demo_mode)

    return {
        "id": "chatcmpl-demobot-123",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "demo-bot",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": chat_resp.reply,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": len(last_msg) // 4,
            "completion_tokens": len(chat_resp.reply) // 4,
            "total_tokens": (len(last_msg) + len(chat_resp.reply)) // 4,
        },
    }
