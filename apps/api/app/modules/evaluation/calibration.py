import json
from pathlib import Path
from typing import Any
from pydantic import BaseModel


class ConfusionMatrix(BaseModel):
    true_positive: int = 0
    false_positive: int = 0
    true_negative: int = 0
    false_negative: int = 0


class MetricCalibrationResult(BaseModel):
    metric_key: str
    judge_model: str
    sample_size: int
    accuracy: float
    precision: float
    recall: float
    cohen_kappa: float
    confusion_matrix: ConfusionMatrix


def compute_cohens_kappa(tp: int, fp: int, tn: int, fn: int) -> float:
    total = tp + fp + tn + fn
    if total == 0:
        return 0.0

    # Observed agreement
    p_o = (tp + tn) / total

    # Marginal probabilities
    # Positive = PASS, Negative = FAIL
    p_human_pos = (tp + fn) / total
    p_human_neg = (fp + tn) / total

    p_judge_pos = (tp + fp) / total
    p_judge_neg = (fn + tn) / total

    # Expected chance agreement
    p_e = (p_human_pos * p_judge_pos) + (p_human_neg * p_judge_neg)

    if p_e >= 1.0:
        return 1.0

    kappa = (p_o - p_e) / (1.0 - p_e)
    return round(max(-1.0, min(1.0, kappa)), 3)


def run_calibration_on_dataset(
    golden_dataset: list[dict[str, Any]],
    judge_predictions: list[dict[str, Any]],
    judge_model: str = "qwen2.5:32b",
) -> dict[str, MetricCalibrationResult]:
    """Computes Cohen's kappa, accuracy, precision, and recall per metric."""
    pred_map = {p["id"]: p for p in judge_predictions}
    results_by_metric: dict[str, dict[str, int]] = {}

    for item in golden_dataset:
        m_key = item["metric_key"]
        human_label = item["human_label"].lower()  # "pass" or "fail"

        pred = pred_map.get(item["id"])
        if not pred:
            continue
        judge_verdict = pred["verdict"].lower()  # "pass" or "fail"

        stats = results_by_metric.setdefault(
            m_key, {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
        )

        if human_label == "pass" and judge_verdict == "pass":
            stats["tp"] += 1
        elif human_label == "fail" and judge_verdict == "pass":
            stats["fp"] += 1
        elif human_label == "fail" and judge_verdict == "fail":
            stats["tn"] += 1
        elif human_label == "pass" and judge_verdict == "fail":
            stats["fn"] += 1

    calibrations: dict[str, MetricCalibrationResult] = {}
    for m_key, s in results_by_metric.items():
        tp, fp, tn, fn = s["tp"], s["fp"], s["tn"], s["fn"]
        total = tp + fp + tn + fn

        accuracy = (tp + tn) / total if total > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        kappa = compute_cohens_kappa(tp, fp, tn, fn)

        calibrations[m_key] = MetricCalibrationResult(
            metric_key=m_key,
            judge_model=judge_model,
            sample_size=total,
            accuracy=round(accuracy, 3),
            precision=round(precision, 3),
            recall=round(recall, 3),
            cohen_kappa=kappa,
            confusion_matrix=ConfusionMatrix(
                true_positive=tp,
                false_positive=fp,
                true_negative=tn,
                false_negative=fn,
            ),
        )

    return calibrations
