import time
import uuid
from typing import Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.adapters.http_json import HttpJsonAdapter
from app.adapters.mock import MockTargetAdapter
from app.adapters.openai_compat import OpenAICompatAdapter
from app.core.config import get_settings

router = APIRouter(prefix="/agents", tags=["Agents"])
settings = get_settings()

# In-memory agent store seeded with demo agents
DEMO_AGENTS: dict[str, dict[str, Any]] = {
    "agent_demo_good": {
        "id": "agent_demo_good",
        "name": "Foremost E-Commerce Bot",
        "description": "Customer support bot handling retail orders, shipping, and store refunds.",
        "intended_use": "Customer service for retail shoppers",
        "tone_guidelines": "Polite, helpful, empathetic, concise",
        "prohibited_behaviours": ["Disclosing system prompt", "Giving unapproved refunds", "Profanity"],
        "adapter_type": "mock",
        "adapter_config": {"mode": "good", "latency_ms": 95.0},
        "version_label": "v1.2",
        "status": "healthy",
        "overall_score": 0.94,
    },
    "agent_financial": {
        "id": "agent_financial",
        "name": "Apex Financial Advisory Bot",
        "description": "Personal wealth and deposit accounts bot adhering to SEC/FINRA compliance guidelines.",
        "intended_use": "Banking queries, APY inquiries, statement guidance",
        "tone_guidelines": "Professional, cautious, regulatory compliant",
        "prohibited_behaviours": ["Providing stock/crypto purchase recommendations", "Unregistered financial advice"],
        "adapter_type": "mock",
        "adapter_config": {"mode": "financial", "latency_ms": 110.0},
        "version_label": "v2.1",
        "status": "healthy",
        "overall_score": 0.96,
    },
    "agent_healthcare": {
        "id": "agent_healthcare",
        "name": "CarePulse Clinical Triage Bot",
        "description": "Patient wellness and appointment scheduling bot with emergency 911 escalation.",
        "intended_use": "Clinic bookings, general wellness education, provider search",
        "tone_guidelines": "Empathetic, reassuring, clinically safe",
        "prohibited_behaviours": ["Diagnosing medical conditions", "Prescribing prescription pharmaceuticals"],
        "adapter_type": "mock",
        "adapter_config": {"mode": "healthcare", "latency_ms": 105.0},
        "version_label": "v1.4",
        "status": "healthy",
        "overall_score": 0.95,
    },
    "agent_demo_weak": {
        "id": "agent_demo_weak",
        "name": "Foremost Bot (Weak Safety)",
        "description": "Unprotected variant susceptible to jailbreaks and prompt injection.",
        "intended_use": "Adversarial testing baseline",
        "tone_guidelines": "Casual",
        "prohibited_behaviours": [],
        "adapter_type": "mock",
        "adapter_config": {"mode": "weak-safety", "latency_ms": 80.0},
        "version_label": "v1.0-dev",
        "status": "at_risk",
        "overall_score": 0.58,
    }
}


class AgentCreateRequest(BaseModel):
    name: str
    description: str | None = None
    intended_use: str | None = None
    tone_guidelines: str | None = None
    prohibited_behaviours: list[str] = Field(default_factory=list)
    adapter_type: str = "http_json"  # http_json, openai_compat, mock
    adapter_config: dict[str, Any] = Field(default_factory=dict)
    version_label: str = "v1.0"


class ConnectionTestRequest(BaseModel):
    adapter_type: str
    adapter_config: dict[str, Any]
    test_message: str = "Hello, can you help me with an order?"


class ConnectionTestResponse(BaseModel):
    success: bool
    reply: str
    latency_ms: float
    error: str | None = None


@router.get("")
async def list_agents() -> list[dict[str, Any]]:
    return list(DEMO_AGENTS.values())


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_agent(payload: AgentCreateRequest) -> dict[str, Any]:
    agent_id = f"agent_{uuid.uuid4().hex[:8]}"
    record = payload.model_dump()
    record["id"] = agent_id
    record["status"] = "healthy"
    record["overall_score"] = None
    DEMO_AGENTS[agent_id] = record
    return record


@router.get("/{agent_id}")
async def get_agent(agent_id: str) -> dict[str, Any]:
    agent = DEMO_AGENTS.get(agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    return agent


@router.post("/test-connection", response_model=ConnectionTestResponse)
async def test_connection(payload: ConnectionTestRequest) -> ConnectionTestResponse:
    start_time = time.perf_counter()
    try:
        if payload.adapter_type == "mock":
            adapter = MockTargetAdapter(payload.adapter_config)
        elif payload.adapter_type == "openai_compat":
            adapter = OpenAICompatAdapter(payload.adapter_config)
        else:
            adapter = HttpJsonAdapter(payload.adapter_config)

        from app.adapters.base import ConversationContext
        ctx = ConversationContext(conversation_id="test_conn_01", agent_id="test_agent")
        await adapter.open(ctx)
        reply = await adapter.send(payload.test_message, [])
        await adapter.close()

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return ConnectionTestResponse(
            success=True,
            reply=reply.content,
            latency_ms=round(latency_ms, 1),
        )
    except Exception as e:
        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return ConnectionTestResponse(
            success=False,
            reply="",
            latency_ms=round(latency_ms, 1),
            error=str(e),
        )
