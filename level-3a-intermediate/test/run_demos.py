"""Real runs for Level 3a demos, via Bedrock (AnthropicBedrock). Writes test/results.json.

Every [VERIFY] mark in script/level3a.json maps to one run below. Run this BEFORE synthesizing
narration, then replace each [VERIFY] sentence with what actually happened (SOP step 2).

  cd level3a-movie && python3 test/run_demos.py

Needs live creds in the alps-optum profile. The code is the guide's (pages 24-27) verbatim,
except the client line, which is Bedrock.
"""
import json, sys, time, os
import anthropic

client = anthropic.AnthropicBedrock(aws_region="us-east-1", aws_profile="alps-optum", max_retries=6)
MODEL = "us.anthropic.claude-opus-5-5"
out = {}
HERE = os.path.dirname(os.path.abspath(__file__))

def record(run_name, **kw):
    out[run_name] = kw
    print(f"\n=== {run_name} ===")
    for k, v in kw.items():
        print(f"{k}: {v if isinstance(v, str) else json.dumps(v, default=str)[:1500]}")

def text_of(resp):
    return "".join(b.text for b in resp.content if b.type == "text")

# ---------------------------------------------------------------- 3.2 the tool definition (page 23-24)
tools = [
    {
        "name": "get_weather",
        "description": (
            "Get the current temperature for a city. Use this whenever the "
            "user asks about current weather or temperature. Returns the "
            "temperature in Celsius as a short string. Does not return "
            "forecasts; it only knows current conditions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name, e.g. 'Paris' or 'San Francisco, CA'",
                },
            },
            "required": ["city"],
        },
    }
]

# ---------------------------------------------------------------- tool_cost: count_tokens with / without tools
msg = [{"role": "user", "content": "What's the weather in Paris?"}]
try:
    a = client.messages.count_tokens(model=MODEL, messages=msg).input_tokens
    b = client.messages.count_tokens(model=MODEL, messages=msg, tools=tools).input_tokens
    record("tool_cost", without_tools=a, with_one_tool=b, note="scene tool_cost beat 2")
except Exception as e:
    # Bedrock has no count_tokens: measure with two 1-token create() calls and read usage.input_tokens
    a = client.messages.create(model=MODEL, max_tokens=1, messages=msg).usage.input_tokens
    b = client.messages.create(model=MODEL, max_tokens=1, messages=msg, tools=tools).usage.input_tokens
    record("tool_cost", without_tools=a, with_one_tool=b, method="usage.input_tokens from max_tokens=1 calls (count_tokens not on Bedrock)",
           count_tokens_error=repr(e), note="scene tool_cost beat 2")

# ---------------------------------------------------------------- 3.3 one round trip (page 24-25)
def get_weather(city: str) -> str:
    fake_db = {"paris": 18, "tokyo": 25, "new york": 12}
    temp = fake_db.get(city.lower())
    return f"{temp} C" if temp is not None else f"No data for {city}"

messages = [{"role": "user", "content": "What's the weather in Paris?"}]
response = client.messages.create(model=MODEL, max_tokens=1024, tools=tools, messages=messages)
tool_use = next(b for b in response.content if b.type == "tool_use")
record("step12", stop_reason=response.stop_reason, block_types=[b.type for b in response.content],
       name=tool_use.name, input=tool_use.input, usage=response.usage.model_dump(),
       note="scene step12_live beats 4-5")

result = get_weather(**tool_use.input)
messages += [
    {"role": "assistant", "content": response.content},
    {"role": "user", "content": [{"type": "tool_result", "tool_use_id": tool_use.id, "content": result}]},
]
final = client.messages.create(model=MODEL, max_tokens=1024, tools=tools, messages=messages)
record("step34", result=result, final_text=text_of(final), final_stop=final.stop_reason, note="scene step34_live beat 4")

# ---------------------------------------------------------------- 3.5 WRONG order -> 400 (page 27)
bad = messages[:2] + [{"role": "user", "content": [
    {"type": "text", "text": "Here are the results:"},
    {"type": "tool_result", "tool_use_id": tool_use.id, "content": result},
]}]
try:
    client.messages.create(model=MODEL, max_tokens=200, tools=tools, messages=bad)
    record("wrong_order", error="NO ERROR (unexpected)", note="scene wrong_right beat 2")
except Exception as e:
    record("wrong_order", error=str(e)[:600], note="scene wrong_right beat 2")

good = messages[:2] + [{"role": "user", "content": [
    {"type": "tool_result", "tool_use_id": tool_use.id, "content": result},
    {"type": "text", "text": "Also, keep the answer short."},
]}]
r = client.messages.create(model=MODEL, max_tokens=200, tools=tools, messages=good)
record("right_order", final_text=text_of(r), note="scene wrong_right beat 3")

# ---------------------------------------------------------------- 3.4 the agent loop (page 25-26), with a trace capture
def celsius_to_fahrenheit(celsius: float) -> str:
    return f"{celsius * 9 / 5 + 32:.1f} F"

TOOL_FUNCTIONS = {"get_weather": get_weather, "celsius_to_fahrenheit": celsius_to_fahrenheit}
TOOLS = [
    {"name": "get_weather", "description": "Get the current temperature in Celsius for a city.",
     "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}},
    {"name": "celsius_to_fahrenheit", "description": "Convert a temperature from Celsius to Fahrenheit.",
     "input_schema": {"type": "object", "properties": {"celsius": {"type": "number"}}, "required": ["celsius"]}},
]

def run_agent(question: str, max_steps: int = 10, funcs=TOOL_FUNCTIONS):
    trace = []
    messages = [{"role": "user", "content": question}]
    for step in range(max_steps):
        response = client.messages.create(model=MODEL, max_tokens=2048,
                                          system="You are a weather assistant. Use tools for live data.",
                                          tools=TOOLS, messages=messages)
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text"), trace
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            trace.append(f"[step {step}] {block.name}({block.input})")
            try:
                output = funcs[block.name](**block.input)
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
            except Exception as e:
                trace.append(f"[step {step}]   -> Error: {e}")
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": f"Error: {e}", "is_error": True})
        messages.append({"role": "user", "content": results})
    return "Stopped: reached max_steps without a final answer.", trace

for name, q in [("agent_paris_f", "What's the weather in Paris in Fahrenheit?"),
                ("agent_compare", "Compare Paris and Tokyo in Fahrenheit."),
                ("agent_atlantis", "What's the weather in Atlantis?")]:
    ans, trace = run_agent(q)
    record(name, question=q, trace=trace, answer=ans, note="scene agent_run")

# ---------------------------------------------------------------- errors that teach (page 27): instructive error -> retry
def get_weather_strict(city: str) -> str:
    fake_db = {"paris": 18, "tokyo": 25, "new york": 12, "san francisco, ca": 15, "san francisco": 15}
    if city.lower() not in fake_db:
        raise ValueError(f"City not found. Try the full name, e.g. 'San Francisco, CA'")
    return f"{fake_db[city.lower()]} C"

ans, trace = run_agent("What's the weather in SF?", funcs={**TOOL_FUNCTIONS, "get_weather": get_weather_strict})
record("error_retry", trace=trace, answer=ans, note="scene errors beat 3")

json.dump(out, open(os.path.join(HERE, "results.json"), "w"), indent=1, default=str)
print(f"\nwrote {os.path.join(HERE, 'results.json')} with {len(out)} runs")
