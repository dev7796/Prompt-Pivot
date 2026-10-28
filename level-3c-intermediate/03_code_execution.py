"""Level 3c, section 3.10: code execution, a sandbox you don't run.

    python 03_code_execution.py            # mean and SD of 1..10, tool off then tool on
    python 03_code_execution.py --chart    # upload sales.csv, ask for a bar chart, download it

The honest finding from the real run: with code_execution switched ON, Claude never called it for the
docs' own example. It did the arithmetic in its head, correctly (mean 5.500, SD 2.872 population,
and it said which). Server tools are still Claude's choice. Turn one on and you have offered it, not
forced it.

Needs the Anthropic API directly (not available on Bedrock). The chart demo also needs the Files
API, which is Claude-API-only.
"""
import pathlib
import sys
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-opus-5-5"
CODE_EXEC = {"type": "code_execution_20250825", "name": "code_execution"}

HERE = pathlib.Path(__file__).resolve().parent
STATS_Q = ("Compute the mean and standard deviation of the integers 1..10. Give both numbers to three "
           "decimals and say whether the standard deviation is population or sample.")


def text_of(r):
    return "".join(b.text for b in r.content if b.type == "text")


if "--chart" in sys.argv:
    # Files API round trip. The container_upload block puts the file inside the sandbox; the chart
    # Claude saves comes back as a file_id you download. NOTE: this is client.beta.messages.create
    # with the two beta headers -- the plain client.messages.create does not accept `betas=`.
    # (That was the bug in the first harness, caught by the SDK before any request was sent.)
    csv_path = HERE / "test" / "sales.csv"
    up = client.beta.files.upload(file=open(csv_path, "rb"))
    r = client.beta.messages.create(
        model=MODEL, max_tokens=4096, tools=[CODE_EXEC],
        betas=["code-execution-2025-08-25", "files-api-2025-04-14"],
        messages=[{"role": "user", "content": [
            {"type": "container_upload", "file_id": up.id},
            {"type": "text", "text": "Read sales.csv. List the top 3 rows by revenue, then save a bar chart "
                                     "of revenue by product as chart.png."}]}])
    print("blocks:", [b.type for b in r.content])
    print(text_of(r))
    for b in r.content:
        d = b.model_dump()
        inner = d.get("content") if isinstance(d.get("content"), dict) else {}
        for item in inner.get("content", []) or []:
            if item.get("file_id"):
                data = client.beta.files.download(item["file_id"], betas=["files-api-2025-04-14"])
                out = HERE / "chart_from_claude.png"
                out.write_bytes(data.read())
                print("saved", out)
    sys.exit()

print("--- no tools ---")
r = client.messages.create(model=MODEL, max_tokens=512, messages=[{"role": "user", "content": STATS_Q}])
print(text_of(r))

print("\n--- code_execution ON ---")
r = client.messages.create(model=MODEL, max_tokens=4096, tools=[CODE_EXEC],
                           messages=[{"role": "user", "content": STATS_Q}])
print("blocks:", [b.type for b in r.content])
for b in r.content:
    if b.type == "server_tool_use":                   # only present if Claude chose to run code
        print("code:", b.input.get("code"))
    elif "result" in b.type:
        print("stdout:", b.model_dump())
print(text_of(r))

# Truth, from Python's statistics module: mean 5.5; pstdev 2.872; stdev 3.028.
# Real run (test/results.json): both calls returned the same correct numbers; the second had blocks
# ['thinking', 'text'] -- the tool was never invoked. 4.5 s and 4.4 s.
# Code execution is free when paired with web_search_20260209 / web_fetch_20260209 or later in the
# same request; with the 2025 tool versions pinned here it is billed per session after a free daily
# allowance.
