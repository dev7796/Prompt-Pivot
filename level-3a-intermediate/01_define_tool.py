"""Level 3a, section 3.2: define a tool, then measure what it costs.

A tool definition is a name, a description, and a JSON Schema for the input. Claude never
sees the Python function; it only sees this. The description is the label on the drawer,
so write it like the docstring you'd give a new teammate (four sentences: what it does,
when to use it, what it returns, what it does NOT do).

Then the part the docs mention in one line: your tool list is prepended to every request
as system-prompt tokens. We measure it with count_tokens.
"""
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
                "city": {
                    "type": "string",
                    "description": "City name, e.g. 'Paris' or 'San Francisco, CA'",
                },
            },
            "required": ["city"],
        },
    }
]

if __name__ == "__main__":
    msg = [{"role": "user", "content": "What's the weather in Paris?"}]
    without = client.messages.count_tokens(model=MODEL, messages=msg).input_tokens
    with_tool = client.messages.count_tokens(model=MODEL, messages=msg, tools=tools).input_tokens
    print(f"without tools: {without:>4} input tokens")
    print(f"with one tool: {with_tool:>4} input tokens")
    print(f"# the tool definition is {with_tool // without}x the question")
    # Real run (see test/results.json): 18 without, 461 with. One four-sentence tool is 25x the
    # question it is attached to. Thirty tools is thousands of tokens on every turn of the loop;
    # Level 4 fixes that with prompt caching. For now, keep the tool list to what the task needs.
    #
    # Bedrock has no count_tokens. Measure with two max_tokens=1 create() calls and read
    # response.usage.input_tokens instead (that is what test/run_demos.py does).
