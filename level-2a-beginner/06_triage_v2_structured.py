"""2.2 The finished triage bot: examples teach the decision, the schema guarantees the shape."""
from enum import Enum
from pydantic import BaseModel
import anthropic

client = anthropic.Anthropic()

class Category(str, Enum):
    BILLING = "BILLING"
    BUG = "BUG"
    OTHER = "OTHER"

class TriageResult(BaseModel):
    category: Category
    reason: str          # one short sentence, not step-by-step reasoning

SYSTEM = """Classify each support message as BILLING, BUG or OTHER.

<examples>
<example><message>I was charged twice this month.</message><label>BILLING</label></example>
<example><message>The export button crashes the app.</message><label>BUG</label></example>
<example><message>Do you have an office in Berlin?</message><label>OTHER</label></example>
</examples>"""

def triage(message: str) -> TriageResult:
    response = client.messages.parse(
        model="claude-opus-5-5",
        max_tokens=200,
        system=SYSTEM,
        messages=[{"role": "user", "content": f"<message>{message}</message>"}],
        output_format=TriageResult,
    )
    if response.stop_reason != "end_turn":      # refusal or max_tokens: no trustworthy JSON
        raise RuntimeError(f"stopped early: {response.stop_reason}")
    return response.parsed_output

for m in ["I was charged twice this month.",
          "The export button crashes the app.",
          "Do you have an office in Berlin?"]:
    result = triage(m)
    print(result.category.value, " ", result.reason)
    if result.category == Category.BILLING:
        print("   -> billing queue")
