import math
from dataclasses import dataclass
from typing import Any
from pydantic import BaseModel


@dataclass
class DriftTestResult:
    has_drift: bool
    metric_key: str
    test_type: str  # "z_test", "welch_t_test", "ewma"
    p_value: float
    baseline_val: float
    current_val: float
    absolute_delta: float
    sample_size: int
    severity: str  # "info", "warning", "critical"
    summary: str


class StatisticalDriftDetector:
    def __init__(self, min_sample_size: int = 30, alpha: float = 0.01, min_delta: float = 0.05) -> None:
        self.min_sample_size = min_sample_size
        self.alpha = alpha  # Significance threshold (p < 0.01)
        self.min_delta = min_delta  # Minimum 5 percentage points shift to avoid alert fatigue

    def test_fail_rate_shift(
        self,
        metric_key: str,
        baseline_fails: int,
        baseline_total: int,
        current_fails: int,
        current_total: int,
    ) -> DriftTestResult | None:
        """One-sided two-proportion z-test testing if failure rate increased significantly."""
        if current_total < self.min_sample_size or baseline_total < self.min_sample_size:
            return None

        p1 = baseline_fails / baseline_total
        p2 = current_fails / current_total
        delta = p2 - p1

        # Pooled sample proportion
        p_pool = (baseline_fails + current_fails) / (baseline_total + current_total)

        if p_pool == 0.0 or p_pool == 1.0 or delta <= 0:
            return DriftTestResult(
                has_drift=False,
                metric_key=metric_key,
                test_type="z_test",
                p_value=1.0,
                baseline_val=p1,
                current_val=p2,
                absolute_delta=delta,
                sample_size=current_total,
                severity="info",
                summary=f"Failure rate stable or improved ({p1:.1%} -> {p2:.1%})",
            )

        se = math.sqrt(p_pool * (1 - p_pool) * (1 / baseline_total + 1 / current_total))
        if se == 0:
            z_score = 0.0
        else:
            z_score = delta / se

        # One-sided normal survival function approximation
        p_value = 0.5 * math.erfc(z_score / math.sqrt(2))

        has_drift = (p_value < self.alpha) and (delta >= self.min_delta)

        severity = "info"
        if has_drift:
            severity = "critical" if delta >= 0.15 or p_value < 0.001 else "warning"

        summary = (
            f"Fail rate rose from {p1:.1%} to {p2:.1%} (Δ={delta:+.1%}, "
            f"p={p_value:.4f}, z={z_score:.2f}, n={current_total})"
        )

        return DriftTestResult(
            has_drift=has_drift,
            metric_key=metric_key,
            test_type="z_test",
            p_value=round(p_value, 5),
            baseline_val=round(p1, 4),
            current_val=round(p2, 4),
            absolute_delta=round(delta, 4),
            sample_size=current_total,
            severity=severity,
            summary=summary,
        )

    def test_score_mean_shift(
        self,
        metric_key: str,
        baseline_scores: list[float],
        current_scores: list[float],
    ) -> DriftTestResult | None:
        """Welch's unequal variances t-test testing if mean score degraded."""
        n1 = len(baseline_scores)
        n2 = len(current_scores)
        if n1 < self.min_sample_size or n2 < self.min_sample_size:
            return None

        m1 = sum(baseline_scores) / n1
        m2 = sum(current_scores) / n2
        delta = m1 - m2  # Degradation is positive

        var1 = sum((x - m1) ** 2 for x in baseline_scores) / (n1 - 1) if n1 > 1 else 0.0
        var2 = sum((x - m2) ** 2 for x in current_scores) / (n2 - 1) if n2 > 1 else 0.0

        denom = math.sqrt(var1 / n1 + var2 / n2) if (var1 / n1 + var2 / n2) > 0 else 1e-9
        t_stat = delta / denom

        if delta <= 0:
            return DriftTestResult(
                has_drift=False,
                metric_key=metric_key,
                test_type="welch_t_test",
                p_value=1.0,
                baseline_val=m1,
                current_val=m2,
                absolute_delta=-delta,
                sample_size=n2,
                severity="info",
                summary=f"Mean score healthy ({m1:.2f} -> {m2:.2f})",
            )

        p_value = 0.5 * math.erfc(t_stat / math.sqrt(2))
        has_drift = (p_value < self.alpha) and (delta >= self.min_delta)

        severity = "critical" if delta >= 0.20 else "warning" if has_drift else "info"

        return DriftTestResult(
            has_drift=has_drift,
            metric_key=metric_key,
            test_type="welch_t_test",
            p_value=round(p_value, 5),
            baseline_val=round(m1, 3),
            current_val=round(m2, 3),
            absolute_delta=round(delta, 3),
            sample_size=n2,
            severity=severity,
            summary=f"Mean score degraded from {m1:.2f} to {m2:.2f} (Δ=-{delta:.2f}, p={p_value:.4f})",
        )
