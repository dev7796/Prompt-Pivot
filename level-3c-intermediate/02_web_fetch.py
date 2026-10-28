"""Level 3c, section 3.10: web fetch, and the rule about where URLs come from.

    python 02_web_fetch.py                 # fetch a URL you gave it
    python 02_web_fetch.py --no-url        # ask for a page without giving the URL
    python 02_web_fetch.py --search-first  # web_search + web_fetch together

The rule: Claude can only fetch a URL that already appeared in the conversation -- in your message,
in a tool result, or in an earlier search or fetch result. A URL it writes itself is blocked. That
is an exfiltration guard: the model cannot invent an address and ship your data to it.

Needs the Anthropic API directly (not available on Bedrock).
"""
import sys
import anthropic

client = anthropic.Anthropic()
MODEL = "claude-opus-5-5"

WEB_FETCH = {"type": "web_fetch_20250910", "name": "web_fetch", "max_uses": 5,
             "citations": {"enabled": True}}
WEB_SEARCH = {"type": "web_search_20250305", "name": "web_search", "max_uses": 5}

DOCS_URL = "https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview"


def show(r):
    print("blocks:", [b.type for b in r.content])
    n_cit = 0
    for b in r.content:
        if b.type == "text":
            print(b.text, end="")
            n_cit += len(b.citations or [])
    print(f"\n\ncitations: {n_cit}   [{r.usage.input_tokens} in / {r.usage.output_tokens} out]")


if "--no-url" in sys.argv:
    # Real run: Claude wrote the docs URL itself, the tool blocked it, and Claude explained the rule
    # in its own words ("only URLs you've pasted in or that came from earlier search results").
    r = client.messages.create(model=MODEL, max_tokens=1024, tools=[WEB_FETCH], messages=[
        {"role": "user", "content": "Fetch the Anthropic tool use overview page and summarize it in three sentences."}])
elif "--search-first" in sys.argv:
    # Real run: fetch (blocked, URL not yet in the conversation) -> search -> fetch (works).
    # The search result put the URL into the conversation, which made it fair game. 17.3 s, 6 citations.
    r = client.messages.create(model=MODEL, max_tokens=4096, tools=[WEB_SEARCH, WEB_FETCH], messages=[
        {"role": "user", "content": "Find Anthropic's 'Building effective agents' article, fetch it, "
                                    "and tell me the two core patterns it names. Cite the page."}])
else:
    # Real run: fetched, 16 blocks, 6 citations, 6.4 s. Claude also noticed the URL now redirects.
    r = client.messages.create(model=MODEL, max_tokens=2048, tools=[WEB_FETCH], messages=[
        {"role": "user", "content": f"Fetch {DOCS_URL} and summarize it in three sentences."}])

show(r)

# Two more guards from the docs, both worth knowing:
#   - a fetched PDF comes back as base64 and is processed like an attached PDF (Level 2b page citations apply)
#   - a URL that looks like it carries a credential (a token in the query string) is refused unless it
#     came from your system prompt or your own message
# Web fetch has no per-call fee; you pay for the tokens of what it brings back.
