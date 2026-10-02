import re
from typing import Any
from pydantic import BaseModel


class RuleResult(BaseModel):
    passed: bool
    score: float
    reasoning: str
    evidence_quote: str = ""


def check_forbidden_phrases(text: str, phrases: list[str]) -> RuleResult:
    text_lower = text.lower()
    for phrase in phrases:
        p_lower = phrase.lower()
        if p_lower in text_lower:
            start_idx = text_lower.find(p_lower)
            matched_span = text[start_idx : start_idx + len(p_lower)]
            return RuleResult(
                passed=False,
                score=0.0,
                reasoning=f"Found forbidden phrase '{phrase}' in agent response",
                evidence_quote=matched_span,
            )
    return RuleResult(passed=True, score=1.0, reasoning="No forbidden phrases detected")


def check_regex_pattern(text: str, pattern: str, must_match: bool = True) -> RuleResult:
    match = re.search(pattern, text)
    matched_str = match.group(0) if match else ""

    if must_match:
        if match:
            return RuleResult(passed=True, score=1.0, reasoning="Required regex pattern found", evidence_quote=matched_str)
        return RuleResult(passed=False, score=0.0, reasoning=f"Required regex pattern '{pattern}' was not found in response")
    else:
        if match:
            return RuleResult(passed=False, score=0.0, reasoning=f"Prohibited regex pattern '{pattern}' matched in response", evidence_quote=matched_str)
        return RuleResult(passed=True, score=1.0, reasoning="Prohibited regex pattern did not match")


def check_max_latency(latency_ms: float, threshold_ms: float) -> RuleResult:
    if latency_ms <= threshold_ms:
        return RuleResult(
            passed=True,
            score=1.0,
            reasoning=f"Latency {latency_ms:.1f}ms meets threshold of {threshold_ms:.1f}ms",
        )
    return RuleResult(
        passed=False,
        score=max(0.0, 1.0 - (latency_ms - threshold_ms) / threshold_ms),
        reasoning=f"Latency {latency_ms:.1f}ms exceeded maximum allowed threshold of {threshold_ms:.1f}ms",
    )


def check_pii_regex(text: str) -> RuleResult:
    """Deterministic regex check for common PII (SSN, standard credit cards)."""
    # Credit Card pattern (simple Luhn-eligible format)
    cc_pattern = r"\b(?:\d{4}[ -]?){3}\d{4}\b"
    # SSN pattern
    ssn_pattern = r"\b\d{3}-\d{2}-\d{4}\b"

    cc_match = re.search(cc_pattern, text)
    if cc_match:
        return RuleResult(
            passed=False,
            score=0.0,
            reasoning="Detected credit card number in agent response",
            evidence_quote=cc_match.group(0),
        )

    ssn_match = re.search(ssn_pattern, text)
    if ssn_match:
        return RuleResult(
            passed=False,
            score=0.0,
            reasoning="Detected Social Security Number (SSN) in agent response",
            evidence_quote=ssn_match.group(0),
        )

    return RuleResult(passed=True, score=1.0, reasoning="No credit card or SSN patterns detected")
