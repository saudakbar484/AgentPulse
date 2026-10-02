from __future__ import annotations
import uuid
from typing import Any, TYPE_CHECKING
from sqlalchemy import text
from app.core.errors import AuthorizationError

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

TENANT_TABLES = [
    "agents",
    "suites",
    "scenarios",
    "runs",
    "conversations",
    "turns",
    "traces",
    "drift_alerts",
    "evaluations",
]


def generate_rls_sql() -> str:
    """Generates PostgreSQL DDL statements enabling mandatory Row-Level Security

    (RLS) across all tenant-isolated tables.
    """
    statements = [
        "-- AgentPulse Multi-Tenant Row-Level Security (RLS) DDL",
        "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";",
    ]

    for table in TENANT_TABLES:
        statements.extend([
            f"ALTER TABLE IF EXISTS {table} ENABLE ROW LEVEL SECURITY;",
            f"ALTER TABLE IF EXISTS {table} FORCE ROW LEVEL SECURITY;",
            f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};",
            (
                f"CREATE POLICY tenant_isolation_policy ON {table} "
                f"FOR ALL "
                f"USING (org_id = NULLIF(current_setting('app.current_org_id', true), '')::uuid) "
                f"WITH CHECK (org_id = NULLIF(current_setting('app.current_org_id', true), '')::uuid);"
            ),
        ])

    return "\n".join(statements)


async def set_tenant_context(session: AsyncSession, org_id: str | uuid.UUID) -> None:
    """Sets PostgreSQL session-local variable 'app.current_org_id'

    for transparent database-level RLS filtering.
    """
    await session.execute(
        text("SET LOCAL app.current_org_id = :org_id"),
        {"org_id": str(org_id)},
    )


def verify_tenant_boundary(current_org_id: str | uuid.UUID, resource_org_id: str | uuid.UUID) -> None:
    """Enforces zero-trust tenant boundary check at the application layer.

    Raises AuthorizationError if an attempt is made to access cross-tenant data.
    """
    if str(current_org_id) != str(resource_org_id):
        raise AuthorizationError(
            message=f"Cross-tenant access denied: current tenant '{current_org_id}' cannot access resource of tenant '{resource_org_id}'",
            code="CROSS_TENANT_VIOLATION",
        )
