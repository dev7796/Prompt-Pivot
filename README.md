# Prompt & Pivot — Building AI Agents with Claude

Code for every lesson on the **AI: Prompt & Pivot** YouTube channel. One folder per video, named
by level. Each folder has its own README with the file-by-section table, setup, and things to try.

| Folder | Video | Status |
|---|---|---|
| `level-1-novice/` | Talk to Claude: the Messages API, tokens, system prompts, the chatbot | published |
| `level-2a-beginner/` | Make Claude Reliable: prompt engineering and structured outputs | published |
| `level-2b-beginner/` | Documents, Images and Proof: PDFs, citations, the Files API | published |
| `level-3a-intermediate/` | Give Claude Hands: tool use and the agent loop | published |
| `level-3b-intermediate/` | Steering the Tools: tool choice, parallel, strict, SDK runner | published |
| `level-3c-intermediate/` | Built-in Tools and a Research Assistant | in production |
| `level-4a-advanced/` | Think Better: thinking and prompt caching | planned |
| `level-4b-advanced/` | Memory and the Long Game: batches, memory, compaction | planned |
| `level-4c-advanced/` | Computer Use and MCP | planned |
| `level-4d-advanced/` | Agent SDK, Skills and Claude Code | planned |
| `level-5a-expert/` | The Agent Design Patterns | planned |
| `level-5b-expert/` | Multi-Agent Systems and Evals | planned |
| `level-5c-expert/` | Guardrails and Shipping | planned |

## Running any example

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install anthropic pydantic
export ANTHROPIC_API_KEY="sk-ant-..."     # get one at platform.claude.com; never commit it
cd level-1-novice && python 05_chat.py
```

Model IDs change. If a script fails with `not_found_error`, copy the current ID from the
[models page](https://docs.claude.com/en/docs/about-claude/models/overview) or run `client.models.list()`.

## Conventions
- Files are numbered in the order they appear in the video: `01_`, `02_`, ...
- Every file runs on its own and prints something.
- Code is kept identical to what is typed on screen, so you can pause the video and compare.
