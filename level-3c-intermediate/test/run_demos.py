"""Real runs for Level 3c demos. Writes test/results.json.

Server tools (web_search, web_fetch, code_execution) may not be available on Bedrock. The harness
probes Bedrock first; if the probe fails it falls back to the direct Anthropic API (ANTHROPIC_API_KEY)
and records which backend served each run so the script can say so on camera.

  AWS_CONFIG_FILE=$HOME/.aws/config AWS_SHARED_CREDENTIALS_FILE=$HOME/.aws/credentials \\
  uv run --quiet --with anthropic --with boto3 python3 test/run_demos.py

Every run is wrapped so one failure does not stop the rest. Each writes a 'backend' field.
"""
import json, os, sys, time, traceback, pathlib, csv, io
import anthropic

HERE = pathlib.Path(__file__).resolve().parent
# --only a,b,c  re-runs just those demos and merges into the existing results.json (keeps cost down
# when one run needs a fix). Without it, every demo runs and results.json is rewritten.
ONLY = set()
if "--only" in sys.argv:
    ONLY = set(sys.argv[sys.argv.index("--only") + 1].split(","))
out = json.load(open(HERE / "results.json")) if (ONLY and (HERE / "results.json").exists()) else {}

BEDROCK = anthropic.AnthropicBedrock(aws_region="us-east-1", aws_profile="alps-optum", max_retries=3)
BEDROCK_MODEL = "us.anthropic.claude-opus-5-5"
def _direct_key():
    """ANTHROPIC_API_KEY from the environment, else from ~/.anthropic_api_key (one line, chmod 600).
    The file lives in $HOME, outside every repo, so it can never be committed. The key is only ever
    handed to the SDK; nothing here prints or logs it."""
    k = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if k:
        return k
    f = pathlib.Path.home() / ".anthropic_api_key"
    if f.is_file():
        return f.read_text().strip()
    return ""


_KEY = _direct_key()
DIRECT = anthropic.Anthropic(api_key=_KEY) if _KEY else None
DIRECT_MODEL = "claude-opus-5-5"

WEB_SEARCH = {"type": "web_search_20250305", "name": "web_search", "max_uses": 5}
WEB_FETCH = {"type": "web_fetch_20250910", "name": "web_fetch", "max_uses": 5, "citations": {"enabled": True}}
CODE_EXEC = {"type": "code_execution_20250825", "name": "code_execution"}


def record(name, **kw):
    out[name] = kw
    print(f"\n=== {name} ===")
    for k, v in kw.items():
        print(f"{k}: {v if isinstance(v, str) else json.dumps(v, default=str, ensure_ascii=False)[:1500]}")


def attempt(name, fn):
    if ONLY and name not in ONLY and name != "backend_probe":
        return
    try:
        fn()
    except Exception as e:
        record(name, error=f"{type(e).__name__}: {e}"[:600], trace=traceback.format_exc()[-500:])


def text_of(r):
    return "".join(getattr(b, "text", "") for b in r.content if b.type == "text")


def blocks_of(r):
    return [b.type for b in r.content]


def citations_of(r):
    urls = []
    for b in r.content:
        if b.type == "text":
            for c in (getattr(b, "citations", None) or []):
                u = getattr(c, "url", None) or getattr(c, "document_title", None)
                if u:
                    urls.append(u)
    return urls


# ---------------------------------------------------------------- backend probe
def probe():
    res = {}
    for tool in (WEB_SEARCH, WEB_FETCH, CODE_EXEC):
        try:
            r = BEDROCK.messages.create(model=BEDROCK_MODEL, max_tokens=200, tools=[tool],
                                        messages=[{"role": "user", "content": "Say OK."}])
            res[tool["type"]] = f"bedrock OK ({r.stop_reason})"
        except Exception as e:
            res[tool["type"]] = f"bedrock FAIL: {type(e).__name__}: {str(e)[:160]}"
    record("backend_probe", results=res, direct_available=DIRECT is not None,
           note="server_intro: which backend serves server tools")
    return all("OK" in v for v in res.values())
attempt("backend_probe", lambda: None)
BEDROCK_OK = False
try:
    BEDROCK_OK = probe()
except Exception as e:
    record("backend_probe", error=str(e)[:400])

if BEDROCK_OK:
    client, MODEL, BACKEND = BEDROCK, BEDROCK_MODEL, "bedrock"
elif DIRECT:
    client, MODEL, BACKEND = DIRECT, DIRECT_MODEL, "direct"
