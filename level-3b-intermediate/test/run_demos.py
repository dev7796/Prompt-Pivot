"""Real runs for Level 3b demos, via Bedrock (AnthropicBedrock). Writes test/results.json.

Every [VERIFY] mark in script/level3b.json maps to one run below. Run this BEFORE synthesizing
narration, then replace each [VERIFY] sentence in script/build_script.py with what actually
happened (SOP step 2).

  cd level3b-movie && uv run --quiet --with anthropic python3 test/run_demos.py

Needs live creds in the alps-optum profile. Code is the guide's (pages 27-30) except the client
line. Each run is wrapped so one failure (expected: forced tool_choice on Opus) does not stop the rest.
"""
import json, os, time, traceback
from concurrent.futures import ThreadPoolExecutor
import anthropic
from anthropic import beta_tool

client = anthropic.AnthropicBedrock(aws_region="us-east-1", aws_profile="alps-optum", max_retries=6)
MODEL = "us.anthropic.claude-opus-5-5"
HAIKU = "us.anthropic.claude-haiku-4-5"
HERE = os.path.dirname(os.path.abspath(__file__))
out = {}


def record(run_name, **kw):
    out[run_name] = kw
    print(f"\n=== {run_name} ===")
    for k, v in kw.items():
        print(f"{k}: {v if isinstance(v, str) else json.dumps(v, default=str)[:1500]}")


def attempt(run_name, fn):
    try:
        fn()
    except Exception as e:
        record(run_name, error=f"{type(e).__name__}: {e}", trace=traceback.format_exc()[-800:])


def text_of(resp):
    return "".join(b.text for b in resp.content if b.type == "text")


def tool_uses(resp):
    return [{"name": b.name, "input": b.input} for b in resp.content if b.type == "tool_use"]


# ---------------------------------------------------------------- tools from 3a (page 25)
def get_weather(city: str) -> str:
    fake_db = {"paris": 18, "tokyo": 25, "new york": 12}
    temp = fake_db.get(city.lower())
    return f"{temp} C" if temp is not None else f"No data for {city}"


def celsius_to_fahrenheit(celsius: float) -> str:
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


def run_agent(question, tool_choice=None, system="You are a weather assistant. Use tools for live data.",
              parallel_exec=False, final_none=False, max_steps=10):
    """3a loop + optional tool_choice, thread-pool execution, and a tool_choice=none final turn.
    Returns (trace, answer, stats)."""
    messages = [{"role": "user", "content": question}]
    trace, calls, assistant_msgs, t0 = [], 0, 0, time.time()
    kw = {"tool_choice": tool_choice} if tool_choice else {}
    for step in range(max_steps):
        r = client.messages.create(model=MODEL, max_tokens=2048, system=system, tools=TOOLS,
                                   messages=messages, **kw)
        messages.append({"role": "assistant", "content": r.content})
        assistant_msgs += 1
        if r.stop_reason != "tool_use":
            answer = text_of(r)
            break
        blocks = [b for b in r.content if b.type == "tool_use"]
        calls += len(blocks)
        trace.append(f"[step {step}] " + " | ".join(f"{b.name}({b.input})" for b in blocks))

        def run_one(block):
            try:
                o = TOOL_FUNCTIONS[block.name](**block.input)
                return {"type": "tool_result", "tool_use_id": block.id, "content": o}
            except Exception as e:
                return {"type": "tool_result", "tool_use_id": block.id, "content": f"Error: {e}", "is_error": True}

        if parallel_exec:
            with ThreadPoolExecutor() as pool:
                results = list(pool.map(run_one, blocks))
        else:
            results = [run_one(b) for b in blocks]
        trace.append(f"[step {step}]   -> " + " | ".join(str(x["content"]) for x in results))
        messages.append({"role": "user", "content": results})   # ALL results, ONE message
    else:
        answer = "Stopped: reached max_steps"
    if final_none:
        messages.append({"role": "user", "content": "Write the final answer for the user."})
        r = client.messages.create(model=MODEL, max_tokens=1024, system=system, tools=TOOLS,
                                   messages=messages, tool_choice={"type": "none"})
        answer = text_of(r)
        trace.append(f"[final, tool_choice=none] stop_reason={r.stop_reason}")
    stats = {"tool_calls": calls, "assistant_messages": assistant_msgs,
             "calls_per_assistant_msg": round(calls / max(assistant_msgs, 1), 2),
             "seconds": round(time.time() - t0, 1)}
    return trace, answer, stats


