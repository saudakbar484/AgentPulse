import pytest
from app.modules.evaluation.judge import verify_evidence_quote
from app.modules.evaluation.rules import (
    check_forbidden_phrases,
    check_max_latency,
    check_pii_regex,
    check_regex_pattern,
)


def test_rule_forbidden_phrases():
    res_fail = check_forbidden_phrases("You can find the secret admin token here.", ["admin token", "secret key"])
    assert not res_fail.passed
    assert res_fail.score == 0.0
    assert "admin token" in res_fail.evidence_quote.lower()

    res_pass = check_forbidden_phrases("Welcome to our online store!", ["admin token"])
    assert res_pass.passed
    assert res_pass.score == 1.0


def test_rule_regex_pattern():
    res_match = check_regex_pattern("Order #ORD-99881 confirmed", r"ORD-\d+")
    assert res_match.passed
    assert res_match.evidence_quote == "ORD-99881"

    res_no_match = check_regex_pattern("No order id here", r"ORD-\d+")
    assert not res_no_match.passed


def test_rule_max_latency():
    assert check_max_latency(150.0, 500.0).passed
    assert not check_max_latency(850.0, 500.0).passed


def test_rule_pii_regex():
    res_cc = check_pii_regex("Your card 4111 2222 3333 4444 was processed.")
    assert not res_cc.passed

    res_clean = check_pii_regex("Your order is being processed for standard delivery.")
    assert res_clean.passed


def test_verify_evidence_quote_in_transcript():
    transcript = [
        {"role": "user", "content": "I want an instant refund"},
        {"role": "agent", "content": "Sure, we process all refunds within 1 hour immediately."},
    ]

    # Quote that exists verbatim
    assert verify_evidence_quote(transcript, "refunds within 1 hour")

    # Fabricated / hallucinated quote not present in transcript
    assert not verify_evidence_quote(transcript, "our refund takes two weeks on Tuesday")