else:
    record("no_backend", error="Bedrock refused server tools and no Anthropic key was found. Export ANTHROPIC_API_KEY or write the key (one line) to ~/.anthropic_api_key with chmod 600, then re-run.")
    json.dump(out, open(HERE / "results.json", "w"), indent=1, default=str, ensure_ascii=False)
    raise SystemExit(1)
print(f"\n>>> using backend: {BACKEND}")


def create(**kw):
    t0 = time.time()
    r = client.messages.create(model=MODEL, **kw)
    return r, round(time.time() - t0, 1)


# ---------------------------------------------------------------- 3.10 web search
def search_run():
    # Keep ONE tools list for every turn of this conversation. On the 2026-10-26 run, turn 2 used a tools
    # list without allowed_domains and the API refused with 400 "Invalid `signature` in `thinking` block ...
    # The `tools` list differs from the one this block was created with" -- Opus 5.5 returns a signed
    # thinking block, and the signature covers the tools list. That 400 is now a beat in search_live.
    tools = [{**WEB_SEARCH, "allowed_domains": ["anthropic.com", "claude.com"]}]
    r, secs = create(max_tokens=2048, tools=tools,
                     messages=[{"role": "user", "content": "What did Anthropic announce this week?"}])
    searches = sum(1 for b in r.content if b.type == "server_tool_use")
    record("web_search", backend=BACKEND, stop_reason=r.stop_reason, blocks=blocks_of(r), searches=searches,
           text=text_of(r)[:1500], citations=citations_of(r)[:10], usage=dict(r.usage), seconds=secs,
           note="search_live")
    # multi-turn: send assistant content back unchanged, then with encrypted_content stripped
    msgs = [{"role": "user", "content": "What did Anthropic announce this week?"},
            {"role": "assistant", "content": r.content},
            {"role": "user", "content": "Which of those matters most for developers? One sentence."}]
    r2, _ = create(max_tokens=512, tools=tools, messages=msgs)
    record("web_search_turn2_unchanged", backend=BACKEND, stop_reason=r2.stop_reason, text=text_of(r2)[:500])
    stripped = []
    for b in r.content:
        d = b.model_dump()
        if d.get("type") == "web_search_tool_result" and isinstance(d.get("content"), list):
            for item in d["content"]:
                item.pop("encrypted_content", None)
        stripped.append(d)
    try:
        r3, _ = create(max_tokens=256, tools=tools, messages=[msgs[0], {"role": "assistant", "content": stripped}, msgs[2]])
        record("web_search_turn2_stripped", backend=BACKEND, result="accepted?!", stop_reason=r3.stop_reason)
    except Exception as e:
        record("web_search_turn2_stripped", backend=BACKEND, error=f"{type(e).__name__}: {str(e)[:400]}",
               note="search_live: expected 400 when encrypted_content is removed")
attempt("web_search", search_run)

# ---------------------------------------------------------------- 3.10 web fetch
DOCS_URL = "https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview"

def fetch_with_url():
    r, secs = create(max_tokens=2048, tools=[WEB_FETCH],
                     messages=[{"role": "user", "content": f"Fetch {DOCS_URL} and summarize it in three sentences."}])
    record("web_fetch_with_url", backend=BACKEND, stop_reason=r.stop_reason, blocks=blocks_of(r),
           text=text_of(r)[:1200], citations=citations_of(r)[:6], seconds=secs, note="fetch_live run 1")
attempt("web_fetch_with_url", fetch_with_url)

def fetch_without_url():
    r, secs = create(max_tokens=1024, tools=[WEB_FETCH],
                     messages=[{"role": "user", "content": "Fetch the Anthropic tool use overview page and summarize it in three sentences."}])
    record("web_fetch_without_url", backend=BACKEND, stop_reason=r.stop_reason, blocks=blocks_of(r),
           text=text_of(r)[:1200], seconds=secs, note="fetch_live run 2: URL not in conversation")
attempt("web_fetch_without_url", fetch_without_url)

def search_then_fetch_pdf():
    r, secs = create(max_tokens=4096, tools=[WEB_SEARCH, WEB_FETCH],
                     messages=[{"role": "user", "content": "Find Anthropic's 'Building effective agents' article, fetch it, and tell me the two core patterns it names. Cite the page."}])
    record("search_then_fetch", backend=BACKEND, stop_reason=r.stop_reason, blocks=blocks_of(r),
           text=text_of(r)[:1200], citations=citations_of(r)[:6], seconds=secs, note="fetch_live run 3: search -> fetch chain")
