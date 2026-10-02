from collections import Counter
from typing import Any
from pydantic import BaseModel
from app.modules.evaluation.registry import BUILTIN_METRICS


class FailureCluster(BaseModel):
    reason_summary: str
    count: int
    metric_key: str
    sample_quote: str


class ScorecardResult(BaseModel):
    overall_score: float
    verdict: str  # PASS or FAIL
    metrics_summary: dict[str, dict[str, Any]]
    total_conversations: int
    passed_conversations: int
    failed_conversations: int
    failure_clusters: list[FailureCluster]


def compute_run_scorecard(
    evaluations: list[dict[str, Any]],
    conversation_count: int,
    suite_threshold: float = 0.8,
) -> ScorecardResult:
    if not evaluations:
        return ScorecardResult(
            overall_score=0.0,
            verdict="FAIL",
            metrics_summary={},
            total_conversations=conversation_count,
            passed_conversations=0,
            failed_conversations=conversation_count,
            failure_clusters=[],
        )

    # Group scores by metric_key
    scores_by_metric: dict[str, list[float]] = {}
    fails_by_metric: dict[str, list[dict[str, Any]]] = {}

    for ev in evaluations:
        m_key = ev.get("metric_key", "unknown")
        score = float(ev.get("score", 0.0))
        passed = bool(ev.get("passed", False))

        scores_by_metric.setdefault(m_key, []).append(score)

        if not passed:
            fails_by_metric.setdefault(m_key, []).append(ev)

    metrics_summary: dict[str, dict[str, Any]] = {}
    blocking_failed = False
    weighted_scores: list[float] = []

    for m_key, scores in scores_by_metric.items():
        avg_score = sum(scores) / len(scores)
        weighted_scores.append(avg_score)

        meta = BUILTIN_METRICS.get(m_key)
        threshold = meta.threshold if meta else 0.7
        is_blocking = meta.is_blocking if meta else False

        metric_passed = avg_score >= threshold
        if is_blocking and not metric_passed:
            blocking_failed = True

        metrics_summary[m_key] = {
            "score": round(avg_score, 3),
            "threshold": threshold,
            "passed": metric_passed,
            "is_blocking": is_blocking,
            "sample_count": len(scores),
        }

    overall_score = sum(weighted_scores) / len(weighted_scores) if weighted_scores else 0.0

    # Overall verdict
    is_overall_pass = (overall_score >= suite_threshold) and not blocking_failed
    verdict = "PASS" if is_overall_pass else "FAIL"

    # Compute Failure Clusters
    failure_clusters: list[FailureCluster] = []
    for m_key, fail_items in fails_by_metric.items():
        reasons = [item.get("reasoning", "") for item in fail_items if item.get("reasoning")]
        counter = Counter(reasons)
        for reason, count in counter.most_common(3):
            sample_quote = ""
            for item in fail_items:
                if item.get("reasoning") == reason:
                    sample_quote = item.get("evidence", {}).get("quote", "")
                    break

            failure_clusters.append(
                FailureCluster(
                    reason_summary=reason[:120],
                    count=count,
                    metric_key=m_key,
                    sample_quote=sample_quote,
                )
            )

    failed_convs = len({ev.get("conversation_id") for ev in evaluations if not ev.get("passed")})
    passed_convs = max(0, conversation_count - failed_convs)

    return ScorecardResult(
        overall_score=round(overall_score, 3),
        verdict=verdict,
        metrics_summary=metrics_summary,
        total_conversations=conversation_count,
        passed_conversations=passed_convs,
        failed_conversations=failed_convs,
        failure_clusters=failure_clusters[:5],
    )
