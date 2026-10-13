"""Run the two triage bots from the Video 2 script over the 200-message set and report:
  parseable  = output is exactly one of the three labels (what code can `==` on)
  accuracy   = label matches ground truth (among all 200; unparseable counts as wrong)
Uses the same prompts as level2a-movie/script/code_samples.md, via Bedrock (AnthropicBedrock).
Outputs: test/results_v1.jsonl, test/results_v2.jsonl, test/summary.json"""
import json, sys, time, re
from enum import Enum
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel
import anthropic

MODEL = "us.anthropic.claude-opus-5-5"
# The video ran this through Bedrock. With a direct API key, use anthropic.Anthropic() and model="claude-opus-5-5".
client = anthropic.AnthropicBedrock(aws_region="us-east-1", max_retries=6)
data = json.load(open("test/messages_200.json"))
LABELS = {"BILLING", "BUG", "OTHER"}

# ---------------- v1: the naive bot (01_triage_v1_naive.py)
def triage_v1(message: str) -> str:
    prompt = f"What category is this support message?\n\n{message}"
    r = client.messages.create(model=MODEL, max_tokens=200, messages=[{"role": "user", "content": prompt}])
    # NOTE: the video's v1 uses r.content[0].text. On Opus 5.5 content[0] is a ThinkingBlock, so that
    # line raised AttributeError on all 200 messages (saved as results_v1_content0_crash.jsonl).
    # Here we apply the Level 1 golden rule so we can measure the *shape* of the text answers too.
    return "".join(b.text for b in r.content if b.type == "text")

# ---------------- v2: examples + structured output (06_triage_v2_structured.py)
class Category(str, Enum):
    BILLING = "BILLING"; BUG = "BUG"; OTHER = "OTHER"

class TriageResult(BaseModel):
    category: Category
    reason: str

SYSTEM = """Classify each support message as BILLING, BUG or OTHER.

<examples>
<example><message>I was charged twice this month.</message><label>BILLING</label></example>
<example><message>The export button crashes the app.</message><label>BUG</label></example>
<example><message>Do you have an office in Berlin?</message><label>OTHER</label></example>
</examples>"""

def triage_v2(message: str):
    r = client.messages.parse(model=MODEL, max_tokens=200, system=SYSTEM,
                              messages=[{"role": "user", "content": f"<message>{message}</message>"}],
                              output_format=TriageResult)
    if r.stop_reason != "end_turn":
        return None, r.stop_reason
    return r.parsed_output, r.stop_reason

def parse_v1(text: str):
    """Strict: is the whole output exactly a label (ignoring surrounding whitespace)? That's the
    standard code would need for `if label == 'BILLING'`. Also record a lenient read for context."""
    t = text.strip()
    strict = t.upper() if t.upper() in LABELS else None
    found = [l for l in LABELS if re.search(rf"\b{l}\b", t, re.I)]
    lenient = found[0] if len(found) == 1 else None
    return strict, lenient

def run_v1(d):
    for attempt in range(4):
        try:
            out = triage_v1(d["message"]); strict, lenient = parse_v1(out)
            return {**d, "output": out, "strict": strict, "lenient": lenient}
        except Exception as e:
            time.sleep(2 * (attempt + 1)); err = str(e)
    return {**d, "output": None, "strict": None, "lenient": None, "error": err}

def run_v2(d):
    for attempt in range(4):
        try:
            res, stop = triage_v2(d["message"])
            return {**d, "output": res.model_dump() if res else None, "strict": res.category.value if res else None, "stop_reason": stop}
        except Exception as e:
            time.sleep(2 * (attempt + 1)); err = str(e)
    return {**d, "output": None, "strict": None, "error": err}

def summarize(rows, key="strict"):
    parse = sum(1 for r in rows if r.get(key) is not None)
    acc = sum(1 for r in rows if r.get(key) == r["label"])
    return {"n": len(rows), "parseable": parse, "accurate": acc}

if __name__ == "__main__":
    which = sys.argv[1:] or ["v1", "v2"]
    summary = {}
    for v in which:
        fn = run_v1 if v == "v1" else run_v2
        t0 = time.time()
        with ThreadPoolExecutor(6) as ex:
            rows = list(ex.map(fn, data))
        with open(f"test/results_{v}.jsonl", "w") as f:
            for r in rows: f.write(json.dumps(r) + "\n")
        s = summarize(rows)
        if v == "v1": s["lenient_parseable"] = summarize(rows, "lenient")["parseable"]; s["lenient_accurate"] = summarize(rows, "lenient")["accurate"]
        s["errors"] = sum(1 for r in rows if r.get("error")); s["seconds"] = round(time.time() - t0)
        summary[v] = s
        print(v, s, flush=True)
    json.dump({"model": MODEL, **summary}, open("test/summary.json", "w"), indent=1)
