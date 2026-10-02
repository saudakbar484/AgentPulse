from typing import Any
from fastapi import APIRouter

router = APIRouter(prefix="/docs-content", tags=["Documentation & Guides"])

DOCS_CATALOG: dict[str, dict[str, Any]] = {
    "quickstart": {
        "title": "AgentPulse Quickstart Guide",
        "description": "5-minute guide to setting up CI red-teaming and continuous behavioral drift monitoring for your AI agent.",
        "content": """# AgentPulse Quickstart

AgentPulse acts as an automated behavioral QA engineer and production drift monitor for AI agents.

### 1. Connect Target Agent
Register your agent endpoint via HTTP/JSON or OpenAI-compatible format:
```bash
curl -X POST http://localhost:8000/v1/agents \\
  -H "Content-Type: application/json" \\
  -d '{
    "name": "Production Customer Support Bot",
    "adapter_type": "http_json",
    "adapter_config": {
      "endpoint_url": "https://api.yourcompany.com/chat",
      "method": "POST",
      "auth_header": "Bearer your-secret-token"
    }
  }'
```

### 2. Run Automated CI Suite
```bash
agentpulse run --agent-id agent_demo_good --suite-id suite_regression_v1 --fail-under 0.85
```
Exit code will return `0` if all blocking metrics pass, or `1` if regressions are detected.
""",
    },
    "adapters": {
        "title": "Target Agent Adapter Guide",
        "description": "Connect any LLM agent regardless of hosting platform or runtime language.",
        "content": """# Adapter Specifications

AgentPulse supports three primary adapter types:
1. **HTTP/JSON**: Standard POST payload with customizable request/response body schemas.
2. **OpenAI-Compatible**: Integrates with `/v1/chat/completions` endpoints (vLLM, Ollama, OpenAI, Azure).
3. **Mock**: In-memory synthetic bot with switchable safety profiles (`good`, `weak-safety`, `financial`, `healthcare`).

All outbound calls are validated by a socket-level **Zero-Trust SSRF IP Firewall** that rejects RFC 1918 private IPs and cloud metadata endpoints.
""",
    },
    "metrics": {
        "title": "Evaluator Metric Reference & Rubrics",
        "description": "Mathematical definitions of calibrated LLM judges, statistical drift z-tests, and blocking criteria.",
        "content": r"""# Metric Taxonomy

### 1. Built-in Core Metrics
- **Safety & Jailbreak Defense (Blocking)**: Verifies refusal of adversarial prompts, prompt-injection attempts, and internal token leaks.
- **Hallucination Resistance (Blocking)**: Validates statements against uploaded Knowledge Base documents. Any ungrounded factual claim triggers a penalty.
- **Correctness & Policy Compliance (Blocking)**: Asserts that required constraints (e.g. 30-day receipt rules) are respected.
- **Tone & Brand Alignment (Non-blocking)**: Measures warmth, empathy, and professional demeanor.

### 2. Statistical Calibration (Cohen's κ)
We measure inter-annotator agreement against human expert gold standards using Cohen's kappa:
$$\kappa = \frac{p_o - p_e}{1 - p_e}$$
Production judges must satisfy $\kappa \ge 0.70$.

### 3. Production Drift Detection (Two-Proportion z-Test)
Drift is signaled when live sampled failure rates exceed the baseline window with statistical significance:
$$z = \frac{\hat{p}_1 - \hat{p}_2}{\sqrt{\hat{p}(1-\hat{p})(1/n_1 + 1/n_2)}}$$
Gate: $p < 0.01$, $\Delta \ge 5\%$, $n \ge 30$.
""",
    },
    "ci": {
        "title": "CI/CD & GitHub Actions Automation",
        "description": "Block regressed prompts and model updates before deploying to production.",
        "content": """# GitHub Actions Pipeline

Place `.github/workflows/agentpulse-ci.yml` in your repository:
```yaml
name: Agent Behavioral CI Gate
on: [pull_request, push]

jobs:
  agent-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install AgentPulse CLI
        run: pip install ./apps/cli
      - name: Execute Red-Team Regression Suite
        run: |
          agentpulse run \\
            --agent-id agent_demo_good \\
            --suite-id suite_demo_core \\
            --fail-under 0.85 \\
            --output junit.xml
      - name: Publish Test Results
        uses: EnricoMi/publish-unit-test-result-action@v2
        if: always()
        with:
          files: junit.xml
```
""",
    },
    "security": {
        "title": "Security, Compliance & Multi-Tenant RLS",
        "description": "Enterprise security controls, PostgreSQL row-level security, and audit logging.",
        "content": """# Security & Hardening Architecture

1. **PostgreSQL Row-Level Security (RLS)**: Enforced via `SET LOCAL app.current_org_id` on every query, preventing cross-tenant access at the database engine level.
2. **OWASP L1 Defense Headers**: Injected automatically on all API responses (`X-Frame-Options: DENY`, `nosniff`, `CSP`, `HSTS`).
3. **Sliding-Window Rate Limiter**: 120 req/min default per client IP; 20 req/min for authentication routes.
4. **Adversarial Transcript Sandboxing**: Untrusted turns are wrapped with random cryptographic nonces `<untrusted_dialog_transcript nonce="...">` to prevent transcript prompt injection from hijacking LLM judges.
""",
    },
}


@router.get("")
async def list_documentation_topics() -> list[dict[str, Any]]:
    return [
        {"key": k, "title": v["title"], "description": v["description"]}
        for k, v in DOCS_CATALOG.items()
    ]


@router.get("/{topic}")
async def get_documentation_topic(topic: str) -> dict[str, Any]:
    doc = DOCS_CATALOG.get(topic)
    if not doc:
        return {"error": "Topic not found", "available_topics": list(DOCS_CATALOG.keys())}
    return doc
