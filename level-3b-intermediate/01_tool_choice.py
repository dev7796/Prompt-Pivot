"""Level 3b, section 3.6: controlling tool choice.

tool_choice has four values:
  {"type": "auto"}                       Claude decides (default when tools are given)
  {"type": "any"}                        Claude must call some tool
  {"type": "tool", "name": "get_weather"} Claude must call this tool
  {"type": "none"}                       Claude may not call tools

Two things this script shows that the docs undersell:
  1. "any" and "tool" are a 400 on Opus 5.5 / Sonnet 5.5 / Fable / Mythos (and any model with
     manual extended thinking). The error is one line; we print it.
  2. "none" never errors, but when Claude WANTED a tool it can return ZERO content blocks
     (end_turn, 1 output token). It only answers normally when no tool was wanted, or when the
     tool results are already in the conversation. So: none at the END of a run, never the start.

    python 01_tool_choice.py
"""
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-opus-5-5"

TOOLS = [{
    "name": "get_weather",
    "description": "Get the current temperature in Celsius for a city.",
    "input_schema": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
}]
QUESTION = [{"role": "user", "content": "What's the weather in Paris?"}]


def show(label, response):
    text = "".join(b.text for b in response.content if b.type == "text")
    print(f"\n[{label}] stop_reason={response.stop_reason}  blocks={[b.type for b in response.content]}")
    if text:
        print("  text:", text)


# 1. Forcing: a 400 on the newest models.
for choice in ({"type": "tool", "name": "get_weather"}, {"type": "any"}):
    try:
        r = client.messages.create(model=MODEL, max_tokens=1024, tools=TOOLS, tool_choice=choice, messages=QUESTION)
        show(f"forced {choice['type']}", r)
    except anthropic.BadRequestError as e:
        print(f"\n[forced {choice['type']}] {e}")
        # Real run: 400 - tool_choice: type "tool" and "any" are not supported for this model.

# 2. none, on a question that wants the tool: no error, no blocks.
r = client.messages.create(model=MODEL, max_tokens=1024, tools=TOOLS, tool_choice={"type": "none"}, messages=QUESTION)
show("none, tool wanted", r)
# Real run: stop_reason=end_turn  blocks=[]  (output_tokens=1). Same with a system prompt saying
# "if you cannot use a tool, say so plainly", and same when the user asks it to explain.

# 3. none, on a question that does not want the tool: answers normally.
r = client.messages.create(model=MODEL, max_tokens=256, tools=TOOLS, tool_choice={"type": "none"},
                           messages=[{"role": "user", "content": "In one sentence, what does a weather assistant do?"}])
show("none, no tool wanted", r)

# 4. The safe use: the LAST turn of an agent run, after the tool results are already in messages.
#    Tools stay attached (cache stays warm); Claude just isn't allowed to call them.
messages = QUESTION.copy()
r = client.messages.create(model=MODEL, max_tokens=1024, tools=TOOLS, messages=messages)
messages.append({"role": "assistant", "content": r.content})
tool_use = next(b for b in r.content if b.type == "tool_use")
messages.append({"role": "user", "content": [{"type": "tool_result", "tool_use_id": tool_use.id, "content": "18 C"}]})
messages.append({"role": "user", "content": "Write the final answer for the user."})
r = client.messages.create(model=MODEL, max_tokens=1024, tools=TOOLS, tool_choice={"type": "none"}, messages=messages)
show("none, final turn", r)
# Real run: "It's **64.4°F (18°C)** in Paris right now." -- a real answer, because there was
# nothing left to fetch.

# What to do instead of forcing, on the models that refuse it:
#   - auto + a clear system-prompt instruction ("Always use get_weather for weather questions")
#   - strict tools (03_strict_tools.py), if what you wanted was valid arguments
#   - structured outputs (Level 2a), if what you wanted was a guaranteed shape
# Changing tool_choice between requests invalidates the cached message history (Level 4).
