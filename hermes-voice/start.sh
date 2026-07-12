#!/bin/bash
# Hermes Voice — Startup script
set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Source the Gemini API key from Hermes env
if [ -f ~/.hermes/.env ]; then
  export $(grep -E '^GOOGLE_API_KEY=' ~/.hermes/.env | head -1)
  export GEMINI_API_KEY="$GOOGLE_API_KEY"
fi

if [ -z "$GEMINI_API_KEY" ]; then
  echo "ERROR: GEMINI_API_KEY not found in ~/.hermes/.env"
  exit 1
fi

export HERMES_API_URL="http://localhost:8642"
export HERMES_API_KEY="YOUR_HERMES_API_KEY_HERE"
export HOST="0.0.0.0"
export PORT="7861"

echo "═══════════════════════════════════════"
echo "  Hermes Voice — Starting..."
echo "  https://$HOST:$PORT"
echo "═══════════════════════════════════════"

exec .venv/bin/python -u server.py 2>&1 | tee /tmp/hermes-voice.log
