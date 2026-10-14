"""Level 2b, section 2.5: citations on a PDF.

For PDFs the citation type is page_location: start_page_number / end_page_number are 1-based.
The cited_text is the literal text from the page, so a number pulled from a table cell
comes back with the table row it was read from.
"""
import base64, anthropic
client = anthropic.Anthropic()

with open("quarterly_report.pdf", "rb") as f:
    pdf_b64 = base64.standard_b64encode(f.read()).decode()

response = client.messages.create(
    model="claude-opus-5-5", max_tokens=400,
    messages=[{"role": "user", "content": [
        {"type": "document",
         "source": {"type": "base64", "media_type": "application/pdf",
                    "data": pdf_b64},
         "title": "Quarterly report",
         "citations": {"enabled": True}},
        {"type": "text", "text": "What was the Q4 operating margin?"},
    ]}],
)
for block in response.content:
    if block.type != "text":
        continue
    print(block.text)
    for c in (block.citations or []):
        print(f"   [{c.type}] p.{c.start_page_number}-{c.end_page_number - 1}: {c.cited_text!r}")
