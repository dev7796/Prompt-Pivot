"""2.1 The naive triage bot: correct answers, none of them machine-readable."""
import anthropic

client = anthropic.Anthropic()

def triage(message: str) -> str:
    prompt = f"What category is this support message?\n\n{message}"
    response = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text

for m in ["I was charged twice this month.",
          "The export button crashes the app.",
          "Do you have an office in Berlin?"]:
    print(triage(m))
