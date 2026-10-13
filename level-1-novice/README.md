# Level 1 · Novice — Talk to Claude

Code from the video **Build Your First AI Agent with Claude in 20 Lines of Python**.
Each file matches one section of the lesson and runs on its own.

| File | Section | What it shows |
|---|---|---|
| `01_first_call.py` | 1.1 | The Messages API: model, max_tokens, messages |
| `02_read_response.py` | 1.2 | Loop over `content`, check `block.type`, read `stop_reason` and `usage` |
| `03_system_prompt.py` | 1.4 | The system prompt as a job description |
| `04_multi_turn.py` | 1.5 | The API is stateless; resend the history every call |
| `05_chat.py` | 1.6 | The complete command-line chatbot |
| `06_streaming.py` | 1.7 | `messages.stream()` and `get_final_message()` |
| `07_count_tokens.py` | 1.8 | `messages.count_tokens()` |

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install anthropic
export ANTHROPIC_API_KEY="sk-ant-..."      # from the Claude Console; never commit it
python 05_chat.py
```

## Try it
- Change the system prompt in `05_chat.py` (a pirate, a strict reviewer) and see the whole tone change.
- Tell the chatbot your name, then ask it back. Then comment out the `history.append(... "assistant" ...)` line and see what breaks.
- Set `max_tokens=20` and watch `stop_reason` flip to `max_tokens`.
- Watch the input-token count climb every turn. That growth is what Level 4 fixes.
