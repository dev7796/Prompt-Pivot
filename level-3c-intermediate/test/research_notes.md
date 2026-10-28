## MCP definition and purpose

MCP (Model Context Protocol) is an open-source standard for connecting AI applications (e.g., Claude, ChatGPT) to external systems: data sources (local files, databases), tools (search engines, calculators) and workflows (specialized prompts). Official docs compare it to a "USB-C port for AI applications."
Architecture: developers either expose data through MCP servers or build AI applications (MCP clients) that connect to those servers.
Problem solved: the "N×M integration problem" — each client and server implements the protocol once, so integrations go from N×M to N+M.
Sources:
- https://modelcontextprotocol.io/docs/2026-07-28/getting-started/intro
- https://www.anthropic.com/news/model-context-protocol
- https://www.databricks.com/blog/what-is-model-context-protocol

## MCP origin: Anthropic, November 2024

Anthropic introduced and open-sourced MCP on November 25, 2024. The launch included the spec and SDKs, local MCP server support in Claude Desktop, and an open-source repository of servers (Google Drive, Slack, GitHub, Git, Postgres, Puppeteer). It is MIT-licensed. SDKs exist for TypeScript, Python, Java, Kotlin, C#, Go, PHP, Ruby, Rust, Swift and others.
Sources:
- https://www.anthropic.com/news/model-context-protocol
- https://en.wikipedia.org/wiki/Model_Context_Protocol
- https://tech-insider.org/ie/model-context-protocol-mcp-update-2026/

## MCP governance: Linux Foundation AAIF

On Dec 9, 2025, Anthropic donated MCP to the Agentic AI Foundation (AAIF), a directed fund under the Linux Foundation. The AAIF was co-founded by Anthropic, Block and OpenAI, with support from Google, Microsoft, AWS, Cloudflare and Bloomberg. Its founding projects are MCP, Block's goose and OpenAI's AGENTS.md. The existing maintainers still make protocol decisions through the SEP process; the Linux Foundation says it will not dictate technical direction. One secondary source names AWS, Bloomberg, Cloudflare, Google and Microsoft as platinum members, with Cisco, IBM, Oracle, SAP, Snowflake and SUSE also listed as members (I haven't checked this against aaif.io).
Sources:
- https://blog.modelcontextprotocol.io/posts/2025-12-09-mcp-joins-agentic-ai-foundation/
- https://www.linuxfoundation.org/press/linux-foundation-announces-the-formation-of-the-agentic-ai-foundation
- https://blckalpaca.at/en/knowledge-base/ai-agents/a2a-protocol-basics/linux-foundation-aaif-bedeutung

## Major vendors supporting MCP

- Microsoft: added MCP to Copilot Studio on Mar 19, 2025; also in VS Code with GitHub Copilot (since v1.102), Semantic Kernel, Azure OpenAI, and Windows/Foundry integrations.
- OpenAI: adopted MCP in March 2025 across the Agents SDK, Responses API and ChatGPT desktop; added MCP to ChatGPT apps in Sept 2025; co-developed the MCP Apps UI extension.
- Google / Google DeepMind: adopted MCP; Gemini CLI supports local and remote servers.
- AWS, Cloudflare (MCP server hosting), Bloomberg: AAIF supporters.
- Other clients: Cursor, Goose, VS Code. MCP Apps launch partners: Amplitude, Asana, Box, Canva, Figma, monday.com, Slack, Salesforce and others.
Sources:
- https://tech-insider.org/ie/model-context-protocol-mcp-update-2026/
- https://en.wikipedia.org/wiki/Model_Context_Protocol
- https://www.pento.ai/blog/a-year-of-mcp-2025-review
- https://www.digidop.com/blog/mcp-ai-revolution
- https://workos.com/blog/everything-your-team-needs-to-know-about-mcp-in-2026

## MCP adoption stats and 2026 spec

- SDK downloads: about 100K a month at launch, reaching about 97M a month by March 2026 (reported in several secondary sources).
- Servers: more than 10,000 active public servers (Anthropic, Dec 2025); about 15,930 across four major registries (mid-2026 estimate).
- Spec: the 2026-07-28 specification is the largest revision so far. It makes the protocol stateless and moves some features into extensions.
- Security caveat: independent scans found exploitable flaws in many public servers, and the NSA and CISA have issued guidance.
- The MCP Dev Summit North America (NYC, April 2026) drew about 1,200 people.
Caveat: these numbers come from secondary or blog sources, not official audits.
Sources:
- https://knak.com/blog/mcp-adoption-in-2026-what-marketers-need-to-know/
- https://tech-insider.org/ie/model-context-protocol-mcp-update-2026/
- https://www.digidop.com/blog/mcp-ai-revolution
- https://en.wikipedia.org/wiki/Model_Context_Protocol

