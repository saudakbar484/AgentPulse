import asyncio
import uuid
from typing import Any
from pydantic import BaseModel
from app.adapters.base import TargetAdapter
from app.adapters.http_json import HttpJsonAdapter
from app.adapters.mock import MockTargetAdapter
from app.adapters.openai_compat import OpenAICompatAdapter
from app.llm.client import LLMClient
from app.modules.evaluation.judge import evaluate_turn_with_judge
from app.modules.evaluation.registry import BUILTIN_METRICS
from app.modules.evaluation.scoring import ScorecardResult, compute_run_scorecard
from app.modules.runs.simulator import run_simulated_conversation


class RunProgress(BaseModel):
    run_id: str
    status: str
    total_conversations: int
    completed_conversations: int
    failed_conversations: int
    current_cost_usd: float
    avg_latency_ms: float
    verdict: str | None = None
    score_overall: float | None = None


# In-memory progress tracking for real-time SSE updates
active_run_progress: dict[str, RunProgress] = {}


def get_adapter_for_agent(adapter_type: str, config: dict[str, Any]) -> TargetAdapter:
    if adapter_type == "openai_compat":
        return OpenAICompatAdapter(config)
    elif adapter_type == "mock":
        return MockTargetAdapter(config)
    return HttpJsonAdapter(config)


async def execute_run_pipeline(
    run_id: str,
    scenarios: list[dict[str, Any]],
    adapter_type: str,
    adapter_config: dict[str, Any],
    ground_truth_docs: str = "",
    agent_guidelines: str = "",
    concurrency_limit: int = 5,
    llm_client: LLMClient | None = None,
) -> tuple[ScorecardResult, list[dict[str, Any]]]:
    """Executes the complete test suite simulation and evaluation loop."""
    progress = RunProgress(
        run_id=run_id,
        status="running",
        total_conversations=len(scenarios),
        completed_conversations=0,
        failed_conversations=0,
        current_cost_usd=0.0,
        avg_latency_ms=0.0,
    )
    active_run_progress[run_id] = progress

    semaphore = asyncio.Semaphore(concurrency_limit)
    completed_conversations_data: list[dict[str, Any]] = []
    all_evaluations: list[dict[str, Any]] = []

    async def process_scenario(sc: dict[str, Any]) -> None:
        async with semaphore:
            conv_id = str(uuid.uuid4())
            adapter = get_adapter_for_agent(adapter_type, adapter_config)

            # 1. Run multi-turn simulated conversation
            turns, term_reason, avg_latency = await run_simulated_conversation(
                conversation_id=conv_id,
                persona_name=sc.get("persona_name", "Curious Customer"),
                emotion=sc.get("emotion", "neutral"),
                goal=sc.get("goal", "Inquire about products"),
                opening_message=sc.get("opening_message", "Hello"),
                max_turns=sc.get("max_turns", 6),
                target_adapter=adapter,
                llm_client=llm_client,
            )

            # 2. Evaluate against core metrics
            conv_evals: list[dict[str, Any]] = []
            target_metrics = ["correctness_faithfulness", "hallucination", "safety_jailbreak", "tone_brand"]

            for m_key in target_metrics:
                meta = BUILTIN_METRICS.get(m_key)
                if not meta:
                    continue

                verdict_res = await evaluate_turn_with_judge(
                    metric_key=m_key,
                    metric_name=meta.name,
                    rubric_text=meta.rubric,
                    transcript_turns=turns,
                    agent_guidelines=agent_guidelines,
                    ground_truth_chunks=ground_truth_docs,
                    threshold=meta.threshold,
                    llm_client=llm_client,
                )

                eval_dict = {
                    "conversation_id": conv_id,
                    "metric_key": m_key,
                    "score": verdict_res.score,
                    "passed": verdict_res.passed,
                    "verdict": verdict_res.verdict,
                    "reasoning": verdict_res.reasoning,
                    "evidence": verdict_res.evidence,
                    "judge_model": verdict_res.judge_model,
                }
                conv_evals.append(eval_dict)
                all_evaluations.append(eval_dict)

            conv_passed = all(ev["passed"] for ev in conv_evals)

            conv_data = {
                "id": conv_id,
                "scenario_id": sc.get("id"),
                "category": sc.get("category", "general"),
                "turns": turns,
                "evaluations": conv_evals,
                "termination_reason": term_reason,
                "avg_latency_ms": avg_latency,
                "passed": conv_passed,
            }
            completed_conversations_data.append(conv_data)

            # Update live progress
            progress.completed_conversations += 1
            if not conv_passed:
                progress.failed_conversations += 1
            progress.current_cost_usd += 0.003
            progress.avg_latency_ms = avg_latency

    # Execute all scenarios concurrently with concurrency bounds
    tasks = [process_scenario(sc) for sc in scenarios]
    await asyncio.gather(*tasks)

    # Compute final scorecard
    scorecard = compute_run_scorecard(
        evaluations=all_evaluations,
        conversation_count=len(scenarios),
        suite_threshold=0.8,
    )

    progress.status = "completed"
    progress.verdict = scorecard.verdict
    progress.score_overall = scorecard.overall_score

    return scorecard, completed_conversations_data
