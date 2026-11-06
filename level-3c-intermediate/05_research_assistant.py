"""Level 3c, the build: a research assistant. Web search (server tool) plus save_note (client tool),
in the same loop.

    python 05_research_assistant.py
    python 05_research_assistant.py "How does prompt caching work in the Claude API?"

Two kinds of tool in one tools list. Claude runs the search on Anthropic's side and the results
arrive inside the response. save_note is ours: a tool_use comes back, we run it, we return a
tool_result. The loop is the Level 3a loop with one new branch: stop_reason == "pause_turn".

Needs the Anthropic API directly for web_search (not available on Bedrock).
"""
import sys
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-opus-5-5"


def save_note(title: str, body: str) -> str:
    with open("research_notes.md", "a") as f:
        f.write(f"\n## {title}\n\n{body}\n")
    return f"saved note: {title}"


TOOLS = [
    {"type": "web_search_20250305", "name": "web_search", "max_uses": 8},
    {
        "name": "save_note",
        "description": (
            "Save a finding to the user's research notes file. Call this once per "
            "distinct finding, with a short title and a body that includes the "
            "source URL. Returns a confirmation string."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "3-8 word title"},
                "body":  {"type": "string", "description": "The finding, plus its source URL"},
            },
            "required": ["title", "body"],
        },
    },
]


def research(topic, max_steps=15):
    messages = [{"role": "user", "content": f"Research this and save notes: {topic}"}]
    tokens_in = tokens_out = 0
    for step in range(max_steps):
        r = client.messages.create(
            model=MODEL, max_tokens=4096,
            system="You are a careful researcher. Cite sources in every note.",
            tools=TOOLS, messages=messages,
        )
        tokens_in += r.usage.input_tokens; tokens_out += r.usage.output_tokens
        messages.append({"role": "assistant", "content": r.content})

        for b in r.content:                             # the trace
            if b.type == "server_tool_use":
                print(f"[step {step}] SEARCH {b.input.get('query')!r}")
            elif b.type == "tool_use":
                print(f"[step {step}] save_note({b.input.get('title')!r})")
        print(f"[step {step}] input tokens: {r.usage.input_tokens}")

        if r.stop_reason == "pause_turn":          # server tool mid-flight
            continue                                # call again, as is
        if r.stop_reason != "tool_use":
            print(f"tokens in={tokens_in} out={tokens_out}")
            return "".join(b.text for b in r.content if b.type == "text")

        results = [{"type": "tool_result", "tool_use_id": b.id,
                    "content": save_note(**b.input)}
                   for b in r.content
                   if b.type == "tool_use" and b.name == "save_note"]
        messages.append({"role": "user", "content": results})
    return "Stopped at max_steps."


topic = sys.argv[1] if len(sys.argv) > 1 else "What is the Model Context Protocol and who supports it?"
print(research(topic))

# Real run (test/results.json, 2026-10-26): 2 steps, 34.6 s. Step 0: three searches (of 8 allowed) and
# five save_note calls, all in one assistant message -- the searches ran server-side, then the five
# client calls came out in parallel (Level 3b). Step 1: the summary. 0 pause_turn. 5 notes, 18 URLs,
# every note sourced. Tokens: 45,661 in on step 0, 27,519 on step 1, 73,180 total, 3,629 out.
# The input bill is the search results being read and then re-sent. A five-step run pays that five
# times. Level 4 is about paying for it once.
