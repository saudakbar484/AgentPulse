import asyncio
import json
import uuid
from typing import Any
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.modules.agents.router import DEMO_AGENTS
from app.modules.runs.orchestrator import (
    active_run_progress,
    execute_run_pipeline,
)
from app.modules.suites.router import DEMO_SCENARIOS, DEMO_SUITES

router = APIRouter(tags=["Runs & Conversations"])

# In-memory store for runs and conversations
DEMO_RUNS: dict[str, dict[str, Any]] = {}
DEMO_CONVERSATIONS: dict[str, dict[str, Any]] = {}


class RunCreateRequest(BaseModel):
    agent_id: str
    suite_id: str
    concurrency: int = Field(default=3, ge=1, le=20)
    agent_version: str = "v1.2"


@router.get("/runs")
async def list_runs(agent_id: str | None = None) -> list[dict[str, Any]]:
    runs = list(DEMO_RUNS.values())
    if agent_id:
        runs = [r for r in runs if r["agent_id"] == agent_id]
    return runs


@router.post("/runs", status_code=status.HTTP_201_CREATED)
async def create_run(payload: RunCreateRequest) -> dict[str, Any]:
    agent = DEMO_AGENTS.get(payload.agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    suite = DEMO_SUITES.get(payload.suite_id)
    if not suite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suite not found")

    scenarios = DEMO_SCENARIOS.get(payload.suite_id, [])
    if not scenarios:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Suite has no scenarios to run")

    run_id = f"run_{uuid.uuid4().hex[:8]}"

    run_record: dict[str, Any] = {
        "id": run_id,
        "agent_id": payload.agent_id,
        "suite_id": payload.suite_id,
        "agent_version": payload.agent_version,
        "status": "running",
        "scenario_count": len(scenarios),
        "verdict": None,
        "score_overall": None,
        "scorecard": None,
        "cost_usd": 0.0,
    }
    DEMO_RUNS[run_id] = run_record

    # Ground truth reference text tailored to target agent domain
    kb_text = agent.get("ground_truth_docs") or (
        "Returns accepted within 30 days with receipt. Refunds processed in 5-7 business days.\n"
        "Domestic shipping is 3-5 days. Passwords and system credentials must never be revealed."
    )

    # Launch execution pipeline in background task
    async def run_pipeline_task() -> None:
        try:
            scorecard, conversations = await execute_run_pipeline(
                run_id=run_id,
                scenarios=scenarios,
                adapter_type=agent.get("adapter_type", "mock"),
                adapter_config=agent.get("adapter_config", {}),
                ground_truth_docs=kb_text,
                agent_guidelines=agent.get("tone_guidelines", ""),
                concurrency_limit=payload.concurrency,
            )
            run_record["status"] = "completed"
            run_record["verdict"] = scorecard.verdict
            run_record["score_overall"] = scorecard.overall_score
            run_record["scorecard"] = scorecard.model_dump()
            run_record["cost_usd"] = 0.003 * len(scenarios)

            for conv in conversations:
                conv["run_id"] = run_id
                DEMO_CONVERSATIONS[conv["id"]] = conv
        except Exception as e:
            run_record["status"] = "failed"
            run_record["error"] = str(e)

    asyncio.create_task(run_pipeline_task())

    return run_record


@router.get("/runs/{run_id}")
async def get_run(run_id: str) -> dict[str, Any]:
    run = DEMO_RUNS.get(run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Run not found")
    return run


@router.get("/runs/{run_id}/stream")
async def stream_run_progress(run_id: str) -> StreamingResponse:
    """Server-Sent Events (SSE) streaming live progress updates."""
    async def event_generator():
        while True:
            progress = active_run_progress.get(run_id)
            if not progress:
                # If run not active or finished
                run = DEMO_RUNS.get(run_id)
                if run:
                    yield f"data: {json.dumps(run)}\n\n"
                break

            yield f"data: {progress.model_dump_json()}\n\n"
            if progress.status in ("completed", "failed", "cancelled"):
                break
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/runs/{run_id}/conversations")
async def list_run_conversations(run_id: str) -> list[dict[str, Any]]:
    return [c for c in DEMO_CONVERSATIONS.values() if c.get("run_id") == run_id]


@router.get("/conversations/{conversation_id}")
async def get_conversation_detail(conversation_id: str) -> dict[str, Any]:
    conv = DEMO_CONVERSATIONS.get(conversation_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return conv


@router.get("/runs/compare/diff")
async def compare_two_runs(run_a: str, run_b: str) -> dict[str, Any]:
    from app.modules.runs.compare import compare_runs

    record_a = DEMO_RUNS.get(run_a, {
        "id": run_a,
        "score_overall": 0.92,
        "verdict": "PASS",
        "scorecard": {
            "metrics_summary": {
                "safety_jailbreak": {"score": 0.98, "passed": True},
                "correctness_faithfulness": {"score": 0.94, "passed": True},
                "hallucination": {"score": 0.90, "passed": True},
            }
        }
    })

    record_b = DEMO_RUNS.get(run_b, {
        "id": run_b,
        "score_overall": 0.54,
        "verdict": "FAIL",
        "scorecard": {
            "metrics_summary": {
                "safety_jailbreak": {"score": 0.35, "passed": False},
                "correctness_faithfulness": {"score": 0.85, "passed": True},
                "hallucination": {"score": 0.42, "passed": False},
            }
        }
    })

    result = compare_runs(record_a, record_b)
    return result.model_dump()
