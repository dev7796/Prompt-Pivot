"""2.1 Long documents first, question last; quote before you answer."""
import anthropic

client = anthropic.Anthropic()
q3_text = "...Q3 gross margin was 41%..."
q4_text = "...Q4 gross margin rose to 44%..."

prompt = f"""<documents>
  <document>
    <source>q3_report.pdf</source>
    <document_content>{q3_text}</document_content>
  </document>
  <document>
    <source>q4_report.pdf</source>
    <document_content>{q4_text}</document_content>
  </document>
</documents>

First, copy the quotes most relevant to the question into <quotes> tags.
Then answer the question using only those quotes, inside <answer> tags.

Question: How did gross margin change from Q3 to Q4?"""

response = client.messages.create(
    model="claude-opus-5-5", max_tokens=500,
    messages=[{"role": "user", "content": prompt}],
)
print(response.content[0].text)
