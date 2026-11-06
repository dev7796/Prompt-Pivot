# Level 4a real runs (2026-10-27, Bedrock us-east-1, alps-optum, Opus 5.5 + Haiku 4.5)

Three passes of `run_demos.py` (full, then `--only` for the Haiku ID fix + a harder question + a second
preserve attempt). 21 recorded runs, ~30 calls. Spend: 6,050 uncached input, 6,870 cache-write, 9,634
cache-read, 4,050 output tokens: about **$0.14**.

```
AWS_CONFIG_FILE=$HOME/.aws/config AWS_SHARED_CREDENTIALS_FILE=$HOME/.aws/credentials \
uv run --quiet --with anthropic --with boto3 --with pypdf python3 test/run_demos.py            # everything
uv run --quiet --with anthropic --with boto3 --with pypdf python3 test/run_demos.py --only build,cache_loop
```

## Bedrock support (the open questions from PLAN.md, all answered)
- `thinking={"type":"adaptive","display":"summarized"|"omitted"}`: accepted. Summarized returns text; omitted returns an empty `thinking` field with a signature.
- `output_config={"effort": ...}`: accepted.
- Top-level `cache_control={"type":"ephemeral"}` (automatic caching): **works on Bedrock**, including the moving breakpoint across an agent loop.
- Usage exposes `cache_creation_input_tokens` and `cache_read_input_tokens`.
- `client.messages.count_tokens` is NOT available on Bedrock (`AnthropicError`); the prefix size was inferred from `input_tokens` minus the question.
- Haiku 4.5 needs the full id `us.anthropic.claude-haiku-4-5-20251001-v1:0`; the short alias 3b used (`us.anthropic.claude-haiku-4-5`) now returns "The provided model identifier is invalid."

| run | what happened |
|---|---|
| gcd_summarized | blocks [thinking, text], 1-sentence summary, answer 21 with Euclid, **140 out**, 3.4 s |
| gcd_omitted | thinking field empty, signature present, same answer, **140 out** (identical), 2.1 s |
| hard_summarized (bat & ball) | summary shows the route (a little garbled: says 0.05/1.05 "doesn't satisfy" when it does), answer 1.02 correct, 46 out, 3.4 s |
| hard_omitted | 1.02, 58 out, 1.4 s |
| hard_effort_low / high | 44 out / 55 out, both 1.02, both ~1.2 s |
| enabled_400 | 400 `"thinking.type.enabled" is not supported for this model. Use "thinking.type.adaptive" and "output_config.effort" to control thinking behavior.` |
| disabled_400 | same text with `disabled` |
| haiku_adaptive_400 | 400 `adaptive thinking is not supported on this model` |
| haiku_enabled (budget 2000) | blocks [thinking, text], FULL working in the thinking field (Euclid + verification + GCD(51,22)), 331 out, 1.9 s |
| preserve (attempt 1) | step 1 content was `[tool_use]` only: no thinking block existed to drop; tidy history **accepted** |
| preserve2 (attempt 2, "closest to 70F") | step 0 `[tool_use x3]`, step 1 `[thinking, text, tool_use]` with a real interleaved summary ("70F ~ 21.1C, 3.1 off Paris, 3.9 off Tokyo, so Paris"), dropped the thinking block and sent tool_result: **accepted**, returned [thinking, text]. Honest run: 3 steps, Paris 64.4F |
| cache_short (3a prefix) | input 513 / 488, written 0, read 0 both calls: prefix ~490 < 512, silent miss |
| cache_handbook (1,285 tok) | call 1 write 1,285 / read 0 / uncached 18, 3.4 s; call 2 write 0 / read 1,285 / uncached 16, **4.4 s** (slower: longer answer, 395 vs 268 out) |
| cache_loop (briefing, top-level) | 3 steps (parallel calls). Per step (write/read/uncached): 1,214/0/4 · 240/1,214/2 · 291/1,454/2. $0.0168 vs $0.0252 uncached (-33%) |
| cache_loop_uncached | input 1,218 / 1,456 / 1,747; identical calls and answer |
| cache_timestamp | on top: write 1,286, write 1,286 (read 0). Below the clip: write 1,268, read 1,268 |
| build (summarized thinking + cache) | 3 steps, 5.2 s. Per step write/read/uncached: 0/1,214/4 · 0/1,454/2 · 0/1,745/2 (cache still warm from cache_loop a minute earlier). **0 thinking blocks with text.** $0.0084 vs $0.0252 (-67%) |

## Findings that changed the script
- **Opus 5.5 barely thinks on these questions.** GCD: 140 output tokens in both display modes; the summarize-vs-omit
  comparison showed no token difference because there was almost nothing to hide. The bat-and-ball trap: 44-58
  output tokens, correct every time. `thinking_live` now teaches "adaptive means Claude decides, and it decided
  not to" and the 16,000 budget as headroom. `effort` beat 4 reports low 44 vs high 55 honestly.
- **The summarized thinking is lossy.** The bat-and-ball summary mis-states the first check. Added as a beat:
  a window, not a transcript.
- **Haiku 4.5 in legacy mode shows the full working** (331 tokens, verification included) where Opus showed one
  line. Now the contrast in the Haiku beat.
- **Could not reproduce the preserve-thinking 400 by deleting a block**, even when a real interleaved thinking
  block existed (preserve2). Modifying what the signature covers DID 400 in 3c (tools list). The `preserve` scene
  now tells both attempts, keeps the rule, and says plainly which error we have evidence for.
- **The build run read on step 1**: the cache from cache_loop (same briefing + tools) was still warm. Became the
  "five-minute lifetime, refreshed on hit" beat, and the hook's "rerun: input bill down 67%".
- **The build produced zero thinking blocks with text** across 3 steps; the only mid-loop thinking today was
  preserve2 step 1 (a comparison). `build_run` beat 3 teaches: thinking appears between tool calls when there
  is a decision between them.
- **Cache read was not faster** on the handbook (4.4 s vs 3.4 s, longer answer). Walked back on camera.
- The loop is 3 steps not 4: with the briefing, Claude requests all three cities / conversions at once.
- Prefix for the 3a agent is ~490 tokens, 22 short of the 512 minimum: the silent-miss beat is real.

## Not in the video
- count_tokens unavailable on Bedrock (the script infers the prefix from input_tokens).
- The uncached loop was 5.3 s vs 6.5 s cached (both within noise of each other).
