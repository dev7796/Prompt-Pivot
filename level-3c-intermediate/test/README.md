# Level 3c real runs (2026-10-26, direct Anthropic API, claude-opus-5-5)

Single pass of `run_demos.py`, no reruns (user asked to keep cost minimal). Spend: about 150K input
tokens, 8K output, 5 web searches, 4 fetches -- roughly $0.80 at list price.

Run with the key in `~/.anthropic_api_key` (one line, chmod 600) or `ANTHROPIC_API_KEY`:
```
AWS_CONFIG_FILE=$HOME/.aws/config AWS_SHARED_CREDENTIALS_FILE=$HOME/.aws/credentials \
uv run --quiet --with anthropic --with boto3 python3 test/run_demos.py            # everything
uv run --quiet --with anthropic --with boto3 python3 test/run_demos.py --only csv_chart,web_search
```
`--only` re-runs the named demos and merges into `results.json`.

## Backend
Bedrock refused all three server tools (12/12 across every published tool version and both Opus
inference profiles; `probe_bedrock_tools.py`). Matches the docs: not available on Amazon Bedrock.
All runs below are on the direct API.

| run | what happened |
|---|---|
| web_search | 1 search, 20 blocks (server_tool_use, web_search_tool_result, thinking, 17 text), 8 citations all on anthropic.com/claude.com, 8.8 s, 23,080 in / 849 out. Answer: Anthropic filed an S-1 (ticker ANT) this week, plus last week's items |
| web_search turn 2 | **400** `Invalid signature in thinking block ... The tools list differs from the one this block was created with` -- harness bug (turn 2 dropped `allowed_domains`), but a real rule: resend content AND the same tools list. Turn 3 (strip `encrypted_content`) never ran |
| web_fetch_with_url | fetched, 16 blocks, 6 citations, 6.4 s; noticed the URL now redirects to platform.claude.com |
| web_fetch_without_url | Claude wrote the docs URL itself; the tool blocked it; Claude explained the rule in its reply ("only URLs you've pasted in or that came from earlier search results") |
| search_then_fetch | fetch (blocked, URL not yet in conversation) -> search -> fetch (works). 17.3 s, 6 citations; quotes workflows vs agents and corrects the question ("architectural distinction", not "two core patterns") |
| stats_no_tools | mean 5.500; SD 2.872 population / 3.028 sample; picked population with the reason. Correct. 4.5 s |
| stats_code_exec | **tool never called**: blocks = thinking, text. Same numbers by hand, 4.4 s |
| csv_chart | **did not run**: `Messages.create() got an unexpected keyword argument 'betas'` (needs `client.beta.messages.create`). Fixed in code, not rerun. The scene says so |
| design_eval | 5 questions x 2 tool sets: before 6 calls (Tokyo used 2 tools), after 5; wrong picks 0/0; output tokens 387 vs 417 (richer inputs: "Lyon, France", mode, detail) |
| research | 2 steps, 3 searches (of 8 allowed), 5 save_note calls all in step 0 as parallel client calls, 0 pause_turn, 34.6 s, 73,180 in / 3,629 out, per-step input 45,661 then 27,519. 5 notes, 18 URLs, every note sourced |

## Findings that changed the script
- Opus 5.5 returns a **thinking block** in server-tool responses without being asked, and the block's
  signature covers the tools list. Changing `tools` between turns is a 400. Now the "send it back
  unchanged" beat in `search_live` (the planned encrypted_content strip was never reached).
- **Code execution was not invoked** for the docs' own 1..10 example; Opus did the arithmetic in its
  head, correctly, both with and without the tool. `code_live` now teaches "server tools are still
  Claude's choice" and the `code_exec` claim about arithmetic was softened.
- The **no-URL fetch** case I had scripted from the docs happened live: blocked, and the model stated the
  rule itself. The search-then-fetch run showed the fetch -> blocked -> search -> fetch sequence.
- **Input tokens did not grow per step** as scripted: the run finished in 2 steps, step 0 was the larger
  (45.7K, search results read in-turn), step 1 re-sent the conversation at 27.5K. `build_trace` now
  states those two numbers and the "a 5-step run pays that five times" framing.
- Design mini-eval: no wrong-tool picks on either side; the measurable change was 6 -> 5 calls and
  richer inputs, not fewer mistakes. Said plainly.
- CSV -> chart demo is narrated from the docs with an on-camera admission; corrected code is in the repo.
