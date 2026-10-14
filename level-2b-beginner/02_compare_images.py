"""Level 2b, section 2.3: two labelled images in one message.

A text block before each image gives Claude a name to refer to ("Image 1", "Image 2").
Ask it to say where it read each number so the answer is checkable against the chart.
"""
import base64, anthropic
client = anthropic.Anthropic()

def load_image(path: str) -> str:
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode()

def img(path: str) -> dict:
    return {"type": "image", "source": {"type": "base64",
            "media_type": "image/png", "data": load_image(path)}}

message = client.messages.create(
    model="claude-opus-5-5", max_tokens=400,
    messages=[{"role": "user", "content": [
        {"type": "text", "text": "Image 1: Q3"},
        img("chart_q3.png"),
        {"type": "text", "text": "Image 2: Q4"},
        img("chart_q4.png"),
        {"type": "text", "text": "Which region grew the most from Image 1 "
                                 "to Image 2, and by roughly how much? "
                                 "Say where you read each number."},
    ]}],
)
print(message.content[-1].text)  # last block is the text; block 0 may be thinking
