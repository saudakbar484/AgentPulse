import os
import json
import litellm

if "GROQ_API_KEY" not in os.environ:
    from app.core.config import get_settings
    os.environ["GROQ_API_KEY"] = get_settings().GROQ_API_KEY or ""

print("Testing Groq API connection with openai/gpt-oss-120b...")
response = litellm.completion(
    model="groq/openai/gpt-oss-120b",
    messages=[
        {"role": "system", "content": "You are an enterprise AI evaluation judge. Output strictly JSON with keys: verdict, score, confidence, reasoning, evidence."},
        {"role": "user", "content": "Transcript: Customer asked: 'What is the leave policy?' Agent answered: 'The average leave utilization across the organization is 72%.' Evaluate for correctness & faithfulness."}
    ],
    temperature=0.1,
    max_tokens=300,
)

content = response.choices[0].message.content
print("Groq Response received:")
print(content)
