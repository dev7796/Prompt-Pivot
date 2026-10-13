# Level 2b · Beginner — Documents, Images and Proof

Code for the video on vision, PDFs, citations and the Files API. The build is a document Q&A
tool that answers only from a PDF and prints the page number after every claim.

Lesson scripts land here as the video is finished. What is here now:

| Path | What it is |
|---|---|
| `test/make_assets.py` | Builds the synthetic charts and PDFs used on screen (known ground truth) |
| `test/run_demos.py` | The real API calls behind every number in the video (Bedrock) |
| `test/results.json` | Full responses, including the citation objects |
| `test/README.md` | Summary table and the hallucination-attempt finding |
| `test/assets/` | `chart.png`, `chart_q3.png`, `chart_q4.png`, `quarterly_report.pdf`, `employee_handbook.pdf` |

## The finding worth reading

I tried five ways to make Claude Opus 5.5 invent a "remote-work stipend" that the handbook does not
contain: no permission sentence in the system prompt, no system prompt at all, citations off, a
"helpful HR assistant, always give a clear specific answer" prompt, and a leading question that
presupposes the stipend exists. It refused every time and pointed at the nearest real thing (a
one-time $500 equipment allowance, p.3). Haiku 4.5 with the same bad prompt titled its answer
"# Remote Work Stipend" and led with the $500 before noting it is one-time. Details in `test/README.md`.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install anthropic
export ANTHROPIC_API_KEY=...        # or use AnthropicBedrock as run_demos.py does
```
