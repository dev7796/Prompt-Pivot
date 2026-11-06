"""Level 3c, section 3.10: web search, the first server tool.

You do not run this tool. Claude asks for a search, Anthropic's side runs it, and the results come
back inside the same response, with citations attached. Your loop never sees a tool_use for it.

    python 01_web_search.py
    python 01_web_search.py --turn2        # send the results back and ask a follow-up

Needs the Anthropic API directly: web search is not available on Amazon Bedrock (twelve attempts,
twelve "tool type not supported" refusals; see test/probe_bedrock_tools.py). Same SDK, one
different client line.
"""
import sys
import anthropic

client = anthropic.Anthropic()                       # not AnthropicBedrock, for this chapter only
MODEL = "claude-opus-5-5"

WEB_SEARCH = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 5,                                   # a budget, not a target
    "allowed_domains": ["anthropic.com", "claude.com"],
}

question = "What did Anthropic announce this week?"
r = client.messages.create(model=MODEL, max_tokens=2048, tools=[WEB_SEARCH],
                           messages=[{"role": "user", "content": question}])

# The block order, in every response that searched:
#   server_tool_use (the query) -> web_search_tool_result (the hits) -> text (with citations)
# and Opus 5.5 adds a thinking block up front without being asked.
print("blocks:", [b.type for b in r.content])
print("searches:", sum(1 for b in r.content if b.type == "server_tool_use"))
print()
for b in r.content:
    if b.type == "text":
        print(b.text, end="")
        for c in (b.citations or []):
            print(f"\n    [{c.url}]", end="")
print(f"\n\n[{r.usage.input_tokens} in / {r.usage.output_tokens} out]")

if "--turn2" in sys.argv:
    # Rule: send the assistant content back UNCHANGED, and keep the SAME tools list.
    # The thinking block is signed, and the signature covers the tools list. On the real run, dropping
    # allowed_domains on turn two was a 400: "Invalid `signature` in `thinking` block ... The `tools`
    # list differs from the one this block was created with". Stripping encrypted_content from the
    # search results is a 400 too.
    msgs = [{"role": "user", "content": question},
            {"role": "assistant", "content": r.content},
            {"role": "user", "content": "Which of those matters most for developers? One sentence."}]
    r2 = client.messages.create(model=MODEL, max_tokens=512, tools=[WEB_SEARCH], messages=msgs)
    print("\nturn 2:", "".join(b.text for b in r2.content if b.type == "text"))

# Real run (test/results.json, 2026-10-26): 1 search, 20 blocks, 8 citations all inside
# allowed_domains, 8.8 s, 23,080 in / 849 out. Web search is $10 per 1,000 searches plus tokens.