attempt("search_then_fetch", search_then_fetch_pdf)

# ---------------------------------------------------------------- 3.10 code execution
STATS_Q = "Compute the mean and standard deviation of the integers 1..10. Give both numbers to three decimals and say whether the standard deviation is population or sample."

def stats_no_tools():
    r, secs = create(max_tokens=512, messages=[{"role": "user", "content": STATS_Q}])
    record("stats_no_tools", backend=BACKEND, text=text_of(r)[:800], seconds=secs,
           note="code_live beat 1 (truth: mean 5.5, pop sd 2.872, sample sd 3.028)")
attempt("stats_no_tools", stats_no_tools)

def stats_code_exec():
    r, secs = create(max_tokens=4096, tools=[CODE_EXEC], messages=[{"role": "user", "content": STATS_Q}])
    code = [b.model_dump().get("input") for b in r.content if b.type == "server_tool_use"]
    results = [b.model_dump() for b in r.content if "result" in b.type]
    record("stats_code_exec", backend=BACKEND, stop_reason=r.stop_reason, blocks=blocks_of(r), code=code,
           tool_results=json.dumps(results, default=str)[:1200], text=text_of(r)[:800], seconds=secs,
           container=getattr(getattr(r, "container", None), "id", None), note="code_live beat 2")
attempt("stats_code_exec", stats_code_exec)

def csv_chart():
    rows = [["product", "region", "revenue"], ["Widget", "NA", 12000], ["Gadget", "EU", 18500], ["Gizmo", "APAC", 9100],
            ["Doohickey", "NA", 22000], ["Thingamajig", "EU", 7600]]
    buf = io.StringIO(); csv.writer(buf).writerows(rows)
    csv_path = HERE / "sales.csv"; csv_path.write_text(buf.getvalue())
    if BACKEND != "direct":
        record("csv_chart", skipped="Files API is Claude-API-only; needs the direct backend", note="code_live beats 4-5")
        return
    up = client.beta.files.upload(file=open(csv_path, "rb"))
    t0 = time.time()
    r = client.beta.messages.create(model=MODEL, max_tokens=4096, tools=[CODE_EXEC],
                     messages=[{"role": "user", "content": [
                         {"type": "container_upload", "file_id": up.id},
                         {"type": "text", "text": "Read sales.csv. List the top 3 rows by revenue, then save a bar chart of revenue by product as chart.png."}]}],
                     betas=["code-execution-2025-08-25", "files-api-2025-04-14"])
    secs = round(time.time() - t0, 1)
    file_ids = []
    for b in r.content:
        d = b.model_dump()
        for item in (d.get("content") or {}).get("content", []) if isinstance(d.get("content"), dict) else []:
            if item.get("file_id"):
                file_ids.append(item["file_id"])
    record("csv_chart", backend=BACKEND, stop_reason=r.stop_reason, blocks=blocks_of(r), text=text_of(r)[:800],
           file_ids=file_ids, seconds=secs, note="code_live beats 4-5")
    for fid in file_ids[:1]:
        data = client.beta.files.download(fid, betas=["files-api-2025-04-14"])
        (HERE / "chart_from_claude.png").write_bytes(data.read())
        record("csv_chart_download", saved=str(HERE / "chart_from_claude.png"))
attempt("csv_chart", csv_chart)

# ---------------------------------------------------------------- 3.11 before/after mini-eval
BEFORE_TOOLS = [
    {"name": "get_current_weather", "description": "Gets current weather.", "input_schema": {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}},
    {"name": "get_forecast", "description": "Gets forecast.", "input_schema": {"type": "object", "properties": {"q": {"type": "string"}, "days": {"type": "integer"}}, "required": ["q"]}},
    {"name": "get_weather_by_coordinates", "description": "Gets weather by lat/lon.", "input_schema": {"type": "object", "properties": {"lat": {"type": "number"}, "lon": {"type": "number"}}, "required": ["lat", "lon"]}},
]
AFTER_TOOLS = [{
    "name": "weather",
    "description": ("Get the weather for a location. Use mode 'current' for right now and 'forecast' for the next days. "
                    "Returns temperature, condition, wind and a human-readable time; use detail='full' only when the user asks for more. "
                    "Does not return historical data."),
    "input_schema": {"type": "object", "properties": {
        "location": {"type": "string", "description": "City and country, e.g. 'Lyon, France' or 'Austin, United States'. Coordinates as 'lat,lon' also accepted."},
        "mode": {"type": "string", "enum": ["current", "forecast"]},
        "detail": {"type": "string", "enum": ["concise", "full"], "description": "Default concise."},
    }, "required": ["location", "mode"]},
}]
EVAL_QS = ["Is it raining in Lyon right now?", "What's the weather at 48.85, 2.35?", "Will I need a coat in Austin this weekend?",
           "Give me everything you can about current conditions in Tokyo.", "Weather in Paris?"]

