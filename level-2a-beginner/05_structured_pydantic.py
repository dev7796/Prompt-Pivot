"""2.2 Structured outputs, the easy way: Pydantic + messages.parse()."""
from pydantic import BaseModel
import anthropic

client = anthropic.Anthropic()

class ContactInfo(BaseModel):
    name: str
    email: str
    plan_interest: str
    demo_requested: bool

response = client.messages.parse(              # parse(), not create()
    model="claude-opus-5-5",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": "Extract: John Smith (john@example.com) wants the "
                   "Enterprise plan and asked for a demo next Tuesday.",
    }],
    output_format=ContactInfo,
)
contact = response.parsed_output              # a validated ContactInfo object
print(contact.name, contact.email, contact.demo_requested)
