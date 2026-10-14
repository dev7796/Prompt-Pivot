"""Level 3a, section 3.5: errors that teach.

An instructive error is a mini-prompt. You are writing it for the model that reads it next,
not for a log file. "City not found" is a dead end; "City not found. Try the full name with
region, e.g. 'San Francisco, CA'" is a next move.

This is 03_agent.py with one change: get_weather insists on the "City, ST" form and raises
an instructive error otherwise. The loop already catches it and returns is_error=True.

    python 05_instructive_errors.py "What's the weather in SF?"
    python 05_instructive_errors.py "How warm is it in Lyon right now?"
"""
import sys
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-opus-5-5"


def get_weather(city: str) -> str:
    fake_db = {"paris": 18, "tokyo": 25, "new york": 12, "san francisco, ca": 15}
    if city.lower() not in fake_db:
        raise ValueError("City not found. Try the full name with region, "
                         "e.g. 'San Francisco, CA'")
    return f"{fake_db[city.lower()]} C"


def celsius_to_fahrenheit(celsius: float) -> str:
    return f"{celsius * 9 / 5 + 32:.1f} F"


TOOL_FUNCTIONS = {"get_weather": get_weather, "celsius_to_fahrenheit": celsius_to_fahrenheit}
TOOLS = [
    {"name": "get_weather",
     "description": "Get the current temperature in Celsius for a city.",
     "input_schema": {"type": "object", "properties": {"city": {"type": "string"}},
                      "required": ["city"]}},
    {"name": "celsius_to_fahrenheit",
     "description": "Convert a temperature from Celsius to Fahrenheit.",
     "input_schema": {"type": "object", "properties": {"celsius": {"type": "number"}},
                      "required": ["celsius"]}},
]


def run_agent(question: str, max_steps: int = 10) -> str:
    messages = [{"role": "user", "content": question}]
    for step in range(max_steps):
        response = client.messages.create(
            model=MODEL, max_tokens=2048,
            system="You are a weather assistant. Use tools for live data.",
            tools=TOOLS, messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            print(f"[step {step}] {block.name}({block.input})")
            try:
                output = TOOL_FUNCTIONS[block.name](**block.input)
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
            except Exception as e:
                print(f"[step {step}]   -> Error: {e}")
                # Tool output, including errors, goes ONLY into a tool_result's content.
                # Never into the system prompt, never as a plain user message: text in the
                # instruction slot is an order; text in the data slot is data Claude is
                # trained to be skeptical of. Level 5 covers injection properly.
                results.append({"type": "tool_result", "tool_use_id": block.id,
                                "content": f"Error: {e}", "is_error": True})
        messages.append({"role": "user", "content": results})
    return "Stopped: reached max_steps without a final answer."


if __name__ == "__main__":
    question = sys.argv[1] if len(sys.argv) > 1 else "What's the weather in SF?"
    print(run_agent(question))

# Real runs (test/results_error_variants.json):
#   SF    -> get_weather('San Francisco') [Claude expanded "SF" on its own] -> error ->
#            get_weather('San Francisco, CA') -> "It's 15°C (about 59°F) in San Francisco right now."
#            One error, one retry, right answer. The error message did the teaching.
#   Lyon  -> Lyon; Lyon, France; Lyon, Auvergne-Rhône-Alpes, France; Lyon, FR. All fail. Then:
#            "Its error message gives a US-style example ('San Francisco, CA'), so it may not
#            support cities outside the US." Correct diagnosis. The lesson: an instructive error
#            is a prompt, and a prompt with a US example produces US-shaped guesses. Write the
#            example to match the coverage you actually have.