def mini_eval():
    rows = []
    for q in EVAL_QS:
        for label, tools in (("before", BEFORE_TOOLS), ("after", AFTER_TOOLS)):
            r, secs = create(max_tokens=512, tools=tools, messages=[{"role": "user", "content": q}])
            tus = [{"name": b.name, "input": b.input} for b in r.content if b.type == "tool_use"]
            rows.append({"q": q, "set": label, "tool_uses": tus, "output_tokens": r.usage.output_tokens, "stop": r.stop_reason})
    record("design_eval", backend=BACKEND, rows=rows, note="design_example: compare tool picks and output tokens")
attempt("design_eval", mini_eval)

# ---------------------------------------------------------------- 3.12 the research assistant
NOTES = HERE / "research_notes.md"
if NOTES.exists():
    NOTES.unlink()

def save_note(title: str, body: str) -> str:
    with NOTES.open("a") as f:
        f.write(f"## {title}\n\n{body}\n\n")
    return f"Saved note '{title}'."

RESEARCH_TOOLS = [
    {"type": "web_search_20250305", "name": "web_search", "max_uses": 8},
    {"name": "save_note",
     "description": ("Save a finding to the user's research notes file. Call this once per distinct finding, "
                     "with a short title and a body that includes the source URL. Returns a confirmation string."),
     "input_schema": {"type": "object", "properties": {
         "title": {"type": "string", "description": "3-8 word title"},
         "body": {"type": "string", "description": "Finding plus source URL"}}, "required": ["title", "body"]}},
]

def research(topic, max_steps=15):
    messages = [{"role": "user", "content": f"Research this and save notes: {topic}"}]
    tin = tout = 0; trace = []; per_step_in = []; pauses = 0; t0 = time.time()
    for step in range(max_steps):
        r = client.messages.create(model=MODEL, max_tokens=4096, system="You are a careful researcher. Cite sources in every note.",
                                   tools=RESEARCH_TOOLS, messages=messages)
        tin += r.usage.input_tokens; tout += r.usage.output_tokens; per_step_in.append(r.usage.input_tokens)
        messages.append({"role": "assistant", "content": r.content})
        for b in r.content:
            if b.type == "server_tool_use":
                trace.append(f"[step {step}] SEARCH {json.dumps(b.input)}")
            elif b.type == "tool_use":
                trace.append(f"[step {step}] save_note({b.input.get('title')!r})")
        if r.stop_reason == "pause_turn":
            pauses += 1; trace.append(f"[step {step}] pause_turn -> continue"); continue
        if r.stop_reason != "tool_use":
            return trace, text_of(r), {"tokens_in": tin, "tokens_out": tout, "per_step_in": per_step_in, "pauses": pauses,
                                       "steps": step + 1, "seconds": round(time.time() - t0, 1)}
        results = [{"type": "tool_result", "tool_use_id": b.id, "content": save_note(**b.input)}
                   for b in r.content if b.type == "tool_use" and b.name == "save_note"]
        messages.append({"role": "user", "content": results})
    return trace, "Stopped at max_steps.", {"tokens_in": tin, "tokens_out": tout, "per_step_in": per_step_in, "pauses": pauses, "steps": max_steps}

def research_run():
    trace, ans, stats = research("What is the Model Context Protocol and who supports it?")
    notes = NOTES.read_text() if NOTES.exists() else ""
    titles = [l[3:] for l in notes.splitlines() if l.startswith("## ")]
    with_url = sum(1 for sec in notes.split("## ")[1:] if "http" in sec)
    record("research", backend=BACKEND, trace=trace, answer=ans[:1500], stats=stats, notes_count=len(titles),
           notes_titles=titles, notes_with_url=with_url, notes_preview=notes[:1500], note="hook + build_run + build_trace")
attempt("research", research_run)

json.dump(out, open(HERE / "results.json", "w"), indent=1, default=str, ensure_ascii=False)
errs = [k for k, v in out.items() if "error" in v]
print(f"\nwrote {HERE / 'results.json'} with {len(out)} runs on backend={BACKEND}; errored: {errs}")
