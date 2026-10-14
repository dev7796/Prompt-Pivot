"""Level 3a, section 3.5: the rules for tool_result. Break rule two on purpose.

Rule 1: every tool_use block gets exactly one tool_result, matched by tool_use_id.
Rule 2: the tool_result blocks come FIRST in the next user message. Text can follow; it cannot lead.
Rule 3: all results for one assistant turn go back in ONE user message.

This script sends the result the wrong way round to show the 400, then the right way.
"""
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-opus-5-5"

tools = [{
    "name": "get_weather",
    "description": "Get the current temperature in Celsius for a city.",
    "input_schema": {"type": "object", "properties": {"city": {"type": "string"}},
                     "required": ["city"]},
}]


def get_weather(city: str) -> str:
    return {"paris": "18 C"}.get(city.lower(), f"No data for {city}")


messages = [{"role": "user", "content": "What's the weather in Paris?"}]
response = client.messages.create(model=MODEL, max_tokens=1024, tools=tools, messages=messages)
tool_use = next(b for b in response.content if b.type == "tool_use")
result = get_weather(**tool_use.input)
messages.append({"role": "assistant", "content": response.content})

# WRONG: text before the result -> 400 error
wrong = messages + [{"role": "user", "content": [
    {"type": "text", "text": "Here are the results:"},
    {"type": "tool_result", "tool_use_id": tool_use.id, "content": result},
]}]
try:
    client.messages.create(model=MODEL, max_tokens=1024, tools=tools, messages=wrong)
except anthropic.BadRequestError as e:
    print("WRONG ->", e)
    # Real run: 400 - messages.2: `tool_use` ids were found without `tool_result` blocks
    # immediately after: toolu_... Each `tool_use` block must have a corresponding
    # `tool_result` block in the next message.
    # The API scanned the user message, hit a text block first, and stopped looking.

# RIGHT: results first, optional text after
right = messages + [{"role": "user", "content": [
    {"type": "tool_result", "tool_use_id": tool_use.id, "content": result},
    {"type": "text", "text": "Also, keep the answer short."},
]}]
final = client.messages.create(model=MODEL, max_tokens=1024, tools=tools, messages=right)
print("RIGHT ->", final.content[-1].text)   # "It's 18°C in Paris right now."
