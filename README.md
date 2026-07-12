# Hermes Voice — Complete Project Export

Two voice interfaces for Hermes Agent using Gemini Live API.

## Projects

### 1. hermes-voice/ — FastAPI Backend (port 7861)
Minimal Python server. Browser → WebSocket → FastAPI → Gemini Live.
Gemini acts as voice receptionist, delegates real work to Hermes via function calling.

### 2. gemini-live-app/ — React/Vite Frontend (port 3000)
Full-featured web app. Browser talks directly to Gemini Live via @google/genai SDK.
Supports camera, MCP servers, webhooks, custom personality, Hermes integration.

## What's Sanitized

- All API keys replaced with `YOUR_*_HERE` placeholders
- SSL certs not included (regenerate with openssl)
- node_modules not included (run npm install)
- .venv not included (run pip install)

## Quick Start

### Backend (hermes-voice)
```bash
cd hermes-voice
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# Edit .env with your keys
openssl req -x509 -newkey rsa:2048 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj '/CN=localhost'
./start.sh
# → https://0.0.0.0:7861
```

### Frontend (gemini-live-app)
```bash
cd gemini-live-app
npm install
# Edit .env with your Gemini key
openssl req -x509 -newkey rsa:2048 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes -subj '/CN=localhost'
npm run dev
# → https://0.0.0.0:3000
```

## Requirements

- Google Gemini API key (with Live API access)
- Hermes Agent running on localhost:8642 (or configure HERMES_API_URL)
- For MCP: Agent Zero accessible via Tailscale
- SSL certs required (browsers need HTTPS for mic/camera access)

## Current Deployment (Pi pegasus)

- **Backend (hermes-voice)**: port 7861, FastAPI + uvicorn
- **Frontend (gemini-live-app)**: port 3000, Vite dev server (running as root since May 29)
- **Hermes gateway**: port 8642 (Bearer auth: `YOUR_HERMES_API_KEY_HERE`)
- **Pi IP**: 192.168.1.145 (local) / 100.99.219.7 (Tailscale)

## Models

- Gemini Live: `gemini-3.1-flash-live-preview`
- Default voice: `Aoede` (backend), `Puck` (frontend, configurable)
