"""2.1 The naive triage bot: correct answers, none of them machine-readable.

HEADS UP: as written, this script CRASHES on current models (Opus 5.5 and newer):

    AttributeError: 'ThinkingBlock' object has no attribute 'text'

response.content[0] is a thinking block, not text. That is the Level 1 golden rule
("never assume block zero is text") failing for real. It is left in on purpose because
the video shows the crash. The fix is the loop from Level 1, shown at the bottom of this file.
"""
import anthropic

client = anthropic.Anthropic()

def triage(message: str) -> str:
    prompt = f"What category is this support message?\n\n{message}"
    response = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text          # <- crashes on Opus 5.5, see docstring

for m in ["I was charged twice this month.",
          "The export button crashes the app.",
          "Do you have an office in Berlin?"]:
    print(triage(m))


# --- The fix (Level 1 golden rule): keep only the text blocks -------------------------
# def triage(message: str) -> str:
#     ...
#     return "".join(b.text for b in response.content if b.type == "text")
#
# Even fixed, the output is a paragraph with markdown headers, not a label.
# Measured on 200 messages: 0 came back as a bare label. See 02_ and 06_ for the fix.
