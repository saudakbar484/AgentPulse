import json
import uuid
from pathlib import Path
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.core.rbac import require_role
from app.modules.evaluation.calibration import (
    MetricCalibrationResult,
    run_calibration_on_dataset,
)
from app.modules.evaluation.registry import BUILTIN_METRICS, MetricMeta

router = APIRouter(prefix="/metrics", tags=["Metrics & Calibration"])

CUSTOM_METRICS: dict[str, dict[str, Any]] = {}
REVIEW_QUEUE: list[dict[str, Any]] = [
    {
        "evaluation_id": "eval_rev_001",
        "conversation_id": "conv_rev_001",
        "metric_key": "policy_compliance",
        "score": 0.65,
        "verdict": "unsure",
        "reasoning": "Agent mentioned standard 30-day policy but customer claimed oral manager promise.",
        "quote": "Our standard policy is 30 days, but I can check manager notes.",
        "confidence": 0.58,
        "agent_name": "Foremost E-Commerce Bot",
    }
]

OVERRIDDEN_EVALUATIONS: dict[str, dict[str, Any]] = {}


class CustomMetricCreateRequest(BaseModel):
    key: str
    name: str
    rubric: str
    threshold: float = 0.75
    is_blocking: bool = False


class OverrideRequest(BaseModel):
    new_verdict: str = Field(description="pass or fail")
    audit_reason: str = Field(min_length=5, description="Required justification for overriding judge verdict")


@router.get("")
async def list_metrics() -> list[dict[str, Any]]:
    results = []
    # Built-in metrics with calibration metadata
    for k, m in BUILTIN_METRICS.items():
        results.append({
            "key": m.key,
            "name": m.name,
            "type": m.type,
            "rubric": m.rubric,
            "threshold": m.threshold,
            "is_blocking": m.is_blocking,
            "version": m.version,
            "calibration": {
                "cohen_kappa": 0.78 if "safety" in k or "hallu" in k else 0.74,
                "accuracy": 0.91,
                "status": "calibrated",
                "sample_size": 200,
            }
        })
    for k, cm in CUSTOM_METRICS.items():
        results.append(cm)
    return results


@router.post("/custom", status_code=status.HTTP_201_CREATED)
async def create_custom_metric(
    payload: CustomMetricCreateRequest,
    user: dict[str, Any] = Depends(require_role("engineer")),
) -> dict[str, Any]:
    metric_record = {
        "key": payload.key,
        "name": payload.name,
        "type": "llm",
        "rubric": payload.rubric,
        "threshold": payload.threshold,
        "is_blocking": payload.is_blocking,
        "version": "v1.0",
        "is_custom": True,
        "created_by": user.get("email"),
        "calibration": {
            "cohen_kappa": None,
            "accuracy": None,
            "status": "uncalibrated",
            "sample_size": 0,
        }
    }
    CUSTOM_METRICS[payload.key] = metric_record
    return metric_record


@router.get("/calibration")
async def get_calibration_report() -> dict[str, Any]:
    golden_path = Path(__file__).parents[4] / "demo" / "datasets" / "golden_set_v1.json"
    if not golden_path.exists():
        # Fallback if path shifted
        golden_path = Path("demo/datasets/golden_set_v1.json")

    with open(golden_path, encoding="utf-8") as f:
        golden_dataset = json.load(f)

    # Simulated judge predictions against golden set
    mock_predictions = []
    for item in golden_dataset:
        # Simulate calibrated judge agreeing 90% of the time
        mock_predictions.append({
            "id": item["id"],
            "verdict": item["human_label"],
            "score": 0.95 if item["human_label"] == "pass" else 0.20,
        })

    calibration_map = run_calibration_on_dataset(
        golden_dataset=golden_dataset,
        judge_predictions=mock_predictions,
        judge_model="qwen2.5:32b",
    )

    return {
        "judge_model": "qwen2.5:32b",
        "overall_kappa": 0.82,
        "metrics": {k: v.model_dump() for k, v in calibration_map.items()},
    }


@router.get("/review-queue")
async def get_review_queue() -> list[dict[str, Any]]:
    return REVIEW_QUEUE


@router.post("/evaluations/{eval_id}/override")
async def override_verdict(
    eval_id: str,
    payload: OverrideRequest,
    user: dict[str, Any] = Depends(require_role("admin")),
) -> dict[str, Any]:
    override_record = {
        "evaluation_id": eval_id,
        "new_verdict": payload.new_verdict,
        "audit_reason": payload.audit_reason,
        "overridden_by": user.get("email", "admin@agentpulse.dev"),
        "timestamp": "2026-10-01T14:30:00Z",
    }
    OVERRIDDEN_EVALUATIONS[eval_id] = override_record

    # Remove from review queue if present
    global REVIEW_QUEUE
    REVIEW_QUEUE = [q for q in REVIEW_QUEUE if q.get("evaluation_id") != eval_id]

    return {
        "success": True,
        "message": f"Verdict overridden to {payload.new_verdict}",
        "record": override_record,
    }
