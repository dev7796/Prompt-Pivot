"""1.5 Multi-turn conversations.  The API is a goldfish: you resend the whole history every call."""
import anthropic

client = anthropic.Anthropic()
history = []

def chat(user_text: str) -> str:
    history.append({"role": "user", "content": user_text})
    response = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=1024,
        system="You are a friendly assistant.",
        messages=history,
    )
    reply = "".join(b.text for b in response.content
                    if b.type == "text")
    # Save Claude's turn so the next call includes it
    history.append({"role": "assistant",
                    "content": response.content})
    return reply

print(chat("My name is Priya."))
print(chat("What is my name?"))   # Claude knows, because history was resent
