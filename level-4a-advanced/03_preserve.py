"""Level 4a, section 4.1: the one rule for agents. Send thinking blocks back unchanged.

    python 03_preserve.py             # the 3a loop with summarized thinking; content appended as-is
    python 03_preserve.py --tidy      # drop the thinking block before sending tool results (the thing not to do)

In an agent loop the assistant turn you append is response.content, the whole list: thinking blocks,
text, tool_use. The thinking block carries a signature; the API checks it on the next call. The rule in
the docs: if you modify or drop a signed block, you get a 400.

What we could show: in Level 3c, changing the tools list between turns broke the signature and returned
a 400 ("The tools list differs from the one this block was created with"). What we could NOT reproduce
here: deleting a thinking block. Twice (see the bottom of the file) the tidy history was accepted. The
rule stands, because the API documents it and we have one proven error; the way to be safe is the way
the loop below is written: messages.append({"role": "assistant", "content": response.content}).
"""
import sys
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-opus-5-5"
THINKING = {"type": "adaptive", "display": "summarized"}
SYSTEM = "You are a weather assistant. Use tools for live data."


def get_weather(city: str) -> str:
    fake_db = {"paris": 18, "tokyo": 25, "new york": 12}
    t = fake_db.get(city.lower())
    return f"{t} C" if t is not None else f"No data for {city}"


def celsius_to_fahrenheit(celsius: float) -> str:
    return f"{celsius * 9 / 5 + 32:.1f} F"


FUNCS = {"get_weather": get_weather, "celsius_to_fahrenheit": celsius_to_fahrenheit}
TOOLS = [
    {"name": "get_weather", "description": "Get the current temperature in Celsius for a city.",
     "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}},
    {"name": "celsius_to_fahrenheit", "description": "Convert a temperature from Celsius to Fahrenheit.",
     "input_schema": {"type": "object", "properties": {"celsius": {"type": "number"}}, "required": ["celsius"]}},
]


def run_tools(response):
    return [{"type": "tool_result", "tool_use_id": b.id, "content": FUNCS[b.name](**b.input)}
            for b in response.content if b.type == "tool_use"]


def agent(question, tidy=False, max_steps=8):
    messages = [{"role": "user", "content": question}]
    for step in range(max_steps):
        response = client.messages.create(model=MODEL, max_tokens=4000, system=SYSTEM, tools=TOOLS,
                                          thinking=THINKING, messages=messages)
        print(f"[step {step}] blocks={[b.type for b in response.content]}")
        for b in response.content:
            if b.type == "thinking" and b.thinking:
                print(f"    THINK {b.thinking}")
            elif b.type == "tool_use":
                print(f"    {b.name}({b.input})")

        content = response.content
        if tidy:                                                   # the thing not to do
            content = [b for b in response.content if b.type != "thinking"]
        messages.append({"role": "assistant", "content": content})  # as-is, when tidy is False

        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")
        messages.append({"role": "user", "content": run_tools(response)})
    return "Stopped at max_steps."


question = "Of Paris, Tokyo and New York, which is closest to 70 F right now? Convert only that one and tell me."
try:
    print(agent(question, tidy="--tidy" in sys.argv))
except anthropic.BadRequestError as e:
    print("400:", e.message)

# Real runs (test/results.json, 2026-10-27):
#   Attempt 1, "Paris in Fahrenheit": step 0 content was [tool_use] only. No thinking block existed to drop,
#   so the tidy history was identical to the honest one. Accepted.
#   Attempt 2, the question above: step 0 [tool_use x3] (all three cities at once), step 1 [thinking, text,
#   tool_use] with a real interleaved summary ("70F is about 21.1C, 3.1 off Paris, 3.9 off Tokyo, so
#   Paris"). Dropped that thinking block, sent the tool results against the tidy history: ACCEPTED, and the
#   reply came back [thinking, text]. Honest run: 3 steps, Paris, 64.4 F.
#   So on 2026-10-27 the API did not reject a deleted thinking block. It did reject a changed tools list in
#   Level 3c. Treat the content list as sealed either way; it costs nothing and the rule is documented.
#   Also: thinking appears BETWEEN tool calls only when there is a decision between them. The three-city
#   fetch had none (step 0 was pure tool_use); choosing which city to convert had one (step 1).
