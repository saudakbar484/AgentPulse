import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import logging
for log_name in ["LiteLLM", "litellm", "LiteLLM Proxy", "LiteLLM Router"]:
    logging.getLogger(log_name).setLevel(logging.CRITICAL)

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.audit import router as audit_router
from app.core.config import get_settings
from app.core.errors import setup_error_handlers
from app.core.logging import get_logger, setup_logging
from app.core.metrics import router as metrics_router
from app.core.middleware import SecurityAndObservabilityMiddleware
from app.core.resilience import (
    llm_gateway_breaker,
    slack_webhook_breaker,
    target_agent_breaker,
)
from app.db.rls import generate_rls_sql
from app.modules.agents.router import router as agents_router
from app.modules.auth.router import router as auth_router
from app.modules.docs.router import router as docs_router
from app.modules.evaluation.router import router as evaluation_router
from app.modules.monitoring.router import router as monitoring_router
from app.modules.reports.router import router as reports_router
from app.modules.runs.router import router as runs_router
from app.modules.suites.router import router as suites_router

settings = get_settings()
setup_logging(debug=settings.DEBUG)
logger = get_logger("agentpulse.api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("agentpulse_api_starting", env=settings.APP_ENV, version="1.0.0")
    yield
    logger.info("agentpulse_api_stopping")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Enterprise CI & Continuous Behavioral Observability Platform for AI Agents",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
)

setup_error_handlers(app)

# 1. Observability & Security Middleware (OWASP headers, rate limiting, request timer)
app.add_middleware(SecurityAndObservabilityMiddleware)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", tags=["Health"])
async def healthz() -> dict[str, str]:
    return {"status": "healthy", "app": settings.APP_NAME}


@app.get("/readyz", tags=["Health"])
async def readyz() -> dict[str, str]:
    return {"status": "ready", "app": settings.APP_NAME}


@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "description": "Continuous Behavioral Observability for AI Agents",
        "docs": "/docs",
        "metrics": "/metrics",
    }


# Mount Prometheus Metrics Route at /metrics
app.include_router(metrics_router)

# Mount API V1 Routes
app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
app.include_router(agents_router, prefix=settings.API_V1_PREFIX)
app.include_router(suites_router, prefix=settings.API_V1_PREFIX)
app.include_router(runs_router, prefix=settings.API_V1_PREFIX)
app.include_router(monitoring_router, prefix=settings.API_V1_PREFIX)
app.include_router(evaluation_router, prefix=settings.API_V1_PREFIX)
app.include_router(reports_router, prefix=settings.API_V1_PREFIX)
app.include_router(audit_router, prefix=settings.API_V1_PREFIX)
app.include_router(docs_router, prefix=settings.API_V1_PREFIX)


# System Resilience & Security Status Endpoints
@app.get(f"{settings.API_V1_PREFIX}/system/resilience", tags=["System & Resilience"])
async def get_resilience_status() -> dict[str, Any]:
    return {
        "status": "operational",
        "security_hardening": {
            "rls_enforcement": "ACTIVE",
            "rate_limiting": "ACTIVE (120 req/min)",
            "owasp_headers": "ACTIVE",
            "adversarial_prompt_guard": "ACTIVE",
        },
        "circuit_breakers": [
            llm_gateway_breaker.get_status(),
            target_agent_breaker.get_status(),
            slack_webhook_breaker.get_status(),
        ],
    }


@app.get(f"{settings.API_V1_PREFIX}/system/rls-ddl", tags=["System & Resilience"])
async def get_rls_ddl() -> dict[str, str]:
    return {"ddl": generate_rls_sql()}
