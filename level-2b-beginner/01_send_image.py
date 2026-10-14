"""Level 2b, section 2.3: send one image and ask about it.

Content is a list now. Each item is a block: an image block, then a text block.
Run from this folder so chart.png resolves (it is in test/assets/; copy or symlink it here).
"""
import base64, anthropic
client = anthropic.Anthropic()

with open("chart.png", "rb") as f:
    image_b64 = base64.standard_b64encode(f.read()).decode()

message = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {"type": "image",
             "source": {"type": "base64", "media_type": "image/png",
                        "data": image_b64}},
            {"type": "text", "text": "What trend does this chart show?"},
        ],
    }],
)
# Level 1 golden rule: never assume block 0 is text. On Opus 5.5 the first block
# can be a thinking block; the answer is the last block.
print(message.content[-1].text)
