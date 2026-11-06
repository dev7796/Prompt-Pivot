"""Level 4a, section 4.1: how hard Claude works. output_config.effort.

    python 02_effort.py              # low vs high on the bat-and-ball question, side by side
    python 02_effort.py "Design a sharding scheme for a 2 TB orders table."

effort is a dial on adaptive thinking: low | medium | high | xhigh | max. It is not a token budget; it
tells Claude how much reasoning the question deserves, and Claude still decides. The on-screen code:

    response = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=32000,
        output_config={"effort": "high"},   # low | medium | high | xhigh | max
        messages=[{"role": "user", "content": "Design a sharding scheme for ..."}],
    )
"""
import sys
import time
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-opus-5-5"

HARD = ("A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. Then the shop raises "
        "the ball's price by 50% and lowers the bat's by 10%. What is the new total, to the cent? "
        "Answer with the number only.")
question = sys.argv[1] if len(sys.argv) > 1 else HARD

for level in ("low", "high"):
    t0 = time.time()
    response = client.messages.create(
        model=MODEL,
        max_tokens=32000,
        output_config={"effort": level},
        thinking={"type": "adaptive", "display": "omitted"},
        messages=[{"role": "user", "content": question}],
    )
    answer = "".join(b.text for b in response.content if b.type == "text")
    print(f"effort={level:<4}  output tokens={response.usage.output_tokens:<4}  {time.time() - t0:.1f}s  -> {answer[:120]}")

# Real runs (test/results.json, 2026-10-27), bat and ball: low 44 output tokens, high 55, both 1.02, both
# about 1.2 s. Eleven tokens apart. On a question this size the dial has nothing to turn; it earns its
# keep on long design questions, where high and xhigh spend real tokens and low gives you the sketch.
# The GCD: low 140, high 140. Same as every other mode. Opus 5.5 does not think about the GCD.
