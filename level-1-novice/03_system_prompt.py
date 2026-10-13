"""1.4 The system prompt: the job description on the chef's door."""
import anthropic

client = anthropic.Anthropic()
message = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=1024,
    system="You are a patient Python tutor. "
           "Explain with short examples.",
    messages=[{"role": "user",
               "content": "What is a list comprehension?"}],
)
print(message.content[0].text)
