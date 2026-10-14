"""Level 2b, section 2.6: the Files API. Upload once, reference by id.

The "locker": upload a file, get an id, use it in as many messages as you like, delete it when done.
No more base64 in every request. The Files API is Claude-API-only (not on Bedrock); if you run
on Bedrock, keep using the base64 document block from 03_send_pdf.py.
"""
import anthropic
client = anthropic.Anthropic()

uploaded = client.files.upload(
    file=("quarterly_report.pdf", open("quarterly_report.pdf", "rb"),
          "application/pdf"),
    expires_in_seconds=7 * 24 * 3600,
)
print(uploaded.id)
for f in client.files.list():
    print(f.id, f.size_bytes, f.created_at)

def ask(question: str):
    r = client.messages.create(
        model="claude-opus-5-5", max_tokens=400,
        messages=[{"role": "user", "content": [
            {"type": "document",
             "source": {"type": "file", "file_id": uploaded.id},
             "citations": {"enabled": True}},
            {"type": "text", "text": question},
        ]}],
    )
    print(r.content[-1].text)

ask("What was the operating margin in Q4?")
ask("How much did headcount grow?")
client.files.delete(uploaded.id)
