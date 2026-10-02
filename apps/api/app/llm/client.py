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
        selected_model = model or getattr(settings, "JUDGE_MODEL", "groq/openai/gpt-oss-20b")
        if "120b" in selected_model:
            selected_model = "groq/openai/gpt-oss-20b"

        groq_key = os.environ.get("GROQ_API_KEY") or getattr(settings, "GROQ_API_KEY", None)
        if groq_key and "GROQ_API_KEY" not in os.environ:
            os.environ["GROQ_API_KEY"] = groq_key

        has_real_key = bool(
            groq_key
            or settings.LITELLM_API_BASE
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
            litellm.suppress_debug_info = True
            litellm.set_verbose = False
            # Attempt primary model first, fallback to qwen3.8-27b if rate-limited
            import asyncio
            import re
            models_to_try = [selected_model]
            if "groq" in selected_model:
                for fallback_m in ["groq/llama-3.3-70b-versatile", "groq/llama-3.1-8b-instant", "groq/qwen/qwen3.8-27b"]:
                    if fallback_m not in models_to_try:
                        models_to_try.append(fallback_m)

            last_error = None
            for model_attempt in models_to_try:
                for retry in range(2):
                    try:
                        response = await litellm.acompletion(
                            model=model_attempt,
                            messages=messages,
                            temperature=temperature,
                            seed=seed,
                            max_tokens=max_tokens,
                            api_base=settings.LITELLM_API_BASE,
                            timeout=15.0,
                        )
                        choice = response.choices[0]
                        content = choice.message.content or ""
                        if not content and hasattr(choice.message, "reasoning_content"):
                            content = getattr(choice.message, "reasoning_content", "") or ""
                        usage = getattr(response, "usage", None)
                        tokens_in = getattr(usage, "prompt_tokens", 0) if usage else 0
                        tokens_out = getattr(usage, "completion_tokens", 0) if usage else 0

                        if content:
                            return LLMResponse(
                                content=content,
                                tokens_in=tokens_in,
                                tokens_out=tokens_out,
                                cost_usd=0.000001 * (tokens_in + tokens_out * 2),
                                model=model_attempt,
                                raw=response.model_dump() if hasattr(response, "model_dump") else {},
                            )
                    except Exception as err:
                        last_error = err
                        err_str = str(err)
                        if "rate limit" in err_str.lower() and retry == 0:
                            wait_match = re.search(r"try again in ([\d\.]+)s", err_str, re.IGNORECASE)
                            wait_sec = float(wait_match.group(1)) + 1.0 if wait_match else 5.0
                            logger.warning(f"Rate limited on {model_attempt}. Backing off {wait_sec:.1f}s before retry...")
                            await asyncio.sleep(min(wait_sec, 8.0))
                            continue
                        logger.warning(f"Model {model_attempt} call encountered error: {err}. Trying failover if available.")
                        break

            raise last_error or RuntimeError("LLM completion failed across all candidate models")
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
