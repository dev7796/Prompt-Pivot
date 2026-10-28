"""Real runs for Level 4a demos (4.1 thinking, 4.2 prompt caching). Writes test/results.json.

Back on Bedrock for everything: thinking and caching are Messages API features.

  AWS_CONFIG_FILE=$HOME/.aws/config AWS_SHARED_CREDENTIALS_FILE=$HOME/.aws/credentials \\
  uv run --quiet --with anthropic --with boto3 --with pypdf python3 test/run_demos.py
  ... run_demos.py --only cache_handbook,cache_loop      # re-run some and merge

Every run is wrapped so an expected 400 (we WANT several) does not stop the rest. Mark map is in
script/PLAN.md. Cost: Opus 5.5 at $4/M in, $20/M out; the thinking demos are the output-heavy ones.
"""
import json, os, sys, time, traceback, pathlib
import anthropic

HERE = pathlib.Path(__file__).resolve().parent
ONLY = set()
if "--only" in sys.argv:
    ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(","))
out = json.load(open(HERE / "results.json")) if (ONLY and (HERE / "results.json").exists()) else {}

client = anthropic.AnthropicBedrock(aws_region="us-east-1", aws_profile="alps-optum", max_retries=3)
OPUS = "us.anthropic.claude-opus-5-5"
HAIKU = "us.anthropic.claude-haiku-4-5-20251001-v1:0"   # the short alias 3b used is gone from Bedrock

# Opus 5.5 list prices (per token). Cache write 1.25x, cache read 0.05x on Opus 5.5.
P_IN, P_OUT = 4 / 1e6, 20 / 1e6
def cost(u, cached=True):
    w = getattr(u, "cache_creation_input_tokens", 0) or 0
    r = getattr(u, "cache_read_input_tokens", 0) or 0
    if cached:
        return (u.input_tokens * P_IN) + (w * P_IN * 1.25) + (r * P_IN * 0.05) + u.output_tokens * P_OUT
    return (u.input_tokens + w + r) * P_IN + u.output_tokens * P_OUT   # as if nothing were cached


def record(name, **kw):
    out[name] = kw
    print(f"\n=== {name} ===")
    for k, v in kw.items():
        print(f"{k}: {v if isinstance(v, str) else json.dumps(v, default=str, ensure_ascii=False)[:1500]}")


def attempt(name, fn):
    if ONLY and name not in ONLY:
        return
    try:
        fn()
    except Exception as e:
        record(name, error=f"{type(e).__name__}: {e}"[:700], trace=traceback.format_exc()[-400:])


def usage_of(r):
    u = r.usage
    return {"input": u.input_tokens, "output": u.output_tokens,
            "cache_write": getattr(u, "cache_creation_input_tokens", 0) or 0,
            "cache_read": getattr(u, "cache_read_input_tokens", 0) or 0}


def text_of(r):
    return "".join(b.text for b in r.content if b.type == "text")


def thinking_of(r):
    return "".join(getattr(b, "thinking", "") or "" for b in r.content if b.type == "thinking")


def timed(fn):
    t0 = time.time(); r = fn(); return r, round(time.time() - t0, 1)


GCD_Q = "What is the GCD of 1071 and 462?"

# ---------------------------------------------------------------- 4.1 thinking: see it
def gcd_summarized():
    r, s = timed(lambda: client.messages.create(model=OPUS, max_tokens=16000,
        thinking={"type": "adaptive", "display": "summarized"}, messages=[{"role": "user", "content": GCD_Q}]))
    record("gcd_summarized", blocks=[b.type for b in r.content], thinking=thinking_of(r)[:1500], answer=text_of(r)[:600],
           usage=usage_of(r), seconds=s, note="thinking_live beat 1")
attempt("gcd_summarized", gcd_summarized)

def gcd_omitted():
    r, s = timed(lambda: client.messages.create(model=OPUS, max_tokens=16000,
        thinking={"type": "adaptive", "display": "omitted"}, messages=[{"role": "user", "content": GCD_Q}]))
    tb = [b for b in r.content if b.type == "thinking"]
    record("gcd_omitted", blocks=[b.type for b in r.content], thinking_field_len=len(thinking_of(r)),
           has_signature=bool(tb and getattr(tb[0], "signature", None)), answer=text_of(r)[:400], usage=usage_of(r), seconds=s,
           note="thinking_live beat 2: compare output tokens to summarized")
