# Level 3b real runs

All outputs quoted in the video come from these calls (Bedrock, us-east-1, `us.anthropic.claude-opus-5-5`;
Haiku = `us.anthropic.claude-haiku-4-5-20251001-v1:0`). Three scripts, 26 runs, all merged into `results.json`:
`run_demos.py` (18), `run_followups.py` (6: Haiku id fix, `none` block inspection, `@beta_tool(strict=True)`),
`run_probe2.py` (4: `none` on a non-tool question, serial vs pool with 1 s tools).

Run with the SDK pointed at the standard AWS files (the agent's session uses a different location):
```
AWS_CONFIG_FILE=$HOME/.aws/config AWS_SHARED_CREDENTIALS_FILE=$HOME/.aws/credentials \
uv run --quiet --with anthropic --with boto3 python3 test/run_demos.py
```

| run | what happened |
|---|---|
| forced_opus, any_opus | 400: `tool_choice: type "tool" and "any" are not supported for this model.` (both values) |
| forced_haiku | stop_reason tool_use, content = [tool_use] only, no text. auto_haiku: identical, so the "no text before" contrast is not demonstrable on this question |
| none_opus (tool question) | end_turn, **zero content blocks**, 1 output token. Same with a system prompt and with "if you can't check, say what you'd need" |
| none_opus_no_tool_needed | normal 56-token answer. `none` only goes silent when the model wanted a tool |
| final_none | agent ran get_weather + conversion, then a `tool_choice: none` call produced "It's **64.4°F (18°C)** in Paris right now." |
| three_cities | step 0: 3x get_weather; step 1: 3x conversion; 6 calls / 3 assistant msgs = 2.0; 10.0 s; answer volunteers "Tokyo is the warmest" |
| three_cities_pool | same trace, 8.8 s (fake tools are instant, so no real difference; see slow_*) |
| slow_serial / slow_pool | 1 s sleep per tool: 3.0 s vs 1.0 s per batch; 18.5 s vs 10.2 s end to end |
| partial_failure | Atlantis -> "No data"; step 1 converted only the two real cities (5 calls, 1.67); answer: "It's a legendary city, not a real place." |
| parallel_disabled | `tool_choice: {auto, disable_parallel_tool_use: true}` -> 6 steps, 0.86, 18.1 s; answer ends "I made these lookups one by one when I could have run them all at once." |
| disable_top_level | SDK TypeError (unexpected keyword argument) before the request is sent |
| nudged | system-prompt nudge: 2.0, same as baseline (already maxed on this question) |
| book_nonstrict / book_strict / book_trials | 5 trials each: every call `{"room": "Everest", "attendees": 12, "date": "2026-10-23"}`, attendees int. **No divergence**; the scene says so |
| runner_schema, strict_decorator | `to_dict()`: name from function, description from docstring line 1, Args -> property descriptions, type hints -> types, `additionalProperties: false` added; `@beta_tool(strict=True)` adds `"strict": true` |
| runner_tokyo | works on Bedrock, 3.2 s: "It's 25°C in Tokyo right now. I can only check the temperature, so I don't know about other conditions like rain or humidity." |
| runner_build / runner_strict_build | 3 turns, 3+3 calls, 2.0, 12.8 s / 10.3 s; same list answer |
| runner_strict_type | "to the nearest degree" -> celsius argument 25 (int), answer "about **77°F**" |

## Findings that changed the script
- **`tool_choice: none` can return an empty response.** On Opus 5.5, with a question that wants the tool,
  `none` gives end_turn with zero blocks (1 output token), even when told to say it can't check. It answers
  normally only when no tool was wanted, or when tool results are already in the context (final_none). The
  guide's "none still works everywhere" is true (no error) but incomplete. Now the sharp edge in choice_live,
  the rule in choice_final, and gotcha #2.
- **Strict showed no visible difference in 10 calls.** The scene frames strict as a contract vs a track record
  rather than staging a failure.
- **The nudge did nothing** because the baseline was already fully parallel. Said plainly.
- **The disabled run's answer admits it was throttled** ("one by one when I could have run them all at once").
  Unstaged; now a beat.
- `disable_parallel_tool_use` at top level is an SDK TypeError, not an API 400. Gotcha #3 corrected.
- Haiku with `auto` also returned no text on this question, so the "forcing suppresses text" contrast is stated
  as the guide's claim, not shown.
