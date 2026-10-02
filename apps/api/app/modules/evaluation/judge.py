import asyncio
import logging
from typing import Any
from pydantic import BaseModel, Field
from app.llm.client import LLMClient, default_llm_client
from app.llm.registry import load_prompt

logger = logging.getLogger(__name__)


class EvidenceSchema(BaseModel):
    turn: int = 1
    quote: str = ""


class JudgeOutputSchema(BaseModel):
    verdict: str = Field(description="pass, fail, or unsure")
    score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    reasoning: str
    evidence: EvidenceSchema = Field(default_factory=EvidenceSchema)


class EvaluationVerdict(BaseModel):
    metric_key: str
    verdict: str  # pass, fail, unsure
    score: float
    passed: bool
    reasoning: str
    evidence: dict[str, Any]
    judge_model: str
    confidence: float
    quote_verified: bool


def verify_evidence_quote(transcript_turns: list[dict[str, str]], quote: str) -> bool:
    if not quote or not quote.strip():
        return False
    quote_clean = quote.strip().lower()
    for turn in transcript_turns:
        turn_content = turn.get("content", "").lower()
        if quote_clean in turn_content:
            return True
    return False


async def evaluate_turn_with_judge(
    metric_key: str,
    metric_name: str,
    rubric_text: str,
    transcript_turns: list[dict[str, str]],
    agent_guidelines: str = "",
    ground_truth_chunks: str = "",
    llm_client: LLMClient | None = None,
    threshold: float = 0.7,
) -> EvaluationVerdict:
    client = llm_client or default_llm_client

    # Format transcript text
    transcript_lines = []
    for turn in transcript_turns:
        role = turn.get("role", "unknown").upper()
        content = turn.get("content", "")
        transcript_lines.append(f"[{role}]: {content}")
    formatted_transcript = "\n".join(transcript_lines)

    system_prompt = load_prompt("judge", version="v1")
    user_prompt = f"""
Metric: {metric_name} ({metric_key})
Rubric:
{rubric_text}

Agent Guidelines:
{agent_guidelines}

Ground Truth Reference Documents:
{ground_truth_chunks}

Transcript:
{formatted_transcript}

Evaluate according to the rubric and return strictly JSON.
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    parsed_output, raw_resp = await client.complete_structured(
        messages=messages,
        schema=JudgeOutputSchema,
        temperature=0.1,
    )

    verdict_str = parsed_output.verdict.lower()
    score = parsed_output.score
    confidence = parsed_output.confidence
    quote = parsed_output.evidence.quote

    # 1. Anti-Hallucination Quote Verification Guard
    quote_verified = verify_evidence_quote(transcript_turns, quote)
    if verdict_str == "fail" and not quote_verified:
        logger.warning(
            f"Judge produced 'fail' verdict for metric {metric_key} with unverified quote '{quote}'. "
            "Downgrading verdict to 'unsure' per ADR-004."
        )
        verdict_str = "unsure"
        score = 0.5

    # 2. Borderline handling: if confidence < 0.6 or verdict == "unsure", trigger 3-sample vote
    if confidence < 0.6 or verdict_str == "unsure":
        logger.info(f"Borderline judgment detected for {metric_key} (conf={confidence:.2f}). Running 3-sample majority vote.")
        votes = []
        for _ in range(3):
            try:
                sub_parsed, _ = await client.complete_structured(
                    messages=messages,
                    schema=JudgeOutputSchema,
                    temperature=0.3,
                )
                sub_verdict = sub_parsed.verdict.lower()
                if sub_verdict == "fail" and not verify_evidence_quote(transcript_turns, sub_parsed.evidence.quote):
                    sub_verdict = "unsure"
                votes.append(sub_verdict)
            except Exception:
                votes.append("unsure")

        # Majority resolution
        pass_count = votes.count("pass")
        fail_count = votes.count("fail")
        if pass_count > fail_count and pass_count >= 2:
            verdict_str = "pass"
            score = max(score, threshold)
        elif fail_count > pass_count and fail_count >= 2:
            verdict_str = "fail"
            score = min(score, threshold - 0.1)

    passed = verdict_str == "pass" or (verdict_str != "fail" and score >= threshold)

    return EvaluationVerdict(
        metric_key=metric_key,
        verdict=verdict_str,
        score=score,
        passed=passed,
        reasoning=parsed_output.reasoning,
        evidence={
            "turn": parsed_output.evidence.turn,
            "quote": quote,
            "verified": quote_verified,
        },
        judge_model=raw_resp.model,
        confidence=confidence,
        quote_verified=quote_verified,
    )
