"""Level 4a, section 4.2: prompt caching. Pay once for the part that repeats.

    python 04_caching.py                 # the handbook: call 1 writes, call 2 reads (explicit breakpoint)
    python 04_caching.py --short         # the silent miss: a prefix under 512 tokens caches nothing
    python 04_caching.py --timestamp     # the trap: a timestamp ABOVE the clip rewrites the cache every call
    python 04_caching.py --auto          # the one-line version: top-level cache_control, let the API place it

The request has an order: tools, then system, then messages. Caching stores a prefix of that and reuses
it on later requests. Two ways to ask for it:

    cache_control={"type": "ephemeral"}        # top level: one line, automatic breakpoints
    {"type": "text", "text": ..., "cache_control": {"type": "ephemeral"}}   # explicit: a clip on a block

The receipt is three numbers on response.usage:
    cache_creation_input_tokens   written this call, 1.25x base price
    cache_read_input_tokens       read back from a previous call, 0.1x on most models, 0.05x on Opus 5.5
    input_tokens                  everything after the clip, full price
Both cache fields zero means nothing was cached. The usual reason: prefix under the minimum (512 on
Opus 5.5, 1,024 / 2,048 on some other models). Lifetime: five minutes, refreshed on every hit.

The handbook is the Level 2b asset; this script extracts its text with pypdf (pip install pypdf).
"""
import sys
import time
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-opus-5-5"


def receipt(label, response):
    u = response.usage
    print(f"{label:<34} written: {u.cache_creation_input_tokens:>5}  read: {u.cache_read_input_tokens:>5}  "
          f"uncached: {u.input_tokens:>4}")


def handbook_text():
    from pypdf import PdfReader
    pdf = "../level-2b-beginner/test/assets/employee_handbook.pdf"
    return "\n".join(p.extract_text() for p in PdfReader(pdf).pages)


def handbook():
    """The on-screen explicit breakpoint: a clip on the big block at the end of system."""
    system = [
        {"type": "text", "text": "You answer questions about the Northwind Analytics employee handbook below. Quote the policy."},
        {"type": "text", "text": handbook_text(),
         "cache_control": {"type": "ephemeral"}},
    ]
    for q in ("How many vacation days do new employees get?", "What is the equipment allowance?"):
        t0 = time.time()
        response = client.messages.create(model=MODEL, max_tokens=800, system=system,
                                          messages=[{"role": "user", "content": q}])
        receipt(f"{q[:30]}... {time.time() - t0:.1f}s", response)
        time.sleep(1)


def short():
    """Two small tools and a one-line system prompt: about 490 tokens. 22 short of 512. Nothing caches, no error."""
    tools = [
        {"name": "get_weather", "description": "Get the current temperature in Celsius for a city.",
         "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}},
        {"name": "celsius_to_fahrenheit", "description": "Convert a temperature from Celsius to Fahrenheit.",
         "input_schema": {"type": "object", "properties": {"celsius": {"type": "number"}}, "required": ["celsius"]}},
    ]
    for q in ("What's the weather in Paris, Tokyo and New York, in Fahrenheit?", "And London?"):
        response = client.messages.create(model=MODEL, max_tokens=1500, cache_control={"type": "ephemeral"},
                                          system="You are a weather assistant. Use tools for live data.",
                                          tools=tools, messages=[{"role": "user", "content": q}])
        receipt(q[:34], response)


def timestamp():
    """Anything above the clip that changes between calls rewrites the prefix. Put changing text BELOW the clip."""
    hb = handbook_text()
    print("timestamp on top (inside the prefix):")
    for q in ("How many vacation days?", "What is the equipment allowance?"):
        system = [{"type": "text", "text": f"Current time: {time.strftime('%Y-%m-%d %H:%M:%S')}. You answer questions about the handbook below."},
                  {"type": "text", "text": hb, "cache_control": {"type": "ephemeral"}}]
        receipt(f"  {q}", client.messages.create(model=MODEL, max_tokens=400, system=system,
                                                 messages=[{"role": "user", "content": q}]))
        time.sleep(1.2)
    print("timestamp below the clip (in the user message):")
    for q in ("How many vacation days?", "What is the equipment allowance?"):
        system = [{"type": "text", "text": "You answer questions about the handbook below."},
                  {"type": "text", "text": hb, "cache_control": {"type": "ephemeral"}}]
        receipt(f"  {q}", client.messages.create(model=MODEL, max_tokens=400, system=system,
                                                 messages=[{"role": "user", "content": f"{q} (asked at {time.strftime('%H:%M:%S')})"}]))
        time.sleep(1.2)


def auto():
    """The on-screen one-liner. Same handbook, no clip on any block; the API places the breakpoints."""
    system = "You answer questions about the Northwind Analytics employee handbook below. Quote the policy.\n\n" + handbook_text()
    for q in ("How many vacation days do new employees get?", "What is the equipment allowance?"):
        response = client.messages.create(
            model=MODEL,
            max_tokens=800,
            cache_control={"type": "ephemeral"},        # one line turns it on
            system=system,
            messages=[{"role": "user", "content": q}],
        )
        receipt(q[:34], response)
        time.sleep(1)


{"--short": short, "--timestamp": timestamp, "--auto": auto}.get(next((a for a in sys.argv[1:] if a.startswith("--")), ""), handbook)()

# Real runs (test/results.json, Bedrock, 2026-10-27):
#   --short:  input 513 / 488, written 0, read 0 on both calls. The prefix is about 490 tokens. Silent miss.
#   handbook: call 1 written 1,285 / read 0 / uncached 18, 3.4 s. Call 2 written 0 / read 1,285 / uncached 16,
#             4.4 s. The read was NOT faster this time (longer answer, 395 vs 268 output tokens). The saving
#             is on the bill, not the clock, at this size.
#   --timestamp: on top -> written 1,286 then written 1,286 again, read 0. Below the clip -> written 1,268,
#             then read 1,268.
#   count_tokens is not available on Bedrock; the 490 was inferred from input_tokens minus the question.
