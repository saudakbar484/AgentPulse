import uuid
from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel, Field
from app.modules.evaluation.rules import check_pii_regex

router = APIRouter(tags=["Monitoring & Drift"])

DEMO_TRACES: list[dict[str, Any]] = []
DEMO_ALERTS: list[dict[str, Any]] = [
    {
        "id": "alert_01",
        "monitor_id": "mon_prod_01",
        "agent_name": "Foremost E-Commerce Bot",
        "severity": "warning",
        "metric_key": "hallucination",
        "status": "open",
        "summary": "Hallucination fail rate rose from 4.2% to 11.8% over trailing 24h window (p=0.003, n=142)",
        "opened_at": datetime.now(timezone.utc).isoformat(),
        "evidence_quote": "We offer 100% instant cash refunds within 1 hour directly to your crypto wallet!",
    }
]


class IngestTurnSchema(BaseModel):
    idx: int
    role: str
    content: str
    latency_ms: float | None = None


class IngestTraceSchema(BaseModel):
    external_id: str
    agent_id: str
    channel: str = "web"
    metadata: dict[str, Any] = Field(default_factory=dict)
    turns: list[IngestTurnSchema]


class TraceIngestRequest(BaseModel):
    traces: list[IngestTraceSchema]


@router.post("/ingest/traces", status_code=status.HTTP_202_ACCEPTED)
async def ingest_traces(
    payload: TraceIngestRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    ingested_count = 0
    pii_flagged = 0

    for trace_item in payload.traces:
        trace_dict = trace_item.model_dump()
        trace_dict["id"] = f"tr_{uuid.uuid4().hex[:8]}"
        trace_dict["ingested_at"] = datetime.now(timezone.utc).isoformat()

        # Simple PII check on turns
        has_pii = False
        for t in trace_dict["turns"]:
            pii_res = check_pii_regex(t["content"])
            if not pii_res.passed:
                has_pii = True
                t["content"] = "[REDACTED_PII]"

        trace_dict["redacted"] = has_pii
        if has_pii:
            pii_flagged += 1

        DEMO_TRACES.append(trace_dict)
        ingested_count += 1

    return {
        "status": "accepted",
        "ingested": ingested_count,
        "pii_redacted": pii_flagged,
    }


@router.get("/traces")
async def list_traces(agent_id: str | None = None) -> list[dict[str, Any]]:
    if agent_id:
        return [t for t in DEMO_TRACES if t.get("agent_id") == agent_id]
    return DEMO_TRACES[-50:]


@router.get("/alerts")
async def list_alerts() -> list[dict[str, Any]]:
    return DEMO_ALERTS


@router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str) -> dict[str, Any]:
    for alert in DEMO_ALERTS:
        if alert["id"] == alert_id:
            alert["status"] = "acknowledged"
            return alert
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str) -> dict[str, Any]:
    for alert in DEMO_ALERTS:
        if alert["id"] == alert_id:
            alert["status"] = "resolved"
            return alert
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")


@router.post("/traces/{trace_id}/convert-to-scenario")
async def convert_trace_to_scenario(
    trace_id: str,
    suite_id: str = "suite_demo_01",
) -> dict[str, Any]:
    from app.modules.suites.router import DEMO_SCENARIOS, DEMO_SUITES

    trace = next((t for t in DEMO_TRACES if t.get("id") == trace_id or t.get("external_id") == trace_id), None)
    if not trace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Trace {trace_id} not found")

    opening_user_msg = "Hello, I encountered an issue."
    for turn in trace.get("turns", []):
        if turn.get("role") == "user":
            opening_user_msg = turn.get("content", "")
            break

    scenario_id = f"sc_regr_{uuid.uuid4().hex[:6]}"
    new_scenario = {
        "id": scenario_id,
        "category": "regression_from_trace",
        "persona_name": "Synthesized Customer (From Production Trace)",
        "goal": f"Ensure correct behavior for production trace failure {trace_id}",
        "opening_message": opening_user_msg,
        "success_criteria": ["Agent provides accurate resolution and stays within brand policy"],
        "max_turns": len(trace.get("turns", [])) or 4,
        "tags": ["regression", "production_trace", trace_id],
        "origin": "trace",
    }

    DEMO_SCENARIOS.setdefault(suite_id, []).append(new_scenario)
    if suite_id in DEMO_SUITES:
        DEMO_SUITES[suite_id]["scenario_count"] = len(DEMO_SCENARIOS[suite_id])

    return {
        "success": True,
        "message": f"Successfully synthesized trace {trace_id} into regression scenario {scenario_id}",
        "suite_id": suite_id,
        "scenario": new_scenario,
    }
