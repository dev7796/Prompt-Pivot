"""Probe 2: (a) tool_choice=none on a question that does not need the tool; (b) serial vs thread-pool
execution with a 1 s sleep in get_weather so the timing difference is real. Merges into results.json."""
import json, os, time
from concurrent.futures import ThreadPoolExecutor
import anthropic

client = anthropic.AnthropicBedrock(aws_region="us-east-1", aws_profile="alps-optum", max_retries=6)
MODEL = "us.anthropic.claude-opus-5-5"
HERE = os.path.dirname(os.path.abspath(__file__)); RES = os.path.join(HERE, "results.json")
out = json.load(open(RES))
def record(n, **kw):
    out[n] = kw; print(f"\n=== {n} ===")
    for k, v in kw.items(): print(f"{k}: {v if isinstance(v, str) else json.dumps(v, default=str, ensure_ascii=False)[:900]}")
def text_of(r): return "".join(b.text for b in r.content if b.type == "text")

TOOLS = [{"name": "get_weather", "description": "Get the current temperature in Celsius for a city.",
          "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}},
         {"name": "celsius_to_fahrenheit", "description": "Convert a temperature from Celsius to Fahrenheit.",
          "input_schema": {"type": "object", "properties": {"celsius": {"type": "number"}}, "required": ["celsius"]}}]

# (a) none, question that needs no tool
r = client.messages.create(model=MODEL, max_tokens=256, tools=TOOLS, tool_choice={"type": "none"},
                           messages=[{"role": "user", "content": "In one sentence, what does a weather assistant do?"}])
record("none_opus_no_tool_needed", stop_reason=r.stop_reason, blocks=[b.type for b in r.content], text=text_of(r),
       output_tokens=r.usage.output_tokens)

# (a2) none, tool question, but asked to answer from general knowledge
r = client.messages.create(model=MODEL, max_tokens=256, tools=TOOLS, tool_choice={"type": "none"},
                           messages=[{"role": "user", "content": "What's the weather in Paris? If you can't check, say what you'd need."}])
record("none_opus_asked_to_explain", stop_reason=r.stop_reason, blocks=[b.type for b in r.content], text=text_of(r),
       output_tokens=r.usage.output_tokens)

# (b) slow tool: serial vs pool
def get_weather(city: str) -> str:
    time.sleep(1.0)
    return {"paris": "18 C", "tokyo": "25 C", "new york": "12 C"}.get(city.lower(), f"No data for {city}")
def celsius_to_fahrenheit(celsius: float) -> str:
    time.sleep(1.0); return f"{celsius * 9 / 5 + 32:.1f} F"
FN = {"get_weather": get_weather, "celsius_to_fahrenheit": celsius_to_fahrenheit}

def run(parallel_exec):
    messages = [{"role": "user", "content": "What's the weather in Paris, Tokyo and New York, in Fahrenheit?"}]
    t0, tool_secs, trace = time.time(), 0.0, []
    for step in range(10):
        r = client.messages.create(model=MODEL, max_tokens=2048, system="You are a weather assistant. Use tools for live data.",
                                   tools=TOOLS, messages=messages)
        messages.append({"role": "assistant", "content": r.content})
        if r.stop_reason != "tool_use": break
        blocks = [b for b in r.content if b.type == "tool_use"]
        def one(b):
            return {"type": "tool_result", "tool_use_id": b.id, "content": FN[b.name](**b.input)}
        t1 = time.time()
        if parallel_exec:
            with ThreadPoolExecutor() as pool: results = list(pool.map(one, blocks))
        else:
            results = [one(b) for b in blocks]
        tool_secs += time.time() - t1
        trace.append(f"[step {step}] {len(blocks)} calls, tools took {time.time()-t1:.1f}s")
        messages.append({"role": "user", "content": results})
    return {"trace": trace, "tool_seconds": round(tool_secs, 1), "total_seconds": round(time.time() - t0, 1)}

record("slow_serial", **run(False), note="parallel_code: 1 s per tool, run one after another")
record("slow_pool", **run(True), note="parallel_code: 1 s per tool, ThreadPoolExecutor")

json.dump(out, open(RES, "w"), indent=1, default=str, ensure_ascii=False)
print(f"\nmerged: {len(out)} runs")
