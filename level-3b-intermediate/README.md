# Level 3b · Intermediate — Steering the Tools

Code from the video on tool_choice, parallel tool use, strict tools and the SDK tool runner. The
build is the Level 3a weather agent rewritten: two decorated functions, strict schemas, the
runner, zero lines of loop.

| File | Section | What it shows |
|---|---|---|
| `01_tool_choice.py` | 3.6 | The four values; the 400 you get forcing a tool on Opus 5.5; `none` returning zero blocks; `none` on the final turn |
| `02_parallel.py` | 3.7 | Three cities in one turn; `ThreadPoolExecutor` with `pool.map`; the calls-per-message metric; `--serial`, `--nudge`, `--slow` |
| `03_strict_tools.py` | 3.8 | `book_meeting` with `strict: True`; `--trials 5` to compare against non-strict |
| `04_runner.py` | 3.9 | `@beta_tool` and what `to_dict()` builds; `tool_runner(...).until_done()` |
| `05_agent.py` | build | The 3a agent, rewritten: `@beta_tool(strict=True)` + runner + nudge; `for message in runner` as the trace |

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install anthropic==1.13.0        # the runner is beta: pin it
export ANTHROPIC_API_KEY="sk-ant-..."
python 05_agent.py
```

On Bedrock, swap `anthropic.Anthropic()` for `anthropic.AnthropicBedrock(aws_region="us-east-1")` and
the model id for `us.anthropic.claude-opus-5-5`. The runner is SDK-side, so it works there too.

## What the real runs showed

Every number and quote in the video comes from `test/results.json` (Bedrock, Opus 5.5, 26 calls across
`test/run_demos.py`, `test/run_followups.py`, `test/run_probe2.py`). Four things were not in the script:

- **`tool_choice: none` can return an empty response.** On a question that wants the tool, Opus 5.5
  returned `end_turn` with zero content blocks and one output token. A system prompt telling it to say
  so if it can't check didn't help. It answers normally only when no tool was wanted, or when the tool
  results are already in the conversation. The guide's "none still works everywhere" is true (no error)
  but incomplete. Rule: `none` at the end of a run, never at the start.
- **Strict showed no visible difference in ten calls.** Five trials each way on a deliberately sloppy
  request ("the big room for a dozen of us a week from Friday") all produced `Everest`, `12` (int),
  `2026-10-23`. Strict is a contract for the day the track record breaks, not something you can watch work.
- **The disabled-parallel run admitted it.** With `disable_parallel_tool_use: true` the agent took six
  steps instead of two and ended its answer with "I made these lookups one by one when I could have run
  them all at once."
- **The nudge did nothing** on this question because the baseline was already fully parallel (2.0 calls
  per assistant message with and without).

Also: forcing (`tool` and `any`) both return `400 - tool_choice: type "tool" and "any" are not supported
for this model.` on Opus 5.5; Haiku 4.5 accepts it. `disable_parallel_tool_use` at the top level is an
SDK `TypeError` before the request is sent, not an API 400. The thread pool needed real latency to show
anything: with a 1 s sleep per tool, 18.5 s serial became 10.2 s pooled.

## Five gotchas

1. Forcing is a 400 on the newest models. Use `auto` + an instruction, strict, or structured outputs.
2. `none` can return zero blocks. Final turn only, when the context already holds the answer.
3. `disable_parallel_tool_use` goes inside `tool_choice`.
4. One result per user message kills parallelism silently. Collect, then append once.
5. Strict has budgets (20 tools, 24 optional params, 16 unions) and the runner is beta: pin the SDK.

Video: Level 3b on the AI: Prompt & Pivot channel. Previous: `../level-3a-intermediate/`.
Next: `../level-3c-intermediate/` (server tools: web search, web fetch, code execution; a research assistant).
