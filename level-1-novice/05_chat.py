"""1.6 Build it: a command-line chatbot.  Run: python 05_chat.py"""
import anthropic

client = anthropic.Anthropic()
history = []
print("Chat with Claude. Type 'quit' to exit.")

while True:
    user_text = input("you> ").strip()
    if user_text.lower() in {"quit", "exit"}:
        break
    history.append({"role": "user", "content": user_text})
    response = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=2048,
        system="You are a concise, helpful assistant.",
        messages=history,
    )
    history.append({"role": "assistant",
                    "content": response.content})
    for block in response.content:
        if block.type == "text":
            print("claude>", block.text)
    print(f"  [{response.usage.input_tokens} in / "
          f"{response.usage.output_tokens} out]")
