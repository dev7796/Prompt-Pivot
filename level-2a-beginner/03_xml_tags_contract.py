"""2.1 XML tags keep instructions, context and input apart, and give Claude a way out."""
import anthropic

client = anthropic.Anthropic()

contract_text = "The tenant may keep one cat. Rent is due on the 1st."   # in real use: open("contract.txt").read()
question = "Can the tenant keep a dog?"

prompt = f"""<instructions>
Answer the question using only the contract below.
If the contract does not say, answer "Not specified."
</instructions>

<contract>
{contract_text}
</contract>

<question>{question}</question>"""

response = client.messages.create(
    model="claude-opus-5-5", max_tokens=200,
    messages=[{"role": "user", "content": prompt}],
)
print(response.content[0].text)   # -> Not specified.
