# Level 2b · Beginner — Documents, Images and Proof

Code from the video on vision, PDFs, citations and the Files API. The build is a document Q&A
tool that answers only from a PDF and prints the page number after every claim.

| File | Section | What it shows |
|---|---|---|
| `01_send_image.py` | 2.3 | Content is a list of blocks: one image block, one text block |
| `02_compare_images.py` | 2.3 | Two labelled images in one message; ask Claude to say where it read each number |
| `03_send_pdf.py` | 2.4 | A PDF is a `document` block; Claude reads the text and sees each page |
| `04_citations_text.py` | 2.5 | `citations: {enabled: true}` on a text document; the `cited_text` on each block |
| `05_citations_pdf.py` | 2.5 | Citations on a PDF: `page_location` with 1-based page numbers, the literal table row |
| `06_files_api.py` | 2.6 | Upload once, reference by `file_id`, list, delete. Claude-API-only (not Bedrock) |
| `07_doc_qa.py` | build | The finished tool: answer only from the document, `[p.N]` after every claim |

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
cp test/assets/* .            # chart.png, chart_q3.png, chart_q4.png, quarterly_report.pdf, employee_handbook.pdf
python 07_doc_qa.py
```

The sample files are synthetic (matplotlib charts, reportlab PDFs; `test/make_assets.py` builds them),
so every number has a known ground truth: the handbook has vacation on p.4, a one-time $500 equipment
allowance on p.3, and no remote-work stipend anywhere.

On Bedrock, swap `anthropic.Anthropic()` for `anthropic.AnthropicBedrock(aws_region="us-east-1")` and
use the base64 document block (`03`) instead of the Files API (`06`, `07`); Bedrock does not have the
Files API. `test/run_demos.py` is the Bedrock version of every call in the video.

## What the real runs produced (from the video)

| Demo | Result |
|---|---|
| Single chart | Read all four quarters and, unprompted, noted the y-axis starting at 80 exaggerates the climb |
| Two charts | Asia Pacific grew most, +$6.4M (about 35%), with a table saying where each number was read ("third bar, orange") |
| PDF with a table | All three findings plus the 24.1% Q4 margin pulled from a table cell on page 2 |
| Citations on the PDF | `cited_text` is the literal table row, `start_page_number: 2` |
| Handbook, vacation | 15 days, `[p.4]` after each sentence |
| Handbook, stipend | No recurring stipend; pointed at the $500 one-time allowance on p.3 and labelled it correctly |

## The finding worth reading

I tried five ways to make Claude Opus 5.5 invent a "remote-work stipend" that the handbook does not
contain: no permission sentence in the system prompt, no system prompt at all, citations off, a
"helpful HR assistant, always give a clear specific answer" prompt, and a leading question that
presupposes the stipend exists. It refused every time. Haiku 4.5 with the same bad prompt titled its
answer "# Remote Work Stipend" and led with the $500 before noting it is one-time: a real number under
a wrong label, which is what modern hallucination looks like. Keep the one-sentence defence anyway; it
is free and not every call runs on the big model. Details and full responses in `test/`.

## Try it
- Run `01` with `"What does the y-axis start at?"`. Then crop the chart so the axis is hidden and ask again.
- In `05`, ask a question the report does not answer. Count the citations in the reply (there should be none).
- In `07`, delete the second sentence of the system prompt and ask about the stipend on `claude-haiku-4-5`. Compare the heading.
- Upload the handbook once with `06` and ask ten questions. Compare the input-token count with sending base64 ten times.
