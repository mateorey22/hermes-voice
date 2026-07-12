# Gemini Live App — React/Vite Frontend

Full-featured voice conversation interface using Gemini Live API directly from the browser.

## Features

- Real-time voice conversation with Gemini Live
- Camera/visual analysis (multi-camera support)
- Hermes Agent integration (delegates complex tasks via function calling)
- MCP server support (connect to Agent Zero via SSE)
- Webhook/n8n tool connections
- Custom personality/voice settings
- Immersive SVG visualizer (gooey filter)

## Architecture

```
Browser (React) → @google/genai SDK → Gemini Live API (direct, streaming)
                  ↓ function call: ask_hermes
                  Vite proxy /hermes → Hermes API (localhost:8642)
                  ↓ MCP tools
                  Vite proxy /mcp → Agent Zero (Tailscale HTTPS)
```

## Setup

1. `npm install`
2. Copy `.env` and set your Gemini API key
3. Generate SSL certs in `certs/`
4. `npm run dev` — runs on https://0.0.0.0:3000

## Vite Proxy Config

- `/hermes/*` → `http://127.0.0.1:8642` (Hermes API, avoids mixed-content)
- `/mcp/*` → `https://agentzero.tail335dec.ts.net` (Agent Zero MCP, Tailscale)

## Settings Panel

Access via gear icon (top-right). Configure:
- Voice selection (Puck, Aoede, Charon, etc.)
- Custom personality prompt
- Gemini API key (or use .env)
- Hermes Agent IP + API key
- MCP server connections (SSE URL)
- n8n webhook tools (auto-configure from URL)

## Tech Stack

- React 19 + TypeScript
- Vite 7 (dev server with HTTPS + proxy)
- @google/genai SDK (Gemini Live)
- Tailwind CSS classes
