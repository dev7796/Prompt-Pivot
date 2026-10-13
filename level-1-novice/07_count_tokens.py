"""1.8 Counting tokens before you send: weigh the package before you pay for shipping."""
import anthropic

client = anthropic.Anthropic()
count = client.messages.count_tokens(
    model="claude-opus-5-5",
    system="You are a helpful assistant.",
    messages=[{"role": "user", "content": "Hello, world"}],
)
print(count.input_tokens)
