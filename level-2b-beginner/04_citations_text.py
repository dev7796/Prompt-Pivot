"""Level 2b, section 2.5: citations on a plain-text document.

Turn on citations with {"citations": {"enabled": True}} on the document block.
Each text block in the reply then carries a list of citation objects pointing at the
exact span of the source it came from. Answers you can check, not answers you hope are right.
"""
import anthropic
client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {"type": "document",
             "source": {"type": "text", "media_type": "text/plain",
                        "data": "The grass is green. The sky is blue."},
             "title": "Nature facts",
             "context": "A trustworthy reference document.",
             "citations": {"enabled": True}},
            {"type": "text", "text": "What color is the grass?"},
        ],
    }],
)
for block in response.content:
    if block.type == "text":
        print(block.text)
        for c in (block.citations or []):
            print("   source:", repr(c.cited_text), "from doc", c.document_index)
