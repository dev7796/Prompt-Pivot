"""Level 2b build: document Q&A with sources.

Upload a PDF once, answer only from it, and print the page number after every claim.
The one-sentence system prompt ("If the document does not contain the answer, say so") is the
cheapest defence against a confident wrong answer. See test/README.md for what happened when
we tried to make Claude invent a remote-work stipend the handbook does not contain.
"""
import anthropic
client = anthropic.Anthropic()

def upload_pdf(path: str) -> str:
    with open(path, "rb") as f:
        return client.files.upload(file=(path, f, "application/pdf")).id

def ask(file_id: str, question: str) -> None:
    response = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=2048,
        system="Answer only from the provided document. "
               "If the document does not contain the answer, say so.",
        messages=[{
            "role": "user",
            "content": [
                {"type": "document",
                 "source": {"type": "file", "file_id": file_id},
                 "citations": {"enabled": True}},
                {"type": "text", "text": question},
            ],
        }],
    )
    for block in response.content:
        if block.type != "text":
            continue
        print(block.text, end="")
        for c in (block.citations or []):
            print(f" [p.{c.start_page_number}]", end="")
    print()

doc = upload_pdf("employee_handbook.pdf")
ask(doc, "How many vacation days do new employees get?")
ask(doc, "Is there a remote-work stipend?")
