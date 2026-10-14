"""Level 3a, section 3.3: one round trip, by hand.

Four steps, every time:
  1. You send the question plus the tool definitions.
  2. Claude answers with a tool_use block (stop_reason == "tool_use"). It has NOT run anything.
  3. YOU run the function.
  4. You send the result back as a tool_result, and Claude writes the final answer.

Claude never runs your code. It writes a structured request; you decide what executes.
"""
import json
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-opus-5-5"

tools = [
    {
        "name": "get_weather",
        "description": (
            "Get the current temperature for a city. Use this whenever the "
            "user asks about current weather or temperature. Returns the "
            "temperature in Celsius as a short string. Does not return "
            "forecasts; it only knows current conditions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string",
                         "description": "City name, e.g. 'Paris' or 'San Francisco, CA'"},
            },
            "required": ["city"],
        },
    }
]


def get_weather(city: str) -> str:
    """The drawer. Somewhere else in the file; Claude never opens it."""
    fake_db = {"paris": 18, "tokyo": 25, "new york": 12}
    temp = fake_db.get(city.lower())
    return f"{temp} C" if temp is not None else f"No data for {city}"


messages = [{"role": "user", "content": "What's the weather in Paris?"}]

# Step 1 and 2: Claude decides to call the tool
response = client.messages.create(
    model=MODEL, max_tokens=1024,
    tools=tools, messages=messages,
)
print(response.stop_reason)                       # "tool_use"
tool_use = next(b for b in response.content if b.type == "tool_use")
print(tool_use.name, json.dumps(tool_use.input))  # get_weather {"city": "Paris"}

# Step 3: YOU run the function
result = get_weather(**tool_use.input)

# Step 4: send the result back, then Claude writes the final answer
messages += [
    {"role": "assistant", "content": response.content},
    {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": tool_use.id, "content": result},
    ]},
]
final = client.messages.create(
    model=MODEL, max_tokens=1024,
    tools=tools, messages=messages,
)
# content[-1], not content[0]: on Opus 5.5 block 0 can be a thinking block (the Level 2a crash).
print(final.content[-1].text)
# Real run: "It's 18°C (about 64°F) in Paris right now. I can only get the current temperature,
# so I can't tell you about rain or what the forecast looks like."
# That last sentence is lifted from "Does not return forecasts" in the tool description.
# Claude read the label on the drawer and told the user what the drawer can't do.
