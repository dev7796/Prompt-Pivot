# Level 4a · Advanced — Think Better

Code from the video on extended thinking (4.1) and prompt caching (4.2), and the build: the Level 3a
weather agent with two lines added to the request and one habit kept in the loop.

| File | Section | What it shows |
|---|---|---|
| `01_thinking.py` | 4.1 | Adaptive thinking with `display` summarized / omitted; `--hard` for a question with a trap; `--legacy` for the three 400s and Haiku's full working |
| `02_effort.py` | 4.1 | `output_config.effort` low vs high, side by side with output tokens and seconds |
| `03_preserve.py` | 4.1 | The agent loop with thinking; `--tidy` drops the thinking block so you can see what the API does (and read what it did for us) |
| `04_caching.py` | 4.2 | The handbook written then read; `--short` the silent miss under 512; `--timestamp` the trap; `--auto` the one-line version |
| `05_agent_4a.py` | build | The 3a agent plus `thinking=` and `cache_control=`; a receipt per step; `--uncached` control run |
| `briefing.md` | build | The system prompt the agent reads (about 1,200 tokens, so the cache has something to hold) |

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install anthropic==1.13.0 pypdf        # pypdf reads the Level 2b handbook for 04_caching.py
export ANTHROPIC_API_KEY="sk-ant-..."
python 05_agent_4a.py
```

This level is back on Amazon Bedrock in the video: swap `anthropic.Anthropic()` for
`anthropic.AnthropicBedrock(aws_region="us-east-1")` and the model id for `us.anthropic.claude-opus-5-5`.
Everything here works there: adaptive thinking with `display`, `output_config.effort`, top-level
`cache_control`, and both cache fields on `usage`. Two Bedrock differences: `client.messages.count_tokens`
is not available, and Haiku 4.5 needs its full id `us.anthropic.claude-haiku-4-5-20251001-v1:0` (the short
alias Level 3b used now returns "The provided model identifier is invalid").

Cost of running everything here once: about 15 cents. The thinking demos are small; the caching demos
are mostly cache reads.

## What the real runs showed

Every number and quote in the video comes from `test/results.json` (Bedrock, Opus 5.5 and Haiku 4.5, 21
runs across three passes of `test/run_demos.py` on 2026-10-27, about $0.14). Six things were not in the
script:

- **Opus 5.5 barely thinks on small questions.** The GCD cost 140 output tokens with thinking summarized
  and 140 with it omitted: identical, because there was almost nothing to hide. The bat-and-ball trap: 44
  to 58 tokens, correct every time. Adaptive means Claude decides, and it decided not to. The 16,000
  `max_tokens` is headroom, not a plan.
- **The summary is lossy.** The bat-and-ball summary mis-states one of its own checks (says 0.05/1.05
  "doesn't satisfy" the constraint when it does) and still lands the right answer. A window, not a
  transcript.
- **Haiku 4.5 in legacy mode shows the whole working.** Euclid, a verification pass, 331 output tokens,
  where Opus wrote one line. Same question.
- **Deleting a thinking block did not return a 400.** Twice. The first attempt had no thinking block to
  drop (step 0 was `[tool_use]` only). The second produced a real interleaved block ("70F is about 21.1C,
  3.1 off Paris, 3.9 off Tokyo, so Paris"), we dropped it, and the request was accepted. The rule is
  documented and Level 3c has a proven signature 400 (a changed tools list), so the loop still appends
  `response.content` as-is; we just can't show you the delete failing.
- **The build read on step 0.** The cache from the previous demo (same briefing, same tools) was still
  warm a minute later: 1,214 read, 4 uncached, before the agent had written anything. Five-minute
  lifetime, refreshed on every hit. The cold version is `cache_loop` in `results.json`: 1,214 written on
  step 0, read from step 1, 33% off over three steps. Warm: 67% off.
- **The cache read was not faster** on the 1,285-token handbook (4.4 s vs 3.4 s, longer answer). The
  saving at this size is on the bill, not the clock.

Also: the agent loop is three steps, not four. With the briefing's "request all of them at once", Claude
asks for all three cities in one turn and converts all three in the next (Level 3b parallel calls).

## Five gotchas

1. `enabled` / `disabled` / `budget_tokens` are a 400 on Opus 5.5, Sonnet 5.5, Fable and Mythos. Use
   `adaptive` and `effort`. Haiku 4.5 is the reverse: `adaptive` is the 400 there.
2. Append `response.content` whole. Never filter the thinking block out, never edit it.
3. Under 512 tokens nothing caches and nothing complains. Both receipt fields read zero. Check them.
4. Anything above the clip that changes between calls (a timestamp, a user name, today's date) rewrites
   the whole prefix. Put changing text below the breakpoint.
5. The order is tools, system, messages. A clip on the last tool caches all tools; a clip on the last
   system block caches tools and system.

Video: Level 4a on the AI: Prompt & Pivot channel. Previous: `../level-3c-intermediate/`.
Next: Level 4b (memory and the long game).
