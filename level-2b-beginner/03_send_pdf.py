"""Level 2b, section 2.4: a PDF is a document block.

Same shape as an image, with type "document" and media_type "application/pdf".
Claude reads the text AND sees each page as an image, so tables and charts in the PDF work.
"""
import base64, anthropic
client = anthropic.Anthropic()

with open("quarterly_report.pdf", "rb") as f:
    pdf_b64 = base64.standard_b64encode(f.read()).decode()

message = client.messages.create(
    model="claude-opus-5-5", max_tokens=600,
    messages=[{"role": "user", "content": [
        {"type": "document",
         "source": {"type": "base64", "media_type": "application/pdf",
                    "data": pdf_b64}},
        {"type": "text", "text": "List the three key findings, then tell me "
                                 "which quarter had the highest operating "
                                 "margin and what it was."},
    ]}],
)
print(message.content[-1].text)  # last block is the text; block 0 may be thinking
