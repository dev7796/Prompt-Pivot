"""1.1 Your first API call.  Video: Level 1, scene "Your first API call"."""
import anthropic

client = anthropic.Anthropic()   # reads ANTHROPIC_API_KEY from the environment

message = client.messages.create(
    model="claude-opus-5-5",     # which model to use
    max_tokens=1024,             # cap on how much Claude may write
    messages=[
        {"role": "user", "content": "Hello, Claude"},
    ],
)
print(message.content[0].text)
