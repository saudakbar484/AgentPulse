import uuid
from datetime import datetime, timezone
from typing import Any
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from app.core.logging import get_logger
from app.core.rbac import require_role

router = APIRouter(prefix="/audit", tags=["Security & Audit"])
logger = get_logger("agentpulse.audit")


class AuditEvent(BaseModel):
    id: str = Field(default_factory=lambda: f"audit_{uuid.uuid4().hex[:12]}")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    org_id: str
    actor_id: str
    actor_email: str
    action: str  # USER_LOGIN, VERDICT_OVERRIDE, API_KEY_CREATED, CUSTOM_METRIC_CREATED, etc.
    resource_type: str
    resource_id: str
    client_ip: str = "127.0.0.1"
    status: str = "SUCCESS"  # SUCCESS, FAILED, BLOCKED
    metadata: dict[str, Any] = Field(default_factory=dict)


# In-memory audit event log buffer (persisted to structured log stream)
AUDIT_LOG_BUFFER: list[dict[str, Any]] = [
    {
        "id": "audit_init_001",
        "timestamp": "2026-10-01T14:00:00Z",
        "org_id": "00000000-0000-0000-0000-000000000001",
        "actor_id": "11111111-1111-1111-1111-111111111111",
        "actor_email": "admin@agentpulse.dev",
        "action": "SYSTEM_STARTUP",
        "resource_type": "platform",
        "resource_id": "agentpulse_core",
        "client_ip": "127.0.0.1",
        "status": "SUCCESS",
        "metadata": {"version": "1.0.0", "env": "production"},
    }
]


def record_audit_event(
    org_id: str,
    actor_id: str,
    actor_email: str,
    action: str,
    resource_type: str,
    resource_id: str,
    client_ip: str = "127.0.0.1",
    status: str = "SUCCESS",
    metadata: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        org_id=org_id,
        actor_id=actor_id,
        actor_email=actor_email,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        client_ip=client_ip,
        status=status,
        metadata=metadata or {},
    )
    data = event.model_dump()
    AUDIT_LOG_BUFFER.append(data)
    logger.info(
        "security_audit_event",
        action=action,
        actor=actor_email,
        resource=f"{resource_type}:{resource_id}",
        status=status,
    )
    return event


@router.get("/logs")
async def list_audit_logs(
    action: str | None = Query(default=None),
    actor_email: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    user: dict[str, Any] = Depends(require_role("admin")),
) -> list[dict[str, Any]]:
    """Query security audit trail (Requires Admin or Owner role)."""
    logs = AUDIT_LOG_BUFFER
    if action:
        logs = [entry for entry in logs if entry.get("action") == action]
    if actor_email:
        logs = [entry for entry in logs if entry.get("actor_email") == actor_email]
    return list(reversed(logs[-limit:]))
