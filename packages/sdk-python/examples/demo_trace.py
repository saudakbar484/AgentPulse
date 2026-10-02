import asyncio
from agentpulse.client import AgentPulseClient


async def main() -> None:
    client = AgentPulseClient(api_key="ag_live_demo_test_key", base_url="http://localhost:8000")

    print("🚀 Ingesting sample production customer conversation trace...")

    async with client.trace(external_id="trace_prod_2026_001", agent_id="agent_demo_good", channel="web_chat") as trace:
        trace.record_turn("user", "Hi, when does your annual holiday discount sale begin?")
        trace.record_turn("agent", "Our annual holiday sale starts on December 1st with up to 30% off selected items!", latency_ms=115.0)
        trace.record_turn("user", "Great, thank you for the quick help!")
        trace.record_turn("agent", "You're very welcome! Let me know if you need anything else.", latency_ms=88.0)

    print("✅ Trace ingested successfully into AgentPulse.")
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