attempt("gcd_omitted", gcd_omitted)

def enabled_400():
    try:
        r = client.messages.create(model=OPUS, max_tokens=8000, thinking={"type": "enabled", "budget_tokens": 4000},
                                   messages=[{"role": "user", "content": GCD_Q}])
        record("enabled_400", result="ACCEPTED?!", usage=usage_of(r))
    except Exception as e:
        record("enabled_400", error=f"{type(e).__name__}: {str(e)[:500]}", note="thinking_live beat 3: expected 400 on Opus 5.5")
attempt("enabled_400", enabled_400)

def disabled_400():
    try:
        r = client.messages.create(model=OPUS, max_tokens=1000, thinking={"type": "disabled"},
                                   messages=[{"role": "user", "content": GCD_Q}])
        record("disabled_400", result="ACCEPTED?!", usage=usage_of(r))
    except Exception as e:
        record("disabled_400", error=f"{type(e).__name__}: {str(e)[:500]}", note="thinking_live beat 3")
attempt("disabled_400", disabled_400)

def haiku_adaptive_400():
    try:
        r = client.messages.create(model=HAIKU, max_tokens=4000, thinking={"type": "adaptive"},
                                   messages=[{"role": "user", "content": GCD_Q}])
        record("haiku_adaptive_400", result="ACCEPTED?!", usage=usage_of(r), blocks=[b.type for b in r.content])
    except Exception as e:
        record("haiku_adaptive_400", error=f"{type(e).__name__}: {str(e)[:500]}", note="thinking_live beat 4: expected 400 on Haiku 4.5")
attempt("haiku_adaptive_400", haiku_adaptive_400)

def haiku_enabled():
    r, s = timed(lambda: client.messages.create(model=HAIKU, max_tokens=4000, thinking={"type": "enabled", "budget_tokens": 2000},
                                                messages=[{"role": "user", "content": GCD_Q}]))
    record("haiku_enabled", blocks=[b.type for b in r.content], thinking=thinking_of(r)[:800], answer=text_of(r)[:400],
           usage=usage_of(r), seconds=s, note="thinking_live beat 4")
attempt("haiku_enabled", haiku_enabled)


# ---------------------------------------------------------------- 4.1 a question that needs thinking
# The GCD was too easy: 140 output tokens in every mode, thinking summary one line. Adaptive thinking decided
# not to think. This one has a trap (the obvious answer is wrong) so the meter should move.
HARD_Q = ("A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. Then the shop raises the "
          "ball's price by 50% and lowers the bat's by 10%. What is the new total, to the cent? Answer with the number only.")
def hard_run(name, **kw):
    r, s = timed(lambda: client.messages.create(model=OPUS, max_tokens=16000, messages=[{"role": "user", "content": HARD_Q}], **kw))
    record(name, blocks=[b.type for b in r.content], thinking=thinking_of(r)[:1200], answer=text_of(r)[:300],
           usage=usage_of(r), seconds=s, note="thinking_live / effort: a question that needs thinking (truth: ball 0.05 -> 0.075, bat 1.05 -> 0.945, total 1.02)")
attempt("hard_summarized", lambda: hard_run("hard_summarized", thinking={"type": "adaptive", "display": "summarized"}))
attempt("hard_omitted", lambda: hard_run("hard_omitted", thinking={"type": "adaptive", "display": "omitted"}))
attempt("hard_effort_low", lambda: hard_run("hard_effort_low", thinking={"type": "adaptive", "display": "omitted"}, output_config={"effort": "low"}))
attempt("hard_effort_high", lambda: hard_run("hard_effort_high", thinking={"type": "adaptive", "display": "omitted"}, output_config={"effort": "high"}))

# ---------------------------------------------------------------- 4.1 effort
def effort_run(level):
    r, s = timed(lambda: client.messages.create(model=OPUS, max_tokens=16000, output_config={"effort": level},
        thinking={"type": "adaptive", "display": "omitted"}, messages=[{"role": "user", "content": GCD_Q}]))
    record(f"effort_{level}", answer=text_of(r)[:300], usage=usage_of(r), seconds=s, note="effort beat 4")
attempt("effort_low", lambda: effort_run("low"))
attempt("effort_high", lambda: effort_run("high"))