# ---------------------------------------------------------------- 3.6 tool choice
def forced_opus():
    r = client.messages.create(model=MODEL, max_tokens=1024, tools=TOOLS,
                               tool_choice={"type": "tool", "name": "get_weather"},
                               messages=[{"role": "user", "content": "Weather in Paris?"}])
    record("forced_opus", stop_reason=r.stop_reason, tool_uses=tool_uses(r), text=text_of(r),
           note="hook/choice_live: guide says this should be a 400 on Opus 5.5")
attempt("forced_opus", forced_opus)

def forced_haiku():
    r = client.messages.create(model=HAIKU, max_tokens=1024, tools=TOOLS,
                               tool_choice={"type": "tool", "name": "get_weather"},
                               messages=[{"role": "user", "content": "Weather in Paris?"}])
    record("forced_haiku", stop_reason=r.stop_reason, content_types=[b.type for b in r.content],
           tool_uses=tool_uses(r), text_before=text_of(r), note="choice_live: expect tool_use, no text")
attempt("forced_haiku", forced_haiku)

def any_opus():
    r = client.messages.create(model=MODEL, max_tokens=1024, tools=TOOLS, tool_choice={"type": "any"},
                               messages=[{"role": "user", "content": "Weather in Paris?"}])
    record("any_opus", stop_reason=r.stop_reason, tool_uses=tool_uses(r), note="gotchas: any on Opus")
attempt("any_opus", any_opus)

def none_opus():
    r = client.messages.create(model=MODEL, max_tokens=1024, tools=TOOLS, tool_choice={"type": "none"},
                               messages=[{"role": "user", "content": "What's the weather in Paris?"}])
    record("none_opus", stop_reason=r.stop_reason, tool_uses=tool_uses(r), text=text_of(r),
           note="choice_live: none works everywhere; what does Claude say without the tool?")
attempt("none_opus", none_opus)

def final_none():
    trace, ans, stats = run_agent("What's the weather in Paris in Fahrenheit?", final_none=True)
    record("final_none", trace=trace, answer=ans, stats=stats, note="choice_final")
attempt("final_none", final_none)

# ---------------------------------------------------------------- 3.7 parallel
Q3 = "What's the weather in Paris, Tokyo and New York, in Fahrenheit?"

def three_cities():
    trace, ans, stats = run_agent(Q3)
    record("three_cities", trace=trace, answer=ans, stats=stats, note="hook + parallel_live")
attempt("three_cities", three_cities)

def three_cities_pool():
    trace, ans, stats = run_agent(Q3, parallel_exec=True)
    record("three_cities_pool", trace=trace, answer=ans, stats=stats, note="parallel_code: thread pool")
attempt("three_cities_pool", three_cities_pool)

def partial_failure():
    trace, ans, stats = run_agent("What's the weather in Paris, Tokyo and Atlantis, in Fahrenheit?")
    record("partial_failure", trace=trace, answer=ans, stats=stats, note="parallel_partial")
attempt("partial_failure", partial_failure)

def parallel_disabled():
    trace, ans, stats = run_agent(Q3, tool_choice={"type": "auto", "disable_parallel_tool_use": True})
    record("parallel_disabled", trace=trace, answer=ans, stats=stats, note="parallel_dial")
attempt("parallel_disabled", parallel_disabled)

def disable_top_level():
    client.messages.create(model=MODEL, max_tokens=256, tools=TOOLS, disable_parallel_tool_use=True,
                           messages=[{"role": "user", "content": Q3}])
    record("disable_top_level", result="accepted?!", note="gotchas: expected unexpected-parameter error")
attempt("disable_top_level", disable_top_level)

def nudged():
    trace, ans, stats = run_agent(Q3, system="You are a weather assistant. Use tools for live data. " + NUDGE)
    record("nudged", trace=trace, answer=ans, stats=stats, note="parallel_dial: does the nudge change the metric?")
attempt("nudged", nudged)

# ---------------------------------------------------------------- 3.8 strict
BOOK_SCHEMA = {
    "type": "object",
    "properties": {
        "room": {"type": "string", "enum": ["Everest", "K2", "Denali"]},
        "attendees": {"type": "integer"},
        "date": {"type": "string", "format": "date"},
    },
    "required": ["room", "attendees", "date"],
    "additionalProperties": False,
}
SLOPPY = "Book the big room for a dozen of us a week from Friday."
SYS_BOOK = "You book meeting rooms. Today is Wednesday 2026-10-14. Everest is the largest room."

def book(strict):
    tool = {"name": "book_meeting", "description": "Book a meeting room for a number of attendees.",
            "input_schema": BOOK_SCHEMA}
    if strict:
        tool["strict"] = True
    r = client.messages.create(model=MODEL, max_tokens=1024, tools=[tool], system=SYS_BOOK,
                               messages=[{"role": "user", "content": SLOPPY}])
    tu = tool_uses(r)
    types = {k: type(v).__name__ for k, v in tu[0]["input"].items()} if tu else {}
    return dict(stop_reason=r.stop_reason, tool_uses=tu, arg_types=types, text=text_of(r))

