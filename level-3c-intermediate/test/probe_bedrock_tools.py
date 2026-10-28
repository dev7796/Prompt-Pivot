"""Does Bedrock accept ANY Anthropic server-tool type for Claude? Tries every known version
against two model IDs. Prints one line per (model, tool type). Read-only, tiny requests."""
import anthropic

client = anthropic.AnthropicBedrock(aws_region="us-east-1", aws_profile="alps-optum", max_retries=0)
MODELS = ["us.anthropic.claude-opus-5-5", "us.anthropic.claude-haiku-4-5", "global.anthropic.claude-opus-5-5"]
TOOLS = [
    {"type": "web_search_20250305", "name": "web_search"},
    {"type": "web_search_20260209", "name": "web_search"},
    {"type": "web_fetch_20250910", "name": "web_fetch"},
    {"type": "web_fetch_20260318", "name": "web_fetch"},
    {"type": "code_execution_20250522", "name": "code_execution"},
    {"type": "code_execution_20250825", "name": "code_execution"},
]
for m in MODELS:
    for t in TOOLS:
        try:
            r = client.beta.messages.create(
                model=m, max_tokens=50, tools=[t],
                betas=["web-fetch-2025-09-10", "code-execution-2025-08-25"],
                messages=[{"role": "user", "content": "Reply with the single word ok."}],
            )
            print(f"OK    {m:40s} {t['type']:28s} -> {r.stop_reason}")
        except Exception as e:
            msg = str(e).replace("\n", " ")
            print(f"FAIL  {m:40s} {t['type']:28s} -> {type(e).__name__}: {msg[:140]}")
