"""Level 3a, section 3.4: the agent loop. The build.

One round trip is not an agent. An agent is the loop: ask Claude, run whatever tools it asks
for, feed the results back, repeat until it stops asking. Twenty lines. Everything in later
levels is a refinement of this loop.

Run it:
    python 03_agent.py
    python 03_agent.py "Compare the weather in Paris and Tokyo in Fahrenheit"
    python 03_agent.py "What's the weather in Atlantis?"
"""
import sys
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-opus-5-5"


# ---- 1. The tools: ordinary Python functions ----
def get_weather(city: str) -> str:
    fake_db = {"paris": 18, "tokyo": 25, "new york": 12}
    temp = fake_db.get(city.lower())
    return f"{temp} C" if temp is not None else f"No data for {city}"


def celsius_to_fahrenheit(celsius: float) -> str:
    return f"{celsius * 9 / 5 + 32:.1f} F"


TOOL_FUNCTIONS = {
    "get_weather": get_weather,
    "celsius_to_fahrenheit": celsius_to_fahrenheit,
}

# ---- 2. The tool descriptions Claude sees ----
# The "name" is the only thing the two dicts share. It has to match exactly, or the loop
# looks up a key that isn't there.
TOOLS = [
    {
        "name": "get_weather",
        "description": "Get the current temperature in Celsius for a city.",
        "input_schema": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
    {
        "name": "celsius_to_fahrenheit",
        "description": "Convert a temperature from Celsius to Fahrenheit.",
        "input_schema": {
            "type": "object",
            "properties": {"celsius": {"type": "number"}},
            "required": ["celsius"],
        },
    },
]


# ---- 3. The loop ----
def run_agent(question: str, max_steps: int = 10) -> str:
    messages = [{"role": "user", "content": question}]   # the agent's memory
    for step in range(max_steps):                         # safety limit
        response = client.messages.create(
            model=MODEL, max_tokens=2048,
            system="You are a weather assistant. Use tools for live data.",
            tools=TOOLS, messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":            # Claude is done
            return "".join(b.text for b in response.content if b.type == "text")
        results = []
        for block in response.content:                    # every block: handles parallel calls too
            if block.type != "tool_use":
                continue
            print(f"[step {step}] {block.name}({block.input})")
            try:
                output = TOOL_FUNCTIONS[block.name](**block.input)
                results.append({"type": "tool_result",
                                "tool_use_id": block.id, "content": output})
            except Exception as e:                        # report, don't crash
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": f"Error: {e}", "is_error": True})
        messages.append({"role": "user", "content": results})   # all results, ONE message
    return "Stopped: reached max_steps without a final answer."


if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "What's the weather in Paris in Fahrenheit?"
    print(run_agent(question))

# Real runs (test/results.json):
#   Paris in Fahrenheit  -> [step 0] get_weather, [step 1] celsius_to_fahrenheit -> "64.4°F (18°C)".
#                           Nobody told it to chain two tools. The loop let it.
#   Paris vs Tokyo       -> step 0 called get_weather TWICE in one turn (parallel tool use), step 1
#                           converted both. Four tool calls, two trips round the loop. The loop
#                           copes because it iterates over every block. More on this in Level 3b.
#   Atlantis             -> "No data for Atlantis" came back as a normal result. Claude did not
#                           invent a temperature; it explained and asked which Atlantis you meant.
