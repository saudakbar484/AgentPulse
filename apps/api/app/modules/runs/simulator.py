import logging
from typing import Any
from app.adapters.base import ConversationContext, TargetAdapter
from app.llm.client import LLMClient, default_llm_client
from app.llm.registry import load_prompt

logger = logging.getLogger(__name__)


class SimulatedTurn(BaseModel := type("BaseModel", (), {})):
    idx: int
    role: str
    content: str
    latency_ms: float = 0.0
    raw: dict[str, Any] = {}


async def run_simulated_conversation(
    conversation_id: str,
    persona_name: str,
    emotion: str,
    goal: str,
    opening_message: str,
    max_turns: int,
    target_adapter: TargetAdapter,
    llm_client: LLMClient | None = None,
) -> tuple[list[dict[str, Any]], str, float]:
    """Runs a multi-turn conversation between user persona and target agent.

    Returns (turns, termination_reason, avg_latency_ms).
    """
    client = llm_client or default_llm_client
    turns: list[dict[str, Any]] = []
    latencies: list[float] = []
    termination_reason = "max_turns"

    ctx = ConversationContext(
        conversation_id=conversation_id,
        session_id=f"sess_{conversation_id[:8]}",
        agent_id="target_agent",
    )
    await target_adapter.open(ctx)

    try:
        # Turn 1: Opening customer message
        current_user_msg = opening_message
        turn_idx = 1

        history_for_adapter: list[dict[str, str]] = []

        prompt_template = load_prompt("simulator", version="v1")
        sim_system_prompt = prompt_template
        sim_system_prompt = sim_system_prompt.replace("{persona_name}", persona_name)
        sim_system_prompt = sim_system_prompt.replace("{emotion}", emotion)
        sim_system_prompt = sim_system_prompt.replace("{language}", "en")
        sim_system_prompt = sim_system_prompt.replace("{traits}", "Authentic customer profile")
        sim_system_prompt = sim_system_prompt.replace("{goal}", goal)

        while turn_idx <= max_turns:
            # 1. Record User Turn
            clean_user_msg = current_user_msg.replace("[GOAL_REACHED]", "").replace("[GIVE_UP]", "").strip()
            turns.append({
                "idx": turn_idx,
                "role": "user",
                "content": clean_user_msg,
                "latency_ms": 0.0,
            })
            history_for_adapter.append({"role": "user", "content": clean_user_msg})
            turn_idx += 1

            # 2. Call Target Agent
            try:
                agent_reply = await target_adapter.send(clean_user_msg, history_for_adapter[:-1])
                latencies.append(agent_reply.latency_ms)
                agent_content = agent_reply.content
            except Exception as e:
                logger.error(f"Target agent call failed: {e}")
                turns.append({
                    "idx": turn_idx,
                    "role": "agent",
                    "content": f"[Agent Error: Request failed: {e}]",
                    "latency_ms": 0.0,
                })
                termination_reason = "error"
                break

            # 3. Record Agent Turn
            turns.append({
                "idx": turn_idx,
                "role": "agent",
                "content": agent_content,
                "latency_ms": agent_reply.latency_ms,
                "raw_response": agent_reply.raw_response,
            })
            history_for_adapter.append({"role": "assistant", "content": agent_content})
            turn_idx += 1

            if turn_idx > max_turns:
                termination_reason = "max_turns"
                break

            # 4. Generate next User message via Simulator LLM
            sim_messages = [
                {"role": "system", "content": sim_system_prompt},
            ]
            for t in turns:
                sim_messages.append({
                    "role": "user" if t["role"] == "user" else "assistant",
                    "content": t["content"],
                })
            sim_messages.append({
                "role": "user",
                "content": "Respond to the agent's latest message in character. State [GOAL_REACHED] if resolved or [GIVE_UP] if giving up.",
            })

            sim_resp = await client.complete(sim_messages, temperature=0.5)
            next_user_text = sim_resp.content.strip()

            if "[GOAL_REACHED]" in next_user_text:
                termination_reason = "goal_reached"
                current_user_msg = next_user_text
                # Record final user satisfaction utterance
                turns.append({
                    "idx": turn_idx,
                    "role": "user",
                    "content": next_user_text.replace("[GOAL_REACHED]", "").strip() or "Thank you, that resolves my issue.",
                    "latency_ms": 0.0,
                })
                break
            elif "[GIVE_UP]" in next_user_text:
                termination_reason = "give_up"
                turns.append({
                    "idx": turn_idx,
                    "role": "user",
                    "content": next_user_text.replace("[GIVE_UP]", "").strip() or "This isn't helping. I will speak to someone else.",
                    "latency_ms": 0.0,
                })
                break

            current_user_msg = next_user_text

    finally:
        await target_adapter.close()

    avg_latency = (sum(latencies) / len(latencies)) if latencies else 0.0
    return turns, termination_reason, avg_latency