# ---------------------------------------------------------------- 4.1 preserve thinking blocks
def get_weather(city: str) -> str:
    fake_db = {"paris": 18, "tokyo": 25, "new york": 12}
    t = fake_db.get(city.lower()); return f"{t} C" if t is not None else f"No data for {city}"
def celsius_to_fahrenheit(celsius: float) -> str:
    return f"{celsius * 9 / 5 + 32:.1f} F"
FUNCS = {"get_weather": get_weather, "celsius_to_fahrenheit": celsius_to_fahrenheit}
TOOLS = [
    {"name": "get_weather", "description": "Get the current temperature in Celsius for a city.",
     "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}},
    {"name": "celsius_to_fahrenheit", "description": "Convert a temperature from Celsius to Fahrenheit.",
     "input_schema": {"type": "object", "properties": {"celsius": {"type": "number"}}, "required": ["celsius"]}},
]
Q3 = "What's the weather in Paris, Tokyo and New York, in Fahrenheit?"
SYS_SHORT = "You are a weather assistant. Use tools for live data."

def run_tools(r):
    return [{"type": "tool_result", "tool_use_id": b.id, "content": FUNCS[b.name](**b.input)}
            for b in r.content if b.type == "tool_use"]

def preserve():
    base = [{"role": "user", "content": "What's the weather in Paris in Fahrenheit?"}]
    # First pass (no thinking param) returned blocks ['tool_use'] only -- no thinking block to drop, so the
    # "tidy" history was accepted. Ask for summarized thinking so the block is present; also use a question
    # that needs a decision between tools.
    TH = {"type": "adaptive", "display": "summarized"}
    r1 = client.messages.create(model=OPUS, max_tokens=4000, system=SYS_SHORT, tools=TOOLS, messages=base, thinking=TH)
    blocks1 = [b.type for b in r1.content]
    results = run_tools(r1)
    # tidy (wrong): drop the thinking block
    tidy = [b for b in r1.content if b.type in ("text", "tool_use")]
    try:
        r_bad = client.messages.create(model=OPUS, max_tokens=4000, system=SYS_SHORT, tools=TOOLS, thinking=TH,
                                       messages=base + [{"role": "assistant", "content": tidy}, {"role": "user", "content": results}])
        record("preserve_400", result="ACCEPTED?!", step1_blocks=blocks1, answer=text_of(r_bad)[:300])
    except Exception as e:
        record("preserve_400", step1_blocks=blocks1, error=f"{type(e).__name__}: {str(e)[:500]}", note="preserve beat 5: expected 400")
    # honest: content as-is, run to completion
    msgs = base + [{"role": "assistant", "content": r1.content}, {"role": "user", "content": results}]
    steps = 1
    while True:
        r = client.messages.create(model=OPUS, max_tokens=4000, system=SYS_SHORT, tools=TOOLS, messages=msgs, thinking=TH); steps += 1
        msgs.append({"role": "assistant", "content": r.content})
        if r.stop_reason != "tool_use":
            break
        msgs.append({"role": "user", "content": run_tools(r)})
    record("preserve_ok", steps=steps, answer=text_of(r)[:300], note="preserve beat 5")
attempt("preserve", preserve)


def preserve2():
    """Second attempt: a question that needs reasoning AFTER tool results (pick one of three). Walk the loop with
    summarized thinking; at the first step whose content holds a thinking block, build the tidy history (drop it)
    and send the tool results against it."""
    TH = {"type": "adaptive", "display": "summarized"}
    q = "Of Paris, Tokyo and New York, which is closest to 70 F right now? Convert only that one and tell me."
    msgs = [{"role": "user", "content": q}]
    per_step = []; broke = None; steps = 0
    while steps < 8:
        r = client.messages.create(model=OPUS, max_tokens=4000, system=SYS_SHORT, tools=TOOLS, messages=msgs, thinking=TH); steps += 1
        blocks = [b.type for b in r.content]; per_step.append(blocks)
        if r.stop_reason != "tool_use":
            break
        results = run_tools(r)
        if "thinking" in blocks and broke is None:
            tidy = [b for b in r.content if b.type != "thinking"]
            try:
                rb = client.messages.create(model=OPUS, max_tokens=4000, system=SYS_SHORT, tools=TOOLS, thinking=TH,
                                            messages=msgs + [{"role": "assistant", "content": tidy}, {"role": "user", "content": results}])
                broke = {"step": steps - 1, "result": "ACCEPTED?!", "blocks_back": [b.type for b in rb.content]}
            except Exception as e:
                broke = {"step": steps - 1, "error": f"{type(e).__name__}: {str(e)[:500]}"}
        msgs.append({"role": "assistant", "content": r.content}); msgs.append({"role": "user", "content": results})
    record("preserve2", per_step_blocks=per_step, thinking_summaries=[getattr(b, "thinking", "")[:300] for m in msgs if m["role"] == "assistant" for b in m["content"] if getattr(b, "type", "") == "thinking"],
           tidy_attempt=broke, steps=steps, answer=text_of(r)[:300], note="preserve beat 5, second attempt")
attempt("preserve2", preserve2)

# ---------------------------------------------------------------- 4.2 caching
def cache_short():
    """Two-tool prefix + one-line system: under the 512 minimum. Expect written 0, read 0 twice."""
    rows = []
    for q in (Q3, "And London?"):
        r = client.messages.create(model=OPUS, max_tokens=1500, cache_control={"type": "ephemeral"},
                                   system=SYS_SHORT, tools=TOOLS, messages=[{"role": "user", "content": q}])
        rows.append(usage_of(r))
    # prefix size: count tokens for the tools+system alone
    try:
        n = client.messages.count_tokens(model=OPUS, system=SYS_SHORT, tools=TOOLS, messages=[{"role": "user", "content": "x"}]).input_tokens
    except Exception as e:
        n = f"count_tokens failed: {type(e).__name__}"
    record("cache_short", calls=rows, prefix_tokens_approx=n, note="cache_live beat 1: silent no-cache under 512")
attempt("cache_short", cache_short)

def handbook_text():
    from pypdf import PdfReader
    pdf = HERE.parent.parent / "level-2b-beginner" / "test" / "assets" / "employee_handbook.pdf"   # repo layout
    return "\n".join(p.extract_text() for p in PdfReader(str(pdf)).pages)

def cache_handbook():
    hb = handbook_text()
    system = [{"type": "text", "text": "You answer questions about the Northwind Analytics employee handbook below. Quote the policy."},
              {"type": "text", "text": hb, "cache_control": {"type": "ephemeral"}}]
    rows = []
    for q in ("How many vacation days do new employees get?", "What is the equipment allowance?"):
        r, s = timed(lambda: client.messages.create(model=OPUS, max_tokens=800, system=system,
                                                     messages=[{"role": "user", "content": q}]))
        rows.append({"q": q, "usage": usage_of(r), "seconds": s, "answer": text_of(r)[:300]})
        time.sleep(1)
    record("cache_handbook", handbook_chars=len(hb), calls=rows, note="cache_live beat 2: write then read")
attempt("cache_handbook", cache_handbook)

BRIEFING = """You are a weather assistant for a travel company. Follow this briefing exactly.

UNITS. Report temperatures in the unit the user asks for. If the user names no unit, use Celsius for cities in Europe and Asia and Fahrenheit for cities in the United States. Always show one decimal place for Fahrenheit and whole degrees for Celsius. Never show both units unless asked.

TOOLS. Use get_weather for every temperature; never guess or recall a temperature from memory, even for well-known cities. Use celsius_to_fahrenheit for every conversion; never convert in your head. When the user asks about several cities, request all of them at once rather than one at a time. If get_weather reports no data for a city, say so plainly and do not substitute a nearby city.

FORMAT. For one city, answer in one sentence. For several cities, answer with one short line per city in the order the user named them, then one sentence of comparison if the user asked a comparative question (hottest, coldest, warmer than). Do not add packing advice, clothing suggestions or travel tips unless the user asks. Do not use emoji.

DECLINING. If the user asks for a forecast, historical weather, air quality, pollen, sunrise times or anything other than the current temperature, explain in one sentence that you only have current temperatures and offer that instead. If the user asks about a place that is not a city (a country, a continent, an ocean), ask which city they mean.

TONE. Plain, friendly, brief. No preamble such as "Great question". No closing offers such as "Let me know if you need anything else". Answer, then stop.

PRIVACY. Do not ask for or store the user's location. Do not infer where the user is from their question. If the user volunteers their location, you may use it for this answer only.

EXAMPLES. "Weather in Lyon?" -> "It's 14 degrees Celsius in Lyon right now." "Paris and Tokyo in Fahrenheit, which is warmer?" -> two lines, then "Tokyo is warmer by 12.6 degrees." "Will it rain in Oslo tomorrow?" -> "I only have current temperatures, not forecasts. Oslo is 6 degrees Celsius right now if that helps."
"""

def agent(question, system, cached, thinking=None, max_steps=8):
    kw = {"model": OPUS, "max_tokens": 8000, "system": system, "tools": TOOLS}
    if cached:
        kw["cache_control"] = {"type": "ephemeral"}
    if thinking:
        kw["thinking"] = thinking
    msgs = [{"role": "user", "content": question}]
    steps, trace, total = [], [], 0.0
    t0 = time.time()
    for i in range(max_steps):
        r = client.messages.create(messages=msgs, **kw)
        steps.append(usage_of(r)); total += cost(r.usage, cached=True)
        for b in r.content:
            if b.type == "thinking" and getattr(b, "thinking", ""):
                trace.append(f"[step {i}] THINK {b.thinking[:400]}")
            elif b.type == "tool_use":
                trace.append(f"[step {i}] {b.name}({json.dumps(b.input)})")
        msgs.append({"role": "assistant", "content": r.content})
        if r.stop_reason != "tool_use":
            break
        msgs.append({"role": "user", "content": run_tools(r)})
    uncached_cost = sum((s["input"] + s["cache_write"] + s["cache_read"]) * P_IN + s["output"] * P_OUT for s in steps)
    return {"steps": steps, "n_steps": len(steps), "trace": trace, "answer": text_of(r)[:500], "seconds": round(time.time() - t0, 1),
            "cost_usd": round(total, 5), "cost_if_uncached_usd": round(uncached_cost, 5),
            "tokens_in_total": sum(s["input"] + s["cache_write"] + s["cache_read"] for s in steps),
            "tokens_out_total": sum(s["output"] for s in steps)}

def cache_loop():
    record("cache_loop", **agent(Q3, BRIEFING, cached=True), note="cache_live beats 3-4: moving breakpoint across the loop")
attempt("cache_loop", cache_loop)

def cache_loop_uncached():
    record("cache_loop_uncached", **agent(Q3, BRIEFING, cached=False), note="cache_live beat 4: the control run, no cache_control")
attempt("cache_loop_uncached", cache_loop_uncached)

def cache_timestamp():
    hb = handbook_text()
    rows = {}
    # wrong: timestamp at the TOP of the system prompt, breakpoint at the end
    bad = []
    for q in ("How many vacation days?", "What is the equipment allowance?"):
        system = [{"type": "text", "text": f"Current time: {time.strftime('%Y-%m-%d %H:%M:%S')}. You answer questions about the handbook below."},
                  {"type": "text", "text": hb, "cache_control": {"type": "ephemeral"}}]
        r = client.messages.create(model=OPUS, max_tokens=400, system=system, messages=[{"role": "user", "content": q}])
        bad.append(usage_of(r)); time.sleep(1.2)
    rows["timestamp_on_top"] = bad
    # right: timestamp AFTER the breakpoint (in the user message)
    good = []
    for q in ("How many vacation days?", "What is the equipment allowance?"):
        system = [{"type": "text", "text": "You answer questions about the handbook below."},
                  {"type": "text", "text": hb, "cache_control": {"type": "ephemeral"}}]
        r = client.messages.create(model=OPUS, max_tokens=400, system=system,
                                   messages=[{"role": "user", "content": f"{q} (asked at {time.strftime('%H:%M:%S')})"}])
        good.append(usage_of(r)); time.sleep(1.2)
    rows["timestamp_below_clip"] = good
    record("cache_timestamp", **rows, note="cache_breaks beat 3")
attempt("cache_timestamp", cache_timestamp)

# ---------------------------------------------------------------- the build: thinking + caching agent
def build():
    res = agent(Q3, BRIEFING, cached=True, thinking={"type": "adaptive", "display": "summarized"})
    record("build", **res, note="build_run: summarized thinking + top-level cache_control, per-step receipts")
attempt("build", build)

json.dump(out, open(HERE / "results.json", "w"), indent=1, default=str, ensure_ascii=False)
errs = [k for k, v in out.items() if "error" in v and "400" not in k]
print(f"\nwrote {HERE / 'results.json'} with {len(out)} runs; unexpected errors: {errs}")
