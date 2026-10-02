import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any
import httpx
from pydantic import BaseModel
from app.modules.monitoring.drift import DriftTestResult


class AlertPayload(BaseModel):
    alert_id: str
    agent_id: str
    agent_name: str
    metric_key: str
    severity: str
    summary: str
    evidence_quote: str
    sample_trace_id: str | None = None
    opened_at: str


class AlertManager:
    def __init__(self, cooldown_hours: int = 6) -> None:
        self.cooldown_delta = timedelta(hours=cooldown_hours)
        self.active_alerts: dict[str, dict[str, Any]] = {}
        self.last_alert_time: dict[str, datetime] = {}
        self.healthy_window_counts: dict[str, int] = {}

    def should_fire_alert(self, agent_id: str, metric_key: str) -> bool:
        key = f"{agent_id}:{metric_key}"
        now = datetime.now(timezone.utc)
        if key in self.last_alert_time:
            if now - self.last_alert_time[key] < self.cooldown_delta:
                return False  # Cooldown in effect
        return True

    def record_alert(
        self,
        alert_id: str,
        agent_id: str,
        agent_name: str,
        drift_result: DriftTestResult,
        evidence_quote: str = "",
        sample_trace_id: str | None = None,
    ) -> AlertPayload | None:
        key = f"{agent_id}:{drift_result.metric_key}"
        if not self.should_fire_alert(agent_id, drift_result.metric_key):
            return None

        now = datetime.now(timezone.utc)
        self.last_alert_time[key] = now
        self.healthy_window_counts[key] = 0

        alert_payload = AlertPayload(
            alert_id=alert_id,
            agent_id=agent_id,
            agent_name=agent_name,
            metric_key=drift_result.metric_key,
            severity=drift_result.severity,
            summary=drift_result.summary,
            evidence_quote=evidence_quote,
            sample_trace_id=sample_trace_id,
            opened_at=now.isoformat(),
        )
        self.active_alerts[alert_id] = alert_payload.model_dump()
        return alert_payload

    def record_healthy_window(self, agent_id: str, metric_key: str) -> str | None:
        """Increments healthy window counter.

        Auto-resolves alert after 3 consecutive healthy windows.
        """
        key = f"{agent_id}:{metric_key}"
        self.healthy_window_counts[key] = self.healthy_window_counts.get(key, 0) + 1

        if self.healthy_window_counts[key] >= 3:
            for alert_id, alert in list(self.active_alerts.items()):
                if alert["agent_id"] == agent_id and alert["metric_key"] == metric_key:
                    alert["status"] = "resolved"
                    alert["resolved_at"] = datetime.now(timezone.utc).isoformat()
                    return alert_id
        return None

    async def dispatch_slack_webhook(self, webhook_url: str, alert: AlertPayload) -> bool:
        if not webhook_url:
            return False

        color = "#EF4444" if alert.severity == "critical" else "#F59E0B"
        payload = {
            "text": f"🚨 *AgentPulse Quality Drift Alert: {alert.agent_name}*",
            "attachments": [
                {
                    "color": color,
                    "title": f"Degradation on Metric: `{alert.metric_key}` ({alert.severity.upper()})",
                    "text": alert.summary,
                    "fields": [
                        {
                            "title": "Sample Failing Quote Cited by Judge",
                            "value": f"> *\"{alert.evidence_quote}\"*",
                            "short": False,
                        },
                        {
                            "title": "Agent ID",
                            "value": alert.agent_id,
                            "short": True,
                        },
                        {
                            "title": "Opened At",
                            "value": alert.opened_at,
                            "short": True,
                        },
                    ],
                    "footer": "AgentPulse Production Drift Monitor",
                }
            ],
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(webhook_url, json=payload)
                return resp.status_code == 200
        except Exception:
            return False


# Global singleton instance
default_alert_manager = AlertManager(cooldown_hours=6)
