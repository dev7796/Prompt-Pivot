"""Follow-up runs for Level 3b after run_demos.py: fixes the Haiku model id, inspects the
tool_choice=none response blocks, and checks @beta_tool(strict=True). Merges into results.json.

  AWS_CONFIG_FILE=$HOME/.aws/config AWS_SHARED_CREDENTIALS_FILE=$HOME/.aws/credentials \
  uv run --quiet --with anthropic --with boto3 python3 test/run_followups.py
"""
import json, os, time, traceback
import anthropic
from anthropic import beta_tool

client = anthropic.AnthropicBedrock(aws_region="us-east-1", aws_profile="alps-optum", max_retries=6)
MODEL = "us.anthropic.claude-opus-5-5"
HAIKU = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results.json")
out = json.load(open(RES))

def record(run_name, **kw):
    out[run_name] = kw
    print(f"\n=== {run_name} ===")
    for k, v in kw.items():
        print(f"{k}: {v if isinstance(v, str) else json.dumps(v, default=str, ensure_ascii=False)[:1200]}")

def attempt(run_name, fn):
    try:
        fn()
    except Exception as e:
        record(run_name, error=f"{type(e).__name__}: {e}")

TOOLS = [
    {"name": "get_weather", "description": "Get the current temperature in Celsius for a city.",
     "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}},
]
def text_of(r): return "".join(b.text for b in r.content if b.type == "text")
def tool_uses(r): return [{"name": b.name, "input": b.input} for b in r.content if b.type == "tool_use"]

def forced_haiku():
    r = client.messages.create(model=HAIKU, max_tokens=1024, tools=TOOLS,
                               tool_choice={"type": "tool", "name": "get_weather"},
                               messages=[{"role": "user", "content": "Weather in Paris?"}])
    record("forced_haiku", stop_reason=r.stop_reason, content_types=[b.type for b in r.content],
           tool_uses=tool_uses(r), text_before=text_of(r), note="choice_live: forced on Haiku 4.5")
attempt("forced_haiku", forced_haiku)

def auto_haiku():
    r = client.messages.create(model=HAIKU, max_tokens=1024, tools=TOOLS,
                               messages=[{"role": "user", "content": "Weather in Paris?"}])
    record("auto_haiku", stop_reason=r.stop_reason, content_types=[b.type for b in r.content],
           tool_uses=tool_uses(r), text_before=text_of(r), note="choice_live: same on Haiku with auto, for the 'no text before' contrast")
attempt("auto_haiku", auto_haiku)

def none_opus():
    r = client.messages.create(model=MODEL, max_tokens=1024, tools=TOOLS, tool_choice={"type": "none"},
                               messages=[{"role": "user", "content": "What's the weather in Paris?"}])
    blocks = [{"type": b.type, "text": getattr(b, "text", None)} for b in r.content]
    record("none_opus", stop_reason=r.stop_reason, blocks=blocks, text=text_of(r), usage=dict(r.usage),
           note="choice_live: first run returned end_turn with empty text; what blocks exactly?")
attempt("none_opus", none_opus)

def none_opus_instructed():
    r = client.messages.create(model=MODEL, max_tokens=1024, tools=TOOLS, tool_choice={"type": "none"},
                               system="You are a weather assistant. If you cannot use a tool, say so plainly.",
                               messages=[{"role": "user", "content": "What's the weather in Paris?"}])
    blocks = [{"type": b.type, "text": getattr(b, "text", None)} for b in r.content]
    record("none_opus_instructed", stop_reason=r.stop_reason, blocks=blocks, text=text_of(r),
           note="choice_live: none with a system prompt")
attempt("none_opus_instructed", none_opus_instructed)

@beta_tool(strict=True)
def celsius_to_fahrenheit_s(celsius: float) -> str:
    """Convert a temperature from Celsius to Fahrenheit.

    Args:
        celsius: The temperature in Celsius.
    """
    return f"{celsius * 9 / 5 + 32:.1f} F"

def strict_decorator():
    record("strict_decorator", schema=celsius_to_fahrenheit_s.to_dict(),
           note="build_code: @beta_tool(strict=True) exists; what does to_dict() show?")
attempt("strict_decorator", strict_decorator)

@beta_tool(strict=True)
def get_weather_s(city: str) -> str:
    """Get the current temperature in Celsius for a city.

    Args:
        city: The city name, e.g. Paris.
    """
    return {"paris": "18 C", "tokyo": "25 C", "new york": "12 C"}.get(city.lower(), "No data")

def runner_strict_build():
    t0, trace, calls, turns, final = time.time(), [], 0, 0, None
    runner = client.beta.messages.tool_runner(
        model=MODEL, max_tokens=2048,
        system=("You are a weather assistant. Use tools for live data. For maximum efficiency, whenever you need "
                "to perform multiple independent operations, invoke all relevant tools simultaneously rather than sequentially."),
        tools=[get_weather_s, celsius_to_fahrenheit_s],
        messages=[{"role": "user", "content": "What's the weather in Paris, Tokyo and New York, in Fahrenheit?"}])
    for msg in runner:
        turns += 1
        tus = [f"{b.name}({b.input})" for b in msg.content if b.type == "tool_use"]
        calls += len(tus); trace.append(f"[turn {turns}] " + (" | ".join(tus) if tus else "(text)")); final = msg
    record("runner_strict_build", trace=trace, answer=final.content[-1].text,
           stats={"tool_calls": calls, "assistant_messages": turns,
                  "calls_per_assistant_msg": round(calls / max(turns, 1), 2), "seconds": round(time.time() - t0, 1)},
           note="build_run with strict decorated tools")
attempt("runner_strict_build", runner_strict_build)

json.dump(out, open(RES, "w"), indent=1, default=str, ensure_ascii=False)
print(f"\nmerged into {RES}: {len(out)} runs")
