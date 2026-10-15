"""Level 3b, the build: the Level 3a weather agent, rewritten.

Two decorated functions with strict schemas, the SDK runner, and the parallelism nudge. Count
the lines about the loop: zero. Everything here is a tool or a question.

    python 05_agent.py
    python 05_agent.py "How hot is it in Tokyo, in Fahrenheit, to the nearest degree?"

Same four steps as Level 3a. Same one result per tool_use. Same all results in one message.
Shorter, not different.
"""
import sys
import anthropic
from anthropic import beta_tool

client = anthropic.Anthropic()
MODEL = "claude-opus-5-5"


@beta_tool(strict=True)
def get_weather(city: str) -> str:
    """Get the current temperature in Celsius for a city.

    Args:
        city: The city name, e.g. Paris.
    """
    fake_db = {"paris": 18, "tokyo": 25, "new york": 12}
    temp = fake_db.get(city.lower())
    return f"{temp} C" if temp is not None else f"No data for {city}"


@beta_tool(strict=True)
def celsius_to_fahrenheit(celsius: float) -> str:
    """Convert a temperature from Celsius to Fahrenheit.

    Args:
        celsius: The temperature in Celsius.
    """
    return f"{celsius * 9 / 5 + 32:.1f} F"


question = sys.argv[1] if len(sys.argv) > 1 else "What's the weather in Paris, Tokyo and New York, in Fahrenheit?"
runner = client.beta.messages.tool_runner(
    model=MODEL, max_tokens=2048,
    system="You are a weather assistant. Use tools for live data. For maximum efficiency, "
           "whenever you need to perform multiple independent operations, invoke all relevant "
           "tools simultaneously rather than sequentially.",
    tools=[get_weather, celsius_to_fahrenheit],
    messages=[{"role": "user", "content": question}],
)
calls = turns = 0
for message in runner:                                   # the trace, one assistant turn at a time
    turns += 1
    tool_uses = [b for b in message.content if b.type == "tool_use"]
    calls += len(tool_uses)
    print(f"[turn {turns}] " + (" | ".join(f"{b.name}({b.input})" for b in tool_uses) or "(text)"))
print(message.content[-1].text)
print(f"\n{calls} tool calls / {turns} assistant messages = {calls / turns:.1f} per message")

# Real runs (test/results.json):
#   three cities -> turn 1: 3x get_weather; turn 2: 3x celsius_to_fahrenheit; turn 3: text.
#                   6 / 3 = 2.0 per message, 12.8 s. Same shape as the hand-written loop.
#   "to the nearest degree" -> celsius argument arrived as 25 (int), not "25". Strict at work.
