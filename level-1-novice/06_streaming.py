"""1.7 Streaming: text as Claude writes it."""
import anthropic

client = anthropic.Anthropic()
with client.messages.stream(
    model="claude-opus-5-5",
    max_tokens=1024,
    messages=[{"role": "user",
               "content": "Write a haiku about rivers."}],
) as stream:
    for text in stream.text_stream:     # text as it arrives
        print(text, end="", flush=True)
    final = stream.get_final_message()  # the full Message object

print("\nstop_reason:", final.stop_reason)
