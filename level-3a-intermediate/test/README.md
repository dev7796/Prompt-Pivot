# Level 3a real runs

All outputs quoted in the video come from these calls (Bedrock, us-east-1, `us.anthropic.claude-opus-5-5`).
`run_demos.py` produces `results.json` (9 runs); `run_error_variants.py` produces `results_error_variants.json`
(3 runs). Code is the guide's (pages 24-27) verbatim except the client line.

| run | what happened |
|---|---|
| tool_cost | 18 input tokens without tools, 461 with the one four-sentence tool (Bedrock has no count_tokens; measured via usage.input_tokens on max_tokens=1 calls) |
| step12 | stop_reason tool_use; content was a single tool_use block (no thinking block this run); get_weather {"city": "Paris"} |
| step34 | "It's 18°C (about 64°F) in Paris right now. I can only get the current temperature, so I can't tell you about rain or what the forecast looks like." -- the limitation sentence came from the tool description |
| wrong_order | 400: "messages.2: tool_use ids were found without tool_result blocks immediately after: toolu_... Each tool_use block must have a corresponding tool_result block in the next message." |
| right_order | "It's 18°C in Paris right now." |
| agent_paris_f | [step 0] get_weather Paris, [step 1] celsius_to_fahrenheit 18 -> "It's currently 64.4°F (18°C) in Paris." |
| agent_compare | step 0: get_weather Paris AND Tokyo (parallel, one turn); step 1: two conversions -> Tokyo warmer by 12.6°F, with a table |
| agent_atlantis | one call, "No data" -> explains, lists three real Atlantises, offers Nassau |
| error_retry (SF) | Claude expanded "SF" to "San Francisco" itself; error "City not found. Try the full name with region, e.g. 'San Francisco, CA'" -> retried with "San Francisco, CA" -> 15 C |
| error variant (Lyon) | four retries (Lyon; Lyon, France; Lyon, Auvergne-Rhone-Alpes, France; Lyon, FR), all fail, then a correct diagnosis that the US-style example suggests US-only coverage |

## Findings that changed the script
- The first round trip's final answer volunteered "I can't tell you about the forecast" -- lifted from the
  "Does not return forecasts" sentence in the tool description. Now a beat in step34_live.
- "Compare Paris and Tokyo" produced two tool_use blocks in ONE turn (parallel tool use). The guide's loop
  already handles it. Now shown in agent_run as a preview of 3b.
- The instructive-error demo needed a tool that only accepts the full "City, ST" form; Claude expands "SF"
  on its own. The Lyon variant shows the same error message biasing retries toward US-shaped names.
