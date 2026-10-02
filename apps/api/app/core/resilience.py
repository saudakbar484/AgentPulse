import time
from enum import Enum
from threading import Lock
from typing import Any
from app.core.errors import DomainError
from app.core.metrics import metrics_registry


class CircuitState(str, Enum):
    CLOSED = "CLOSED"        # Normal operations: calls allowed
    OPEN = "OPEN"            # Outage detected: fast-fail immediately
    HALF_OPEN = "HALF_OPEN"  # Testing recovery with single probe


class CircuitBreakerOpenError(DomainError):
    def __init__(self, breaker_name: str, retry_after: float) -> None:
        super().__init__(
            message=f"Circuit breaker '{breaker_name}' is OPEN. Target downstream is degraded. Retry after {round(retry_after, 1)}s.",
            code="CIRCUIT_BREAKER_OPEN",
            status_code=503,
            detail={"breaker_name": breaker_name, "retry_after_seconds": retry_after},
        )


class CircuitBreaker:
    """Thread-safe circuit breaker preventing cascade downstream outages."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._lock = Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            self._evaluate_state_transition()
            return self._state

    def _evaluate_state_transition(self) -> None:
        now = time.time()
        if self._state == CircuitState.OPEN:
            if now - self._last_failure_time >= self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                metrics_registry.set_gauge("agentpulse_circuit_breaker_open", 0.5, target=self.name)

    def can_execute(self) -> bool:
        with self._lock:
            self._evaluate_state_transition()
            return self._state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    def record_success(self) -> None:
        with self._lock:
            self._failure_count = 0
            self._state = CircuitState.CLOSED
            metrics_registry.set_gauge("agentpulse_circuit_breaker_open", 0.0, target=self.name)

    def record_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN or self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                metrics_registry.set_gauge("agentpulse_circuit_breaker_open", 1.0, target=self.name)

    def get_status(self) -> dict[str, Any]:
        with self._lock:
            self._evaluate_state_transition()
            remaining_cooldown = max(0.0, self.recovery_timeout - (time.time() - self._last_failure_time))
            return {
                "name": self.name,
                "state": self._state.value,
                "consecutive_failures": self._failure_count,
                "cooldown_remaining_seconds": round(remaining_cooldown, 2) if self._state == CircuitState.OPEN else 0.0,
            }


# Core downstream system circuit breakers
llm_gateway_breaker = CircuitBreaker(name="llm_gateway", failure_threshold=5, recovery_timeout=20.0)
target_agent_breaker = CircuitBreaker(name="target_agent_adapter", failure_threshold=4, recovery_timeout=15.0)
slack_webhook_breaker = CircuitBreaker(name="slack_webhook", failure_threshold=3, recovery_timeout=30.0)
