# Level 2a · Beginner — Make Claude Reliable

Code from the video on prompt engineering and structured outputs. One project runs through the
whole lesson: a support-ticket triage bot that goes from a chatty paragraph to a typed, validated object.

| File | Section | What it shows |
|---|---|---|
| `01_triage_v1_naive.py` | 2.1 | The "before": correct answers, none machine-readable |
| `02_examples_prompt.py` | 2.1 | Multishot prompting with XML-fenced examples |
| `03_xml_tags_contract.py` | 2.1 | Fences for instructions / context / input, and "give it a way out" |
| `04_long_documents.py` | 2.1 | Documents first, question last; quote before answering |
| `05_structured_pydantic.py` | 2.2 | `messages.parse()` + a Pydantic model = guaranteed shape |
| `06_triage_v2_structured.py` | 2.2 | The finished bot: enum category, `stop_reason` check |
| `07_structured_raw_schema.py` | 2.2 | The same guarantee with a hand-written JSON Schema |

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install anthropic pydantic
export ANTHROPIC_API_KEY="sk-ant-..."
python 06_triage_v2_structured.py
```

## Try it
- Run `01` and `06` on the same message five times each. Count how many outputs you could `==` compare.
- Delete the `<examples>` block from `06`. The shape is still guaranteed; is the *decision* still right?
- Make `reason` an `Optional[str]` and send a message with no content. Watch Claude use `None` instead of inventing a reason.
- Add a fourth category to the enum without adding an example for it. See how often Claude picks it.
