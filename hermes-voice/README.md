# Hermes Voice — FastAPI Backend

Real-time voice interface for Hermes Agent using Gemini Live API.

## Architecture

```
Browser (mic) → WebSocket → FastAPI → Gemini Live API (audio in/out)
                                      ↓ function call: ask_hermes
                                      Hermes Agent API (localhost:8642)
```

## Setup

1. Create venv: `python -m venv .venv && source .venv/bin/activate`
2. Install: `pip install -r requirements.txt`
3. Configure `.env` with your API keys
4. Generate SSL certs in `certs/` (required for microphone access)
5. Run: `./start.sh` or `python server.py`

## Configuration

| Var | Default | Description |
|-----|---------|-------------|
| GEMINI_API_KEY | — | Google Gemini API key |
| HERMES_API_URL | http://localhost:8642 | Hermes gateway URL |
| HERMES_API_KEY | — | Hermes API server key |
| HOST | 0.0.0.0 | Bind address |
| PORT | 7861 | Listen port |

## Model

Uses `gemini-3.1-flash-live-preview` with voice `Aoede`.

## How it works

- Browser captures mic audio (16kHz PCM) → sends via WebSocket as base64
- Server forwards to Gemini Live session
- Gemini responds with audio (24kHz PCM) → relayed to browser
- When Gemini calls `ask_hermes` function, server proxies to Hermes API
- Hermes response sent back to Gemini as tool result → Gemini relays orally
