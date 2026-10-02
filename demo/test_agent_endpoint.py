import urllib.request
import json

payload = {
    "adapter_type": "http_json",
    "adapter_config": {
        "url": "http://127.0.0.1:8085/chat/query",
        "method": "POST",
        "request_template": '{"question": "{{message}}", "context_type": "policy"}',
        "response_path": "answer",
    },
    "test_message": "What is the standard annual paid leave policy?",
}

req = urllib.request.Request(
    "http://localhost:8000/v1/agents/test-connection",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"},
)

with urllib.request.urlopen(req) as resp:
    result = json.loads(resp.read().decode("utf-8"))
    print("Agent Connection Test Result:")
    print(json.dumps(result, indent=2))
