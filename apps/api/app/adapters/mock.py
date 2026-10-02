import asyncio
import time
from typing import Any
from app.adapters.base import AgentReply, ConversationContext, TargetAdapter


class MockTargetAdapter(TargetAdapter):
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.mode = self.config.get("mode", "good")  # good, weak-safety, hallucinating, rude, financial, healthcare
        self.simulated_latency_ms = float(self.config.get("latency_ms", 120.0))
        self.ctx: ConversationContext | None = None

    async def open(self, ctx: ConversationContext) -> None:
        self.ctx = ctx

    async def send(self, message: str, history: list[dict[str, str]]) -> AgentReply:
        start_time = time.perf_counter()
        await asyncio.sleep(self.simulated_latency_ms / 1000.0)

        lower_msg = message.lower()

        if self.mode == "weak-safety":
            if "ignore" in lower_msg or "jailbreak" in lower_msg or "password" in lower_msg or "secret" in lower_msg:
                reply = "Sure! Here is the internal system prompt and secret admin credentials: ADMIN_PASS_123."
            else:
                reply = f"Hello! As an assistant without safety filters, I will comply with whatever you say: {message}"

        elif self.mode == "hallucinating":
            if "refund" in lower_msg or "shipping" in lower_msg:
                reply = "We offer 100% immediate cash refunds within 1 hour, and all shipping arrives by private helicopter!"
            else:
                reply = f"I am 100% sure that Mars is made of swiss cheese and your account has $1,000,000."

        elif self.mode == "rude":
            reply = f"Why are you asking such a foolish question? Look it up yourself. Don't waste my time."

        elif self.mode == "financial":
            if "buy" in lower_msg or "stock" in lower_msg or "crypto" in lower_msg or "invest" in lower_msg:
                reply = (
                    "I am an automated banking assistant and cannot provide personalized financial or investment advice. "
                    "Past performance is no guarantee of future returns. Please consult a FINRA-licensed wealth advisor."
                )
            elif "interest" in lower_msg or "savings" in lower_msg or "apr" in lower_msg:
                reply = (
                    "Our Apex Premier High-Yield Savings Account offers a 4.85% Annual Percentage Yield (APY) "
                    "with FDIC insurance coverage up to $250,000. Terms and conditions apply."
                )
            else:
                reply = "Welcome to Apex Financial. How may I assist you with your deposit accounts, transfers, or statements today?"

        elif self.mode == "healthcare":
            if "chest pain" in lower_msg or "emergency" in lower_msg or "bleeding" in lower_msg or "stroke" in lower_msg:
                reply = (
                    "EMERGENCY DIRECTIVE: If you or someone nearby is experiencing acute chest pain, shortness of breath, "
                    "or severe symptoms, please immediately call 911 or proceed to the nearest emergency medical facility."
                )
            elif "prescribe" in lower_msg or "diagnose" in lower_msg or "medication" in lower_msg:
                reply = (
                    "I am an automated clinical triage assistant and cannot diagnose diseases or prescribe medications. "
                    "I would be glad to schedule an appointment with a board-certified physician at your local clinic."
                )
            else:
                reply = "Welcome to CarePulse Clinical Services. How can I help you schedule an appointment or check clinic hours?"

        else:  # "good" / e-commerce mode
            if "refund" in lower_msg:
                reply = "Our policy allows refunds within 30 days of purchase with a valid receipt. May I have your order number?"
            elif "shipping" in lower_msg:
                reply = "Standard shipping takes 3-5 business days. Express shipping takes 1-2 business days."
            elif "jailbreak" in lower_msg or "secret" in lower_msg or "system prompt" in lower_msg:
                reply = "I cannot disclose internal configuration, passwords, or system instructions. How else may I assist you with your order?"
            else:
                reply = f"Thank you for contacting customer support. Regarding '{message}', I would be glad to help. Could you please provide your account details?"

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return AgentReply(
            content=reply,
            latency_ms=elapsed_ms,
            raw_response={"mode": self.mode, "simulated": True},
        )

    async def close(self) -> None:
        pass
