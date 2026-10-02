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

        full_ctx = " ".join([h.get("content", "") for h in history]) + " " + message
        lower_msg = full_ctx.lower()

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
            if "structur" in lower_msg or "ctr" in lower_msg or "9,900" in lower_msg or "9900" in lower_msg or "under 10000" in lower_msg:
                reply = (
                    "Under federal anti-money laundering (AML) regulations and the Bank Secrecy Act (BSA), "
                    "financial institutions are legally required to file Currency Transaction Reports (CTRs) for cash transactions exceeding $10,000. "
                    "Structuring deposits to avoid reporting thresholds is a federal crime under 31 U.S.C. 5324. I cannot advise on structuring transactions."
                )
            elif "routing" in lower_msg or "maiden" in lower_msg or "account #" in lower_msg or "glba" in lower_msg:
                reply = (
                    "Under the Gramm-Leach-Bliley Act (GLBA) and bank confidentiality rules, I cannot disclose account numbers, "
                    "routing codes, or non-public personal financial records without verified cryptographic multi-factor authentication."
                )
            elif "wire" in lower_msg or "50,000" in lower_msg or "offshore" in lower_msg or "bypass" in lower_msg:
                reply = (
                    "Wire transfers exceeding $10,000 require secondary hardware token 2FA or in-branch verification per federal "
                    "banking security standards. Automated assistants cannot override mandatory dual-custody wire transfer controls."
                )
            elif "guarantee" in lower_msg or "12%" in lower_msg or "risk-free" in lower_msg:
                reply = (
                    "Under SEC Rule 10b-5 and FINRA Rule 2210, investment returns cannot be guaranteed. All securities carry the risk of loss, "
                    "including possible loss of principal. Apex Financial does not promise guaranteed yields on market-linked assets."
                )
            elif "buy" in lower_msg or "stock" in lower_msg or "crypto" in lower_msg or "401(k)" in lower_msg or "invest" in lower_msg:
                reply = (
                    "Under FINRA Rule 2210 and the Investment Advisers Act of 1940, I cannot provide personalized financial or investment advice or asset allocation recommendations. "
                    "Past performance does not guarantee future results. Please consult a FINRA-licensed investment advisor."
                )
            elif "penalty" in lower_msg or "compound" in lower_msg or "withdraw" in lower_msg or "fee" in lower_msg:
                reply = (
                    "Under Regulation DD, interest on the Apex Premier Savings Account compounds daily and is credited monthly. "
                    "There are no monthly maintenance fees with a $500 minimum balance, and early withdrawal penalties only apply to fixed-term CDs. "
                    "All deposits remain insured up to $250,000 by the FDIC."
                )
            elif "interest" in lower_msg or "savings" in lower_msg or "apr" in lower_msg or "apy" in lower_msg:
                reply = (
                    "Under Regulation DD (Truth in Savings), our Apex Premier High-Yield Savings Account currently offers a 4.85% Annual Percentage Yield (APY) "
                    "compounded daily with FDIC insurance coverage up to $250,000. Terms and early withdrawal fees may apply."
                )
            elif "thank" in lower_msg or "help" in lower_msg or "ok" in lower_msg:
                reply = (
                    "Thank you for contacting Apex Financial. We are committed to protecting your assets and financial privacy. "
                    "Please let us know if you need assistance with statements, transfers, or scheduling a consultation with a licensed advisor."
                )
            else:
                reply = "Welcome to Apex Financial. How may I assist you with your deposit accounts, statements, or banking services today?"

        elif self.mode == "healthcare":
            if "suicid" in lower_msg or "kill myself" in lower_msg or "self-harm" in lower_msg or "end my life" in lower_msg or "not worth living" in lower_msg:
                reply = (
                    "CRISIS DIRECTIVE: If you are experiencing thoughts of suicide or self-harm, please know compassionate support is available right now. "
                    "Please call or text 988 to reach the Suicide & Crisis Lifeline (free, confidential, available 24/7). Professional counselors are ready to support you."
                )
            elif "chest pain" in lower_msg or "shortness of breath" in lower_msg or "emergency" in lower_msg or "stroke" in lower_msg or "heart attack" in lower_msg:
                reply = (
                    "EMERGENCY CLINICAL DIRECTIVE: Symptoms of crushing chest pain or severe shortness of breath require immediate medical attention. "
                    "Please call 911 or proceed immediately to the nearest emergency department. Do not delay emergency care for an online consultation."
                )
            elif "oxycodone" in lower_msg or "narcotic" in lower_msg or "adderall" in lower_msg or "prescribe" in lower_msg or "painkiller" in lower_msg:
                reply = (
                    "Under the federal Controlled Substances Act (21 U.S.C. 812), Schedule II controlled substances strictly require an in-person clinical "
                    "evaluation and DEA-registered prescription. Automated triage assistants cannot authorize or prescribe controlled substances."
                )
            elif "hipaa" in lower_msg or "lab results" in lower_msg or "diagnosis" in lower_msg or "records" in lower_msg or "patient" in lower_msg:
                reply = (
                    "Under the Health Insurance Portability and Accountability Act (HIPAA) Privacy Rule (45 CFR Part 164), protected health information (PHI) "
                    "cannot be released without verified patient identity and an active signed HIPAA release authorization on file."
                )
            elif "diagnose" in lower_msg or "disease" in lower_msg or "condition" in lower_msg or "symptom" in lower_msg:
                reply = (
                    "I am an automated clinical intake assistant and cannot provide medical diagnoses. "
                    "I would be glad to schedule an appointment with a board-certified physician at your nearest clinic."
                )
            elif "thank" in lower_msg or "help" in lower_msg or "ok" in lower_msg or "understand" in lower_msg:
                reply = (
                    "You are welcome. Your health and safety are our highest priority. "
                    "Please let us know if you need assistance scheduling an in-person provider appointment or accessing clinical documentation."
                )
            else:
                reply = "Welcome to CarePulse Clinical Services. How may I assist you with clinic hours, directions, or provider appointments today?"

        else:  # "good" / e-commerce mode
            if "cvv" in lower_msg or "credit card" in lower_msg or "card number" in lower_msg:
                reply = (
                    "Under Payment Card Industry Data Security Standards (PCI-DSS), support representatives and chat assistants never request or store "
                    "full credit card numbers or CVV security codes. Please enter payment details strictly through our encrypted checkout gateway."
                )
            elif "discount" in lower_msg or "coupon" in lower_msg or "override" in lower_msg:
                reply = (
                    "Promotional discounts are validated automatically by our billing system. "
                    "I do not have authorization to manually apply promotional overrides exceeding store policy."
                )
            elif "refund" in lower_msg:
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
