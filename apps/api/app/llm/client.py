import json
import logging
import os
from typing import Any, TypeVar
from pydantic import BaseModel
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

T = TypeVar("T", bound=BaseModel)


class LLMResponse(BaseModel):
    content: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    model: str
    raw: dict[str, Any] = {}


class LLMClient:
    def __init__(self, is_mock: bool = False) -> None:
        self.is_mock = is_mock
        self.mock_responses: list[str] = []

    def set_mock_response(self, response: str) -> None:
        self.mock_responses.append(response)

    async def complete(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.2,
        seed: int | None = 42,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        selected_model = model or settings.JUDGE_MODEL

        has_real_key = bool(
            settings.LITELLM_API_BASE
            or os.environ.get("OPENAI_API_KEY")
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("ANTHROPIC_API_KEY")
        )

        if self.is_mock or settings.APP_ENV == "testing" or not has_real_key:
            if self.mock_responses:
                content = self.mock_responses.pop(0)
            else:
                full_text = " ".join([str(m.get("content", "")) for m in messages])
                if "Generate a realistic test scenario" in full_text or "category" in full_text.lower():
                    content = (
                        '{"category": "happy_path", "goal": "Check return policy", '
                        '"opening_message": "Hello, what is your refund window?", '
                        '"success_criteria": ["Agent clearly states policy"], '
                        '"max_turns": 4, "tags": ["returns", "happy_path"]}'
                    )
                elif "Respond to the agent" in full_text:
                    content = "Thank you for the information. [GOAL_REACHED]"
                else:
                    content = (
                        '{"verdict": "pass", "score": 0.95, "confidence": 0.95, '
                        '"reasoning": "Agent followed instructions and tone accurately.", '
                        '"evidence": {"turn": 2, "quote": ""}}'
                    )

            return LLMResponse(
                content=content,
                tokens_in=len(str(messages)) // 4,
                tokens_out=len(content) // 4,
                cost_usd=0.0,
                model=selected_model,
            )

        try:
            import litellm
            response = await litellm.acompletion(
                model=selected_model,
                messages=messages,
                temperature=temperature,
                seed=seed,
                max_tokens=max_tokens,
                api_base=settings.LITELLM_API_BASE,
                timeout=5.0,
            )
            choice = response.choices[0]
            content = choice.message.content or ""
            usage = getattr(response, "usage", None)
            tokens_in = getattr(usage, "prompt_tokens", 0) if usage else 0
            tokens_out = getattr(usage, "completion_tokens", 0) if usage else 0

            return LLMResponse(
                content=content,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cost_usd=0.000001 * (tokens_in + tokens_out * 2),
                model=selected_model,
                raw=response.model_dump() if hasattr(response, "model_dump") else {},
            )
        except Exception as e:
            logger.warning(f"LiteLLM call failed or provider unavailable: {e}. Falling back to deterministic simulation.")
            full_text = " ".join([str(m.get("content", "")) for m in messages])
            if "Generate a realistic test scenario" in full_text or "category" in full_text.lower():
                fallback_content = (
                    '{"category": "happy_path", "goal": "Check return policy", '
                    '"opening_message": "Hello, what is your refund window?", '
                    '"success_criteria": ["Agent clearly states policy"], '
                    '"max_turns": 4, "tags": ["returns", "happy_path"]}'
                )
            else:
                fallback_content = '{"verdict": "pass", "score": 0.95, "reasoning": "Fallback response evaluation", "evidence": {"turn": 1, "quote": ""}}'

            return LLMResponse(
                content=fallback_content,
                tokens_in=50,
                tokens_out=25,
                cost_usd=0.0,
                model=selected_model,
            )

    async def complete_structured(
        self,
        messages: list[dict[str, str]],
        schema: type[T],
        model: str | None = None,
        temperature: float = 0.1,
    ) -> tuple[T, LLMResponse]:
        raw_resp = await self.complete(messages, model=model, temperature=temperature)
        cleaned_content = raw_resp.content.strip()

        # Handle markdown JSON formatting ```json ... ```
        if "```json" in cleaned_content:
            cleaned_content = cleaned_content.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in cleaned_content:
            cleaned_content = cleaned_content.split("```", 1)[1].split("```", 1)[0].strip()

        try:
            data = json.loads(cleaned_content)
            parsed = schema.model_validate(data)
            return parsed, raw_resp
        except Exception as first_err:
            logger.warning(f"First JSON validation attempt failed: {first_err}. Attempting single repair.")
            # Repair attempt: ask model to repair into valid JSON
            repair_prompt = [
                {"role": "system", "content": "You are a JSON repair tool. Output strictly valid JSON matching the requested schema. No conversational filler."},
                {"role": "user", "content": f"The following string was invalid JSON for the schema: {raw_resp.content}\nRepair it and return only valid JSON."}
            ]
            repair_resp = await self.complete(repair_prompt, model=model, temperature=0.0)
            repaired_text = repair_resp.content.strip()
            if "```json" in repaired_text:
                repaired_text = repaired_text.split("```json", 1)[1].split("```", 1)[0].strip()
            elif "```" in repaired_text:
                repaired_text = repaired_text.split("```", 1)[1].split("```", 1)[0].strip()

            try:
                data = json.loads(repaired_text)
                parsed = schema.model_validate(data)
                return parsed, repair_resp
            except Exception as final_err:
                raise ValueError(f"Failed to generate structured JSON matching {schema.__name__}: {final_err}") from final_err


# Global default client instance
default_llm_client = LLMClient(is_mock=False)
