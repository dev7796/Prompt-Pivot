"""Level 4a, the build: the Level 3a weather agent, upgraded. Two lines in the request, one habit in the loop.

    python 05_agent_4a.py
    python 05_agent_4a.py --uncached            # the control run: same agent, no cache_control
    python 05_agent_4a.py "Paris and Tokyo in Fahrenheit, which is warmer?"

The two lines:   thinking={"type": "adaptive", "display": "summarized"}     # better steps
                 cache_control={"type": "ephemeral"}                        # pay once for briefing + tools
The habit:       messages.append({"role": "assistant", "content": r.content})   # as-is, never tidied

briefing.md is the system prompt (about 1,200 tokens of units, tools, format, declining, tone, examples).
With the two tools it clears the 512 minimum, so the cache has something to hold. Each step prints a
receipt: written / read / uncached. Watch the breakpoint move with the conversation.
"""
import json
import sys
import time
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-opus-5-5"
P_IN, P_OUT = 4 / 1e6, 20 / 1e6                   # Opus 5.5 list: $4/M in, $20/M out; write 1.25x, read 0.05x


def get_weather(city: str) -> str:
    fake_db = {"paris": 18, "tokyo": 25, "new york": 12}
    t = fake_db.get(city.lower())
    return f"{t} C" if t is not None else f"No data for {city}"


def celsius_to_fahrenheit(celsius: float) -> str:
    return f"{celsius * 9 / 5 + 32:.1f} F"


FUNCS = {"get_weather": get_weather, "celsius_to_fahrenheit": celsius_to_fahrenheit}
get_weather_tool = {"name": "get_weather", "description": "Get the current temperature in Celsius for a city.",
                    "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}
celsius_to_fahrenheit_tool = {"name": "celsius_to_fahrenheit", "description": "Convert a temperature from Celsius to Fahrenheit.",
                              "input_schema": {"type": "object", "properties": {"celsius": {"type": "number"}}, "required": ["celsius"]}}

SYSTEM = open("briefing.md").read()        # units, tools, format, declining, tone, examples
TOOLS = [get_weather_tool, celsius_to_fahrenheit_tool]   # from Level 3a


def agent(question, cached=True, max_steps=8):
    messages = [{"role": "user", "content": question}]
    paid = paid_uncached = 0.0
    t0 = time.time()
    for step in range(max_steps):
        kw = {"cache_control": {"type": "ephemeral"}} if cached else {}
        r = client.messages.create(
            model=MODEL, max_tokens=8000,
            thinking={"type": "adaptive", "display": "summarized"},
            system=SYSTEM, tools=TOOLS, messages=messages, **kw,
        )
        for b in r.content:
            if b.type == "thinking" and b.thinking:
                print(f"    THINK {b.thinking}")
            elif b.type == "tool_use":
                print(f"[step {step}] {b.name}({b.input})")
        u = r.usage
        print(f"    written={u.cache_creation_input_tokens} read={u.cache_read_input_tokens} uncached={u.input_tokens}")
        messages.append({"role": "assistant", "content": r.content})      # as-is

        w, rd = u.cache_creation_input_tokens, u.cache_read_input_tokens
        paid += u.input_tokens * P_IN + w * P_IN * 1.25 + rd * P_IN * 0.05 + u.output_tokens * P_OUT
        paid_uncached += (u.input_tokens + w + rd) * P_IN + u.output_tokens * P_OUT

        if r.stop_reason != "tool_use":
            print(f"\n{len(messages) // 2} steps, {time.time() - t0:.1f}s, ${paid:.4f} paid vs ${paid_uncached:.4f} if nothing were cached")
            return "".join(b.text for b in r.content if b.type == "text")
        results = [{"type": "tool_result", "tool_use_id": b.id, "content": FUNCS[b.name](**b.input)}
                   for b in r.content if b.type == "tool_use"]
        messages.append({"role": "user", "content": results})
    return "Stopped at max_steps."


args = [a for a in sys.argv[1:] if not a.startswith("--")]
question = args[0] if args else "What's the weather in Paris, Tokyo and New York, in Fahrenheit?"
print(agent(question, cached="--uncached" not in sys.argv))

# Real run (test/results.json, Bedrock, 2026-10-27), three cities in Fahrenheit, 3 steps, 5.2 s:
#   step 0: get_weather x3 (the briefing says "request all of them at once")   written 0  read 1,214  uncached 4
#   step 1: celsius_to_fahrenheit x3                                            written 0  read 1,454  uncached 2
#   step 2: the answer                                                          written 0  read 1,745  uncached 2
#   4,413 of 4,421 input tokens were cache reads. $0.0084 vs $0.0252 uncached: 67% off.
#   Step 0 READ instead of writing because the same briefing + tools had been cached by the previous demo a
#   minute earlier: five-minute lifetime, refreshed on every hit. A cold start writes 1,214 on step 0 and
#   reads from step 1 (see test/results.json "cache_loop": 1,214/0/4 then 240/1,214/2 then 291/1,454/2; 33% off).
#   Zero thinking blocks with text across the three steps: thinking shows up between tool calls when there
#   is a decision between them, and this question had none. See 03_preserve.py for a run that had one.