attempt("book_nonstrict", lambda: record("book_nonstrict", **book(False), note="strict_live: without strict"))
attempt("book_strict", lambda: record("book_strict", **book(True), note="strict_live: with strict"))

def strict_many_trials():
    """Non-strict occasionally sends '2' or 'two'; run 5 trials each to catch a real divergence."""
    rows = []
    for i in range(5):
        for strict in (False, True):
            try:
                b = book(strict)
                rows.append({"trial": i, "strict": strict, "input": b["tool_uses"][0]["input"] if b["tool_uses"] else None,
                             "types": b["arg_types"]})
            except Exception as e:
                rows.append({"trial": i, "strict": strict, "error": str(e)[:200]})
    record("book_trials", rows=rows, note="strict_live: look for any non-integer attendees / off-enum room without strict")
attempt("book_trials", strict_many_trials)

# ---------------------------------------------------------------- 3.9 runner
@beta_tool
def get_weather_t(city: str) -> str:
    """Get the current temperature in Celsius for a city.

    Args:
        city: The city name, e.g. Paris.
    """
    return {"paris": "18 C", "tokyo": "25 C", "new york": "12 C"}.get(city.lower(), "No data")


@beta_tool
def celsius_to_fahrenheit_t(celsius: float) -> str:
    """Convert a temperature from Celsius to Fahrenheit.

    Args:
        celsius: The temperature in Celsius.
    """
    return f"{celsius * 9 / 5 + 32:.1f} F"


def runner_schema():
    tool_dict = get_weather_t.to_dict() if hasattr(get_weather_t, "to_dict") else getattr(get_weather_t, "input_schema", None)
    record("runner_schema", schema=tool_dict, attrs=[a for a in dir(get_weather_t) if not a.startswith("_")][:30],
           note="runner_live: how to print the generated tool dict")
attempt("runner_schema", runner_schema)

def runner_tokyo():
    t0 = time.time()
    runner = client.beta.messages.tool_runner(model=MODEL, max_tokens=1024, tools=[get_weather_t],
                                              messages=[{"role": "user", "content": "Weather in Tokyo?"}])
    final = runner.until_done()
    record("runner_tokyo", final_text=final.content[-1].text, seconds=round(time.time() - t0, 1),
           note="runner_live: does the runner work on Bedrock?")
attempt("runner_tokyo", runner_tokyo)

def runner_build():
    t0, trace, calls, turns = time.time(), [], 0, 0
    runner = client.beta.messages.tool_runner(
        model=MODEL, max_tokens=2048, system="You are a weather assistant. Use tools for live data. " + NUDGE,
        tools=[get_weather_t, celsius_to_fahrenheit_t], messages=[{"role": "user", "content": Q3}])
    final = None
    for msg in runner:
        turns += 1
        tus = [f"{b.name}({b.input})" for b in msg.content if b.type == "tool_use"]
        calls += len(tus)
        trace.append(f"[turn {turns}] " + (" | ".join(tus) if tus else "(text)"))
        final = msg
    record("runner_build", trace=trace, answer=final.content[-1].text if final else None,
           stats={"tool_calls": calls, "assistant_messages": turns,
                  "calls_per_assistant_msg": round(calls / max(turns, 1), 2), "seconds": round(time.time() - t0, 1)},
           note="hook + build_run")
attempt("runner_build", runner_build)

def runner_strict_type():
    arg_types = []
    runner = client.beta.messages.tool_runner(
        model=MODEL, max_tokens=1024, tools=[get_weather_t, celsius_to_fahrenheit_t],
        messages=[{"role": "user", "content": "How hot is it in Tokyo, in Fahrenheit, to the nearest degree?"}])
    final = None
    for msg in runner:
        for b in msg.content:
            if b.type == "tool_use" and b.name == "celsius_to_fahrenheit_t":
                arg_types.append({"celsius": b.input.get("celsius"), "type": type(b.input.get("celsius")).__name__})
        final = msg
    record("runner_strict_type", celsius_args=arg_types, answer=final.content[-1].text if final else None,
           note="build_run: is celsius a number, not a string?")
attempt("runner_strict_type", runner_strict_type)

json.dump(out, open(os.path.join(HERE, "results.json"), "w"), indent=1, default=str, ensure_ascii=False)
errs = [k for k, v in out.items() if "error" in v]
print(f"\nwrote {os.path.join(HERE, 'results.json')} with {len(out)} runs; errored: {errs}")
