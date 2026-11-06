"""Level 3c, section 3.11: tools agents use well. The 3a weather tool, before and after.

    python 04_tool_design.py               # five questions, both tool sets, side by side

Before: three drawers that look alike, one-sentence descriptions copied from the API, a 40-field
return. After: one tool, a description that says when to use it and what it does NOT do, a
`mode` enum, a `detail` switch, and six fields back.

This runs on Bedrock too (client tools only). Swap the client line and the model id.
"""
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-opus-5-5"

BEFORE = [
    {"name": "get_current_weather", "description": "Gets current weather.",
     "input_schema": {"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]}},
    {"name": "get_forecast", "description": "Gets forecast.",
     "input_schema": {"type": "object", "properties": {"q": {"type": "string"}, "days": {"type": "integer"}}, "required": ["q"]}},
    {"name": "get_weather_by_coordinates", "description": "Gets weather by lat/lon.",
     "input_schema": {"type": "object", "properties": {"lat": {"type": "number"}, "lon": {"type": "number"}}, "required": ["lat", "lon"]}},
]

AFTER = [{
    "name": "weather",
    "description": (
        "Get the weather for a location. Use mode 'current' for right now and 'forecast' for the next days. "
        "Returns temperature, condition, wind and a human-readable time; use detail='full' only when the "
        "user asks for more. Does not return historical data."
    ),
    "input_schema": {"type": "object", "properties": {
        "location": {"type": "string",
                     "description": "City and country, e.g. 'Lyon, France' or 'Austin, United States'. Coordinates as 'lat,lon' also accepted."},
        "mode": {"type": "string", "enum": ["current", "forecast"]},
        "detail": {"type": "string", "enum": ["concise", "full"], "description": "Default concise."},
    }, "required": ["location", "mode"]},
}]

QUESTIONS = [
    "Is it raining in Lyon right now?",
    "What's the weather at 48.85, 2.35?",
    "Will I need a coat in Austin this weekend?",
    "Give me everything you can about current conditions in Tokyo.",
    "Weather in Paris?",
]

for q in QUESTIONS:
    print(f"\n{q}")
    for label, tools in (("before", BEFORE), ("after", AFTER)):
        r = client.messages.create(model=MODEL, max_tokens=512, tools=tools,
                                   messages=[{"role": "user", "content": q}])
        calls = [f"{b.name}({b.input})" for b in r.content if b.type == "tool_use"]
        print(f"  {label:6}  {' + '.join(calls) or '(no tool)'}   [{r.usage.output_tokens} out]")

# Real run (test/results.json). No wrong-tool picks on either side -- Opus 5.5 is good at this.
# The measurable change: 6 calls before vs 5 after (Tokyo "everything" used two drawers before, one
# tool with detail='full' after), and richer inputs after ('Lyon, France', mode, detail) for 387 vs 417
# output tokens. The win is fewer round trips and inputs your code can trust, not fewer mistakes.
#
# The eight principles (section 3.11): choose the right tools; consolidate; namespace; return meaningful
# context; offer a verbosity switch; be token-efficient; write helpful errors; prompt-engineer the
# description. The description is the biggest lever.
