"""Level 3b, section 3.8: strict tools, guaranteed-valid arguments.

"strict": True uses the same constrained decoding as structured outputs (Level 2a), applied to
the tool's input: right types, required fields present, enum values from the list, nothing extra.
It guarantees SHAPE, not meaning: which room is "the big one" is still the model's judgement.

    python 03_strict_tools.py             # one call each, strict off and on
    python 03_strict_tools.py --trials 5  # repeat, looking for a divergence
"""
import sys
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-opus-5-5"

SCHEMA = {
    "type": "object",
    "properties": {
        "room": {"type": "string", "enum": ["Everest", "K2", "Denali"]},
        "attendees": {"type": "integer"},                 # integer, not number
        "date": {"type": "string", "format": "date"},     # ISO: 2026-10-23
    },
    "required": ["room", "attendees", "date"],
    "additionalProperties": False,                        # the fence: nothing you didn't ask for
}
SLOPPY = "Book the big room for a dozen of us a week from Friday."
SYSTEM = "You book meeting rooms. Today is Wednesday 2026-10-14. Everest is the largest room."


def book(strict: bool):
    tool = {"name": "book_meeting", "description": "Book a meeting room for a number of attendees.",
            "input_schema": SCHEMA}
    if strict:
        tool["strict"] = True
    r = client.messages.create(model=MODEL, max_tokens=1024, tools=[tool], system=SYSTEM,
                               messages=[{"role": "user", "content": SLOPPY}])
    tu = next(b for b in r.content if b.type == "tool_use")
    return {k: (v, type(v).__name__) for k, v in tu.input.items()}


if __name__ == "__main__":
    n = int(sys.argv[sys.argv.index("--trials") + 1]) if "--trials" in sys.argv else 1
    for i in range(n):
        for strict in (False, True):
            print(f"trial {i}  strict={strict!s:5}  {book(strict)}")

# Real runs (test/results.json, 5 trials each): every call, strict or not, returned
#   {"room": "Everest", "attendees": 12, "date": "2026-10-23"} with attendees as int.
# No divergence. On a strong model with a small schema, strict changes nothing you can SEE.
# What it changes is the guarantee: without strict you got an integer because the model is good;
# with strict, because anything else cannot be generated. A track record vs a contract.
#
# Limits: the structured-outputs JSON Schema subset (no minimum/maximum/pattern, no recursion);
# at most 20 strict tools, 24 optional parameters and 16 union-typed parameters per request.
# Never put sensitive data in a schema: it goes to the model as text.
# Turn it on where a wrong type would hurt (a database, a payment, a calendar); it buys little
# for a tool that takes a free-text query.
