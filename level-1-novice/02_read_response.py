"""1.2 Reading the response safely.  The golden rule: loop over content, check block.type."""
import anthropic

client = anthropic.Anthropic()
message = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello, Claude"}],
)

for block in message.content:
    if block.type == "text":
        print(block.text)

print("stopped because:", message.stop_reason)
print("tokens in/out:",
      message.usage.input_tokens,
      message.usage.output_tokens)
