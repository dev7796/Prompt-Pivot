# Level 2a · Beginner — Make Claude Reliable

Code from the video on prompt engineering and structured outputs. One project runs through the
whole lesson: a support-ticket triage bot that goes from a chatty paragraph to a typed, validated object.

| File | Section | What it shows |
|---|---|---|
| `01_triage_v1_naive.py` | 2.1 | The "before". Crashes on Opus 5.5 (`content[0]` is a thinking block), then returns paragraphs, not labels |
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

## The 200-message test (from the video)

Both bots were run on the same 200 support messages (70 billing / 70 bug / 60 other) on Claude Opus 5.5:

| | bare label | correct |
|---|---|---|
| `01` naive, as written | crashed 200/200 (`content[0].text`) | -- |
| `01` naive, text blocks only | 0 / 200 | 107 / 200 if you regex a label word out of the prose |
| `06` examples + `parse()` | 200 / 200 | 198 / 200 |

The two misses were judgement calls (an invoice PDF returning a 404, a cancel link stuck in a login loop; both labelled BUG).
The dataset and harness are in `test/`.

## Try it
- Run `01` and `06` on the same message five times each. Count how many outputs you could `==` compare.
- Delete the `<examples>` block from `06`. The shape is still guaranteed; is the *decision* still right?
- Make `reason` an `Optional[str]` and send a message with no content. Watch Claude use `None` instead of inventing a reason.
- Add a fourth category to the enum without adding an example for it. See how often Claude picks it.
