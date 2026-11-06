"""Level 4a, section 4.1: extended thinking, and seeing it.

    python 01_thinking.py                 # adaptive thinking, summarized display (the on-screen code)
    python 01_thinking.py --omitted       # same request, display omitted: compare output tokens
    python 01_thinking.py --hard          # a question with a trap, so the meter has a reason to move
    python 01_thinking.py --legacy        # the three 400s: enabled/disabled on Opus 5.5, adaptive on Haiku 4.5

On Opus 5.5 (and Sonnet 5.5, Fable, Mythos) thinking is ADAPTIVE: you switch it on, Claude decides how
much to use, and max_tokens is the ceiling for thinking plus answer together. The older enabled/disabled
modes with budget_tokens are a 400 on these models, and still the only mode on Haiku 4.5.

display controls what you see of it: "summarized" (a short summary of the reasoning), "omitted" (the
block comes back with an empty thinking field and a signature). Either way the reasoning happened.
"""
import sys
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-opus-5-5"
HAIKU = "claude-haiku-4-5-20251001"     # on Bedrock: us.anthropic.claude-haiku-4-5-20251001-v1:0 (the short alias is gone)

GCD = "What is the GCD of 1071 and 462?"
HARD = ("A bat and a ball cost $1.10 in total. The bat costs $1.00 more than the ball. Then the shop raises "
        "the ball's price by 50% and lowers the bat's by 10%. What is the new total, to the cent? "
        "Answer with the number only.")                      # truth: ball 0.05 -> 0.075, bat 1.05 -> 0.945, total 1.02


def ask(question, display="summarized", model=MODEL):
    response = client.messages.create(
        model=model,
        max_tokens=16000,
        thinking={"type": "adaptive", "display": display},
        messages=[{"role": "user", "content": question}],
    )
    for block in response.content:
        if block.type == "thinking":
            print("THINKING:", block.thinking or "(omitted; signature present)")
        elif block.type == "text":
            print("ANSWER:", block.text)
    print(f"blocks={[b.type for b in response.content]}  output tokens={response.usage.output_tokens}")
    return response


def legacy():
    """The modes the guide's model-row table says are gone on Opus 5.5, and the one Haiku still needs."""
    for thinking in ({"type": "enabled", "budget_tokens": 4000}, {"type": "disabled"}):
        try:
            client.messages.create(model=MODEL, max_tokens=8000, thinking=thinking,
                                   messages=[{"role": "user", "content": GCD}])
            print(f"Opus {thinking['type']}: accepted?!")
        except anthropic.BadRequestError as e:
            print(f"Opus {thinking['type']}: 400 {e.message}")
    try:
        client.messages.create(model=HAIKU, max_tokens=4000, thinking={"type": "adaptive"},
                               messages=[{"role": "user", "content": GCD}])
        print("Haiku adaptive: accepted?!")
    except anthropic.BadRequestError as e:
        print(f"Haiku adaptive: 400 {e.message}")
    print("\nHaiku, legacy mode (the full working comes back in the thinking field):")
    r = client.messages.create(model=HAIKU, max_tokens=4000, thinking={"type": "enabled", "budget_tokens": 2000},
                               messages=[{"role": "user", "content": GCD}])
    for b in r.content:
        print(f"{b.type.upper()}: {getattr(b, 'thinking', None) or getattr(b, 'text', '')}")
    print(f"output tokens={r.usage.output_tokens}")


if "--legacy" in sys.argv:
    legacy()
else:
    q = HARD if "--hard" in sys.argv else GCD
    ask(q, display="omitted" if "--omitted" in sys.argv else "summarized")

# Real runs (test/results.json, Bedrock, 2026-10-27):
#   GCD summarized: blocks [thinking, text], one-sentence summary, answer 21 via Euclid, 140 output tokens.
#   GCD omitted:    thinking field empty, signature present, same answer, 140 output tokens. IDENTICAL.
#   Opus 5.5 had almost nothing to hide: adaptive means Claude decides, and for this question it decided
#   not to think. The 16,000 is headroom, not a plan.
#   Bat and ball, summarized: the summary shows the route (and mis-states one check: it is a window, not a
#   transcript), answer 1.02 correct, 46 output tokens. Omitted: 1.02, 58 tokens.
#   Opus enabled/disabled: 400 '"thinking.type.enabled" is not supported for this model. Use
#   "thinking.type.adaptive" and "output_config.effort" to control thinking behavior.'
#   Haiku adaptive: 400 'adaptive thinking is not supported on this model'.
#   Haiku enabled (budget 2000): full working in the thinking field, Euclid plus a verification pass, 331
#   output tokens, where Opus wrote one line.
