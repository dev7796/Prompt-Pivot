"""Level 3b, section 3.9: the SDK tool runner (beta).

@beta_tool reads a function's name, docstring and type hints and builds the tool definition:
  function name          -> "name"
  docstring, first line  -> "description"
  Args: section          -> each parameter's "description"
  type hints             -> types (str->string, int->integer, float->number, list[str]->array)
and adds "additionalProperties": false for you. Print get_weather.to_dict() to see it.

client.beta.messages.tool_runner(...) is the Level 3a loop, written for you: it calls Claude,
runs what it asks for, formats the results, appends them in one message, and loops until the
stop reason isn't tool_use. until_done() returns the final message; iterate the runner instead to
watch each turn go by.

The runner lives in the SDK's beta namespace: pin your SDK version (this was anthropic==1.13.0),
and keep the hand-written loop in your repo to compare against when the runner surprises you.

    python 04_runner.py
"""
import json
import anthropic
from anthropic import beta_tool

client = anthropic.Anthropic()
MODEL = "claude-opus-5-5"


@beta_tool
def get_weather(city: str) -> str:
    """Get the current temperature in Celsius for a city.

    Args:
        city: The city name, e.g. Paris.
    """
    return {"paris": "18 C", "tokyo": "25 C"}.get(city.lower(), "No data")


print(json.dumps(get_weather.to_dict(), indent=2))
# {"name": "get_weather", "description": "Get the current temperature in Celsius for a city.",
#  "input_schema": {"type": "object", "properties": {"city": {"type": "string",
#    "description": "The city name, e.g. Paris."}}, "required": ["city"], "additionalProperties": false}}

runner = client.beta.messages.tool_runner(
    model=MODEL, max_tokens=1024, tools=[get_weather],
    messages=[{"role": "user", "content": "Weather in Tokyo?"}],
)
final = runner.until_done()          # or: for message in runner: ...
print(final.content[-1].text)
# Real run (3.2 s, on Bedrock): "It's 25°C in Tokyo right now. I can only check the temperature,
# so I don't know about other conditions like rain or humidity."
# The description talking back, again: our docstring said "current temperature", so Claude said
# what it therefore can't say. The runner wrote the plumbing, not the behaviour.
