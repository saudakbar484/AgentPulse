from typing import Any
from pydantic import BaseModel


class MetricDelta(BaseModel):
    metric_key: str
    run_a_score: float
    run_b_score: float
    delta: float  # run_b - run_a
    status: str   # improved, degraded, unchanged


class RunComparisonResult(BaseModel):
    run_a_id: str
    run_b_id: str
    overall_score_a: float
    overall_score_b: float
    overall_delta: float
    verdict_a: str
    verdict_b: str
    metric_deltas: list[MetricDelta]
    regressed_scenario_count: int
    improved_scenario_count: int


def compare_runs(run_a: dict[str, Any], run_b: dict[str, Any]) -> RunComparisonResult:
    score_a = float(run_a.get("score_overall", 0.0))
    score_b = float(run_b.get("score_overall", 0.0))
    overall_delta = score_b - score_a

    scorecard_a = run_a.get("scorecard", {}) or {}
    scorecard_b = run_b.get("scorecard", {}) or {}

    metrics_a = scorecard_a.get("metrics_summary", {})
    metrics_b = scorecard_b.get("metrics_summary", {})

    all_keys = set(metrics_a.keys()).union(set(metrics_b.keys()))
    metric_deltas: list[MetricDelta] = []

    for k in sorted(all_keys):
        sa = float(metrics_a.get(k, {}).get("score", 0.0))
        sb = float(metrics_b.get(k, {}).get("score", 0.0))
        diff = sb - sa

        status = "unchanged"
        if diff >= 0.02:
            status = "improved"
        elif diff <= -0.02:
            status = "degraded"

        metric_deltas.append(
            MetricDelta(
                metric_key=k,
                run_a_score=round(sa, 3),
                run_b_score=round(sb, 3),
                delta=round(diff, 3),
                status=status,
            )
        )

    return RunComparisonResult(
        run_a_id=run_a.get("id", "run_a"),
        run_b_id=run_b.get("id", "run_b"),
        overall_score_a=round(score_a, 3),
        overall_score_b=round(score_b, 3),
        overall_delta=round(overall_delta, 3),
        verdict_a=run_a.get("verdict", "UNKNOWN"),
        verdict_b=run_b.get("verdict", "UNKNOWN"),
        metric_deltas=metric_deltas,
        regressed_scenario_count=sum(1 for d in metric_deltas if d.status == "degraded"),
        improved_scenario_count=sum(1 for d in metric_deltas if d.status == "improved"),
    )
