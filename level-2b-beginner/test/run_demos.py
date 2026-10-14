"""Real runs for Level 2b demos, via Bedrock (AnthropicBedrock). Writes test/results.json.

Bedrock supports images, PDFs and citations. The Files API is Claude-API-only, so the
Files demo in the video shows the code as written; its output comes from the base64
variant below (same request minus the upload), which the video says on camera.
"""
import base64, json, sys, time
import anthropic

client = anthropic.AnthropicBedrock(aws_region="us-east-1", aws_profile="alps-optum", max_retries=6)
MODEL = "us.anthropic.claude-opus-5-5"
A = "test/assets/"
out = {}

def b64(path):
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode()

def text_of(resp):
    return "".join(b.text for b in resp.content if b.type == "text")

def run(name, **kw):
    t0 = time.time()
    r = client.messages.create(model=MODEL, **kw)
    dt = time.time() - t0
    out[name] = {"seconds": round(dt, 1), "stop_reason": r.stop_reason, "usage": r.usage.model_dump(),
                 "text": text_of(r), "content": [b.model_dump() for b in r.content]}
    print(f"\n=== {name} ({dt:.1f}s, {r.usage.input_tokens} in / {r.usage.output_tokens} out) ===\n{text_of(r)}")
    return r

# 1. single chart (scene 3)
run("chart_trend", max_tokens=300, messages=[{"role": "user", "content": [
    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64(A + "chart.png")}},
    {"type": "text", "text": "What trend does this chart show? Two sentences."}]}])

# 2. two labeled charts (scene 5)
run("chart_compare", max_tokens=400, messages=[{"role": "user", "content": [
    {"type": "text", "text": "Image 1: Q3"},
    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64(A + "chart_q3.png")}},
    {"type": "text", "text": "Image 2: Q4"},
    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64(A + "chart_q4.png")}},
    {"type": "text", "text": "Which region grew the most from Image 1 to Image 2, and by roughly how much? Say where you read each number."}]}])

# 3. PDF with table (scene 8)
run("pdf_findings", max_tokens=600, messages=[{"role": "user", "content": [
    {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": b64(A + "quarterly_report.pdf")}},
    {"type": "text", "text": "List the three key findings, then tell me which quarter had the highest operating margin and what it was."}]}])

# 4. citations on plain text (scene 11)
run("cite_text", max_tokens=300, messages=[{"role": "user", "content": [
    {"type": "document", "source": {"type": "text", "media_type": "text/plain", "data": "The grass is green. The sky is blue."},
     "title": "Nature facts", "context": "A trustworthy reference document.", "citations": {"enabled": True}},
    {"type": "text", "text": "What color is the grass?"}]}])

# 5. citations on the PDF (scene 12)
run("cite_pdf", max_tokens=400, messages=[{"role": "user", "content": [
    {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": b64(A + "quarterly_report.pdf")},
     "title": "Q4 2026 report", "citations": {"enabled": True}},
    {"type": "text", "text": "What was the operating margin in Q4?"}]}])

# 6. the build: handbook Q&A with the permission sentence (scene 22)
SYSTEM_OK = "Answer only from the provided document. If the document does not contain the answer, say so."
SYSTEM_BAD = "Answer questions about the document."
def ask(name, system, question):
    r = run(name, max_tokens=600, system=system, messages=[{"role": "user", "content": [
        {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": b64(A + "employee_handbook.pdf")},
         "citations": {"enabled": True}},
        {"type": "text", "text": question}]}])
    # the exact output the video's loop prints
    line = ""
    for b in r.content:
        if b.type != "text":
            continue
        line += b.text
        for c in (b.citations or []):
            line += f" [p.{c.start_page_number}]"
    out[name]["printed"] = line
    print("PRINTED:", line)

ask("hb_vacation_ok", SYSTEM_OK, "How many vacation days do new employees get?")
ask("hb_stipend_ok", SYSTEM_OK, "Is there a remote-work stipend?")
# 7. break it (scene 23)
ask("hb_stipend_bad", SYSTEM_BAD, "Is there a remote-work stipend? How much is it?")

json.dump(out, open("test/results.json", "w"), indent=2, default=str)
print("\nwrote test/results.json")
