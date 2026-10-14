# Level 3a · Intermediate — Give Claude Hands

Code from the video on tool use and the agent loop. The build is a weather agent: one round trip
by hand, then the twenty-line loop, then the loop chaining two tools without being told to.

| File | Section | What it shows |
|---|---|---|
| `01_define_tool.py` | 3.2 | A tool is a name, a four-sentence description and a JSON Schema. Then the cost: 18 tokens without the tool, 461 with it |
| `02_round_trip.py` | 3.3 | The four steps by hand: ask, get `tool_use`, YOU run the function, send `tool_result`, get the answer |
| `03_agent.py` | 3.4 | The agent loop. Two tools, `TOOL_FUNCTIONS` for your code and `TOOLS` for Claude, joined by the name |
| `04_tool_result_rules.py` | 3.5 | Break rule two on purpose: text before a `tool_result` is a 400. Then the right order |
| `05_instructive_errors.py` | 3.5 | An error message is a mini-prompt. One instructive error, one retry, right answer; and the Lyon case where the example biased the retries |

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
python 03_agent.py "Compare the weather in Paris and Tokyo in Fahrenheit"
```

The weather "service" is a four-city dictionary, so every run has a known ground truth and costs
nothing but tokens. Replace `get_weather` with a real API call and nothing else changes.

On Bedrock, swap `anthropic.Anthropic()` for `anthropic.AnthropicBedrock(aws_region="us-east-1")` and
the model id for `us.anthropic.claude-opus-5-5`. Bedrock has no `count_tokens`; `test/run_demos.py`
measures with two `max_tokens=1` calls and `usage.input_tokens`.

## What the real runs showed

Every number and quote in the video comes from `test/results.json` and `test/results_error_variants.json`
(Bedrock, Opus 5.5, 12 calls). Three things happened that were not in the script:

- **The tool description talked back.** The first round trip's answer ended "I can only get the current
  temperature, so I can't tell you about the forecast." That sentence is lifted from "Does not return
  forecasts" in the description. Claude read the label on the drawer and told the user what the drawer
  can't do. Write the four sentences; they get used.
- **Parallel tool use, unprompted.** "Compare Paris and Tokyo" produced two `tool_use` blocks in one
  turn, then two conversions in the next: four tool calls, two trips round the loop. The loop copes
  because it iterates over every block and sends all results back in one message. Level 3b goes deeper.
- **The instructive error worked, and then it biased.** With "Try the full name with region, e.g.
  'San Francisco, CA'", SF resolved in one retry. Lyon got four good-faith retries (Lyon, France; ...,
  FR), all failing, then a correct diagnosis that the US-style example implies US-only coverage. An
  error message is a prompt; its example shapes the guesses.

## Rules for `tool_result` (where the bugs live)

1. Every `tool_use` gets exactly one `tool_result`, matched by `tool_use_id`.
2. `tool_result` blocks come first in the next user message. Text may follow, never lead.
3. All results for one assistant turn go back in one user message.
4. Tool output lands only in a `tool_result`'s `content`. Never in the system prompt, never as a plain
   user message. Data stays in the data slot.

Video: Level 3a on the AI: Prompt & Pivot channel. Previous: `../level-2b-beginner/`.
Next: `../level-3b-intermediate/` (tool_choice, parallel tools, strict tools, the SDK tool runner).
