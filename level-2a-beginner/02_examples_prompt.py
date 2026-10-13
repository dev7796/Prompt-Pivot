"""2.1 Multishot prompting: 3-5 relevant, diverse, clearly marked examples control the format."""
import anthropic

client = anthropic.Anthropic()

system = """Classify each support message as BILLING, BUG or OTHER.

<examples>
<example>
<message>I was charged twice this month.</message>
<label>BILLING</label>
</example>
<example>
<message>The export button crashes the app.</message>
<label>BUG</label>
</example>
<example>
<message>Do you have an office in Berlin?</message>
<label>OTHER</label>
</example>
</examples>

Reply with the label only."""

def triage(message: str) -> str:
    response = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=10,
        system=system,
        messages=[{"role": "user", "content": f"<message>{message}</message>"}],
    )
    return response.content[0].text.strip()

for m in ["I was charged twice this month.",
          "The export button crashes the app.",
          "Do you have an office in Berlin?"]:
    print(triage(m))
