"""Level 3b, section 3.7: parallel tool use.

Claude can request several tools in one turn. The Level 3a loop already handles it, because it
iterates over every tool_use block and sends ALL results back in ONE user message. This version:
  - runs the requested tools concurrently with a ThreadPoolExecutor (pool.map keeps order)
  - prints the trace and the metric: tool calls / assistant messages (above 1.0 = parallel)
  - lets you disable parallelism (the switch lives INSIDE tool_choice) and add the nudge

    python 02_parallel.py
    python 02_parallel.py --serial          # one call per turn (disable_parallel_tool_use)
    python 02_parallel.py --nudge           # the guide's system-prompt sentence
    python 02_parallel.py --slow            # 1 s per tool, to see the pool pay off

The #1 way to LOSE parallelism: sending each result in its own user message. The API accepts it,
nothing errors, and a few turns later Claude is making one call per turn. Collect, then append once.
"""
import sys, time
from concurrent.futures import ThreadPoolExecutor
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-opus-5-5"
SLOW = "--slow" in sys.argv


def get_weather(city: str) -> str:
    if SLOW:
        time.sleep(1.0)                                   # stand-in for a real network call
    fake_db = {"paris": 18, "tokyo": 25, "new york": 12}
    temp = fake_db.get(city.lower())
    return f"{temp} C" if temp is not None else f"No data for {city}"


def celsius_to_fahrenheit(celsius: float) -> str:
    if SLOW:
        time.sleep(1.0)
    return f"{celsius * 9 / 5 + 32:.1f} F"


TOOL_FUNCTIONS = {"get_weather": get_weather, "celsius_to_fahrenheit": celsius_to_fahrenheit}
TOOLS = [
    {"name": "get_weather", "description": "Get the current temperature in Celsius for a city.",
     "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}},
    {"name": "celsius_to_fahrenheit", "description": "Convert a temperature from Celsius to Fahrenheit.",
     "input_schema": {"type": "object", "properties": {"celsius": {"type": "number"}}, "required": ["celsius"]}},
]
NUDGE = ("For maximum efficiency, whenever you need to perform multiple independent operations, "
         "invoke all relevant tools simultaneously rather than sequentially.")


def run_one(block):
    try:
        out = TOOL_FUNCTIONS[block.name](**block.input)
        return {"type": "tool_result", "tool_use_id": block.id, "content": out}
    except Exception as e:
        return {"type": "tool_result", "tool_use_id": block.id, "content": f"Error: {e}", "is_error": True}


def run_agent(question: str, max_steps: int = 10) -> str:
    system = "You are a weather assistant. Use tools for live data."
    if "--nudge" in sys.argv:
        system += " " + NUDGE
    kw = {}
    if "--serial" in sys.argv:
        kw["tool_choice"] = {"type": "auto", "disable_parallel_tool_use": True}   # INSIDE tool_choice
    messages = [{"role": "user", "content": question}]
    calls = assistant_msgs = 0
    t0 = time.time()
    for step in range(max_steps):
        response = client.messages.create(model=MODEL, max_tokens=2048, system=system,
                                          tools=TOOLS, messages=messages, **kw)
        messages.append({"role": "assistant", "content": response.content})
        assistant_msgs += 1
        if response.stop_reason != "tool_use":
            break
        tool_blocks = [b for b in response.content if b.type == "tool_use"]
        calls += len(tool_blocks)
        print(f"[step {step}] " + " | ".join(f"{b.name}({b.input})" for b in tool_blocks))
        t1 = time.time()
        with ThreadPoolExecutor() as pool:
            results = list(pool.map(run_one, tool_blocks))        # keeps the original order
        print(f"[step {step}]   -> " + " | ".join(str(r["content"]) for r in results) + f"   ({time.time() - t1:.1f}s)")
        messages.append({"role": "user", "content": results})      # ALL results, ONE message
    else:
        return "Stopped: reached max_steps without a final answer."
    print(f"\n{calls} tool calls / {assistant_msgs} assistant messages = "
          f"{calls / assistant_msgs:.2f} per message · {time.time() - t0:.1f}s")
    return "".join(b.text for b in response.content if b.type == "text")


if __name__ == "__main__":
    print(run_agent("What's the weather in Paris, Tokyo and New York, in Fahrenheit?"))

# Real runs (test/results.json):
#   default   -> step 0: 3x get_weather; step 1: 3x conversion. 6 calls / 3 msgs = 2.0, 10.0 s.
#   --serial  -> 6 steps, 0.86 per message, 18.1 s, and Claude's answer ends: "I made these
#                lookups one by one when I could have run them all at once."
#   --nudge   -> 2.0, same as default: Opus was already batching everything it could.
#   --slow    -> pool: 1.0 s per batch (18.5 s -> 10.2 s end to end vs running them serially).
#   Paris, Tokyo and Atlantis -> "No data" goes back as a normal result; Claude converts the two
#                it has and says Atlantis is "a legendary city, not a real place". Failures are
#                results too: drop one and you break the tool_use/tool_result pairing (a 400).
#   Top-level disable_parallel_tool_use=True -> SDK TypeError before the request is sent.
