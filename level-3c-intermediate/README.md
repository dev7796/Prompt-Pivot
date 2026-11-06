# Level 3c · Intermediate — Built-in Tools and a Research Assistant

Code from the video on Claude's three server tools (web search, web fetch, code execution), what makes
a tool easy for an agent to use well, and the build: a research assistant that searches the web and
saves sourced notes with a client tool of our own.

| File | Section | What it shows |
|---|---|---|
| `01_web_search.py` | 3.10 | `web_search_20250305` with `allowed_domains`; the block order; citations; `--turn2` and the rule about sending results back unchanged |
| `02_web_fetch.py` | 3.10 | Fetch with a URL; `--no-url` (blocked, Claude states the rule); `--search-first` (fetch -> blocked -> search -> fetch) |
| `03_code_execution.py` | 3.10 | Mean and SD of 1..10 with the tool off and on; `--chart` for the Files API round trip (corrected code) |
| `04_tool_design.py` | 3.11 | The 3a weather tool before (3 tools, 40 fields) and after (1 tool, 6 fields) on five questions |
| `05_research_assistant.py` | build | `web_search` + `save_note` in one tools list; the loop with `pause_turn`; per-step token trace |

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install anthropic==1.13.0
export ANTHROPIC_API_KEY="sk-ant-..."
python 05_research_assistant.py
```

**This chapter does not run on Amazon Bedrock.** Web search, web fetch and code execution execute on
Anthropic's infrastructure during the turn, and Bedrock does not bridge to it. `test/probe_bedrock_tools.py`
tried all six published tool versions against both Opus 5.5 inference profiles: twelve attempts, twelve
`tool type '...' is not supported for this model`. Anthropic's docs say the same. So this is the one
level that uses `anthropic.Anthropic()` instead of `AnthropicBedrock`; `04_tool_design.py` (client tools
only) works on either. Everything after Level 3c goes back to Bedrock.

Cost of running everything here once: about $1 (web search is $10 per 1,000 searches plus tokens; the
research run is the expensive one at ~73K input tokens).

## What the real runs showed

Every number and quote in the video comes from `test/results.json` (direct API, Opus 5.5, one pass of
`test/run_demos.py` on 2026-10-26, no reruns, about $0.80). Five things were not in the script:

- **Claude refused to fetch a URL it wrote itself.** Asked for "the Anthropic tool use overview page"
  with no URL in the conversation, Claude produced the docs URL, the tool blocked it, and Claude explained
  the rule in its reply. With search enabled too, the sequence was fetch (blocked), search, fetch (works):
  the search result put the URL into the conversation. Fetch is gated on provenance, not on correctness.
- **Code execution was switched on and never used.** For the docs' own 1..10 example, Opus did the
  arithmetic in its head, correctly, with blocks `['thinking', 'text']`. Server tools are still Claude's
  choice; turning one on is an offer.
- **Changing the tools list between turns is a 400.** Opus 5.5 returns a signed thinking block in
  server-tool responses, and the signature covers the tools list. Turn two dropped `allowed_domains` and
  got `Invalid signature in thinking block ... The tools list differs from the one this block was created
  with`. Send the content back unchanged, and the same tools.
- **Input tokens did not climb step by step.** The research run finished in two steps: 45,661 in on step 0
  (the search results read in-turn) and 27,519 on step 1 (the conversation re-sent). A five-step run pays
  the re-send five times, which is the setup for Level 4.
- **The redesigned tool made no fewer mistakes**, because there were none to fix: zero wrong-tool picks on
  either side. The measurable change was 6 calls to 5 and richer inputs (`'Lyon, France'`, `mode`, `detail`).

Also: the CSV-to-chart demo did not run in the video's pass. The harness called `client.messages.create`
with `betas=`, which the plain client rejects before any request is sent; the correct call is
`client.beta.messages.create`. The video says so on camera; `03_code_execution.py --chart` has the fix.

## Five gotchas

1. Not on Bedrock. One different client line; everything else is the same SDK.
2. Send server-tool results back byte for byte, with the same `tools` list. Both are signed.
3. Fetch only follows URLs already in the conversation. Pair it with search when the user has no URL.
4. `max_uses` is a cap, not a plan. Three of eight searches used; Claude stops when it has enough.
5. `pause_turn` is a stop reason. Call again with the conversation as is; don't append anything.

Video: Level 3c on the AI: Prompt & Pivot channel. Previous: `../level-3b-intermediate/`.
Next: Level 4 (prompt caching and memory).
