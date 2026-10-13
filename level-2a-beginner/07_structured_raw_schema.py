"""2.2 Structured outputs, the raw way: pass the JSON Schema yourself via output_config."""
import json
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Extract the key info: John Smith (john@example.com) asked for a demo."}],
    output_config={
        "format": {
            "type": "json_schema",
            "schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "email": {"type": "string"},
                    "demo_requested": {"type": "boolean"},
                },
                "required": ["name", "email", "demo_requested"],
                "additionalProperties": False,      # required on every object
            },
        }
    },
)
data = json.loads(response.content[0].text)   # guaranteed to match the schema
print(data)
