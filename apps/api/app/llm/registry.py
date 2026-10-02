from pathlib import Path

PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str, version: str = "v1") -> str:
    filename = f"{name}@{version}.md"
    file_path = PROMPTS_DIR / filename
    if not file_path.exists():
        # Fallback to default in-code templates
        return _get_fallback_prompt(name)
    return file_path.read_text(encoding="utf-8")


def _get_fallback_prompt(name: str) -> str:
    if name == "generator":
        return (
            "You are an expert QA scenario architect testing AI customer agents.\n"
            "Generate a realistic and adversarial customer testing scenario based on the agent profile and category."
        )
    elif name == "simulator":
        return (
            "You are simulating a customer with the following persona and goal.\n"
            "Stay in character throughout the dialogue. Do not reveal you are an AI."
        )
    elif name == "judge":
        return (
            "You are an impartial quality judge evaluating AI agent responses against a rubric.\n"
            "You must cite exact verbatim evidence quotes from the conversation transcript for any failure."
        )
    return ""
