import time
from collections import defaultdict
from threading import Lock
from typing import Any
from fastapi import APIRouter, Response

router = APIRouter(tags=["Observability & Metrics"])


class PrometheusRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self._counters: dict[str, dict[tuple[tuple[str, str], ...], float]] = defaultdict(lambda: defaultdict(float))
        self._gauges: dict[str, dict[tuple[tuple[str, str], ...], float]] = defaultdict(lambda: defaultdict(float))
        self._histograms: dict[str, dict[tuple[tuple[str, str], ...], list[float]]] = defaultdict(lambda: defaultdict(list))
        self._histogram_buckets = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

    def inc_counter(self, name: str, value: float = 1.0, **labels: str) -> None:
        key = tuple(sorted(labels.items()))
        with self._lock:
            self._counters[name][key] += value

    def set_gauge(self, name: str, value: float, **labels: str) -> None:
        key = tuple(sorted(labels.items()))
        with self._lock:
            self._gauges[name][key] = value

    def observe_histogram(self, name: str, value: float, **labels: str) -> None:
        key = tuple(sorted(labels.items()))
        with self._lock:
            self._histograms[name][key].append(value)

    def render_prometheus_exposition(self) -> str:
        lines: list[str] = []

        with self._lock:
            # 1. Counters
            for name, entries in sorted(self._counters.items()):
                lines.append(f"# HELP {name} Total count of {name}")
                lines.append(f"# TYPE {name} counter")
                for labels, val in sorted(entries.items()):
                    lbl_str = ",".join(f'{k}="{v}"' for k, v in labels)
                    if lbl_str:
                        lines.append(f"{name}{{{lbl_str}}} {val}")
                    else:
                        lines.append(f"{name} {val}")

            # 2. Gauges
            for name, entries in sorted(self._gauges.items()):
                lines.append(f"# HELP {name} Current gauge value of {name}")
                lines.append(f"# TYPE {name} gauge")
                for labels, val in sorted(entries.items()):
                    lbl_str = ",".join(f'{k}="{v}"' for k, v in labels)
                    if lbl_str:
                        lines.append(f"{name}{{{lbl_str}}} {val}")
                    else:
                        lines.append(f"{name} {val}")

            # 3. Histograms
            for name, entries in sorted(self._histograms.items()):
                lines.append(f"# HELP {name} Histogram observation of {name}")
                lines.append(f"# TYPE {name} histogram")
                for labels, values in sorted(entries.items()):
                    total_count = len(values)
                    total_sum = sum(values)

                    for b in self._histogram_buckets:
                        count_le = sum(1 for v in values if v <= b)
                        b_labels = dict(labels)
                        b_labels["le"] = str(b)
                        lbl_str = ",".join(f'{k}="{v}"' for k, v in sorted(b_labels.items()))
                        lines.append(f"{name}_bucket{{{lbl_str}}} {count_le}")

                    inf_labels = dict(labels)
                    inf_labels["le"] = "+Inf"
                    lbl_str = ",".join(f'{k}="{v}"' for k, v in sorted(inf_labels.items()))
                    lines.append(f"{name}_bucket{{{lbl_str}}} {total_count}")

                    lbl_str_base = ",".join(f'{k}="{v}"' for k, v in sorted(labels))
                    if lbl_str_base:
                        lines.append(f"{name}_count{{{lbl_str_base}}} {total_count}")
                        lines.append(f"{name}_sum{{{lbl_str_base}}} {round(total_sum, 6)}")
                    else:
                        lines.append(f"{name}_count {total_count}")
                        lines.append(f"{name}_sum {round(total_sum, 6)}")

        return "\n".join(lines) + "\n"


# Global Prometheus Registry Instance
metrics_registry = PrometheusRegistry()

# Initialize core baseline metrics
metrics_registry.set_gauge("agentpulse_system_up", 1.0)
metrics_registry.set_gauge("agentpulse_circuit_breaker_open", 0.0, target="llm_gateway")
metrics_registry.set_gauge("agentpulse_circuit_breaker_open", 0.0, target="eval_judge")


@router.get("/metrics", response_class=Response)
async def get_metrics() -> Response:
    content = metrics_registry.render_prometheus_exposition()
    return Response(content=content, media_type="text/plain; version=0.0.4; charset=utf-8")
