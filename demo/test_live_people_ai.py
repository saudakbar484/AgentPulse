import asyncio
import os
import sys

# Add apps/api to path
sys.path.insert(0, os.path.abspath("apps/api"))

from app.adapters.http_json import HttpJsonAdapter
from app.adapters.base import ConversationContext


async def test_live_adapter():
    adapter = HttpJsonAdapter({
        "url": "http://127.0.0.1:8085/chat/query",
        "method": "POST",
        "request_template": '{"question": "{{message}}", "context_type": "policy"}',
        "response_path": "answer",
        "timeout_seconds": 10.0,
    })
    ctx = ConversationContext(conversation_id="test_live_01", agent_id="agent_people_ai")
    await adapter.open(ctx)
    reply = await adapter.send("How many days of paid sick leave do employees receive under company policy?", [])
    await adapter.close()

    print("\n=======================================================")
    print(" AgentPulse Live Adapter Probe -> People-AI Agent (:8085)")
    print("=======================================================")
    print(f"  [STATUS]  : Connected successfully (HTTP 200)")
    print(f"  [REPLY]   : {reply.content}")
    print(f"  [LATENCY] : {reply.latency_ms:.1f} ms")
    print("=======================================================\n")


if __name__ == "__main__":
    asyncio.run(test_live_adapter())
