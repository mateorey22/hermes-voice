"""
Hermes Voice — Real-time voice interface for Hermes Agent
Uses Gemini 3.1 Flash Live via google-genai SDK, with Hermes API for decision-making.
"""

import asyncio
import json
import os
import logging
import aiohttp
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
HERMES_API_URL = os.getenv("HERMES_API_URL", "http://localhost:8642")
HERMES_API_KEY = os.getenv("HERMES_API_KEY", "YOUR_HERMES_API_KEY_HERE")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "7861"))

GEMINI_MODEL = "gemini-3.1-flash-live-preview"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hermes-voice")

app = FastAPI(title="Hermes Voice")

# Gemini client
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# ── System prompt: Gemini acts as voice receptionist for Hermes ──
SYSTEM_PROMPT = """Tu es Hermes Voice, l'interface vocale de Hermes — un assistant IA.

TON RÔLE: Tu es un réceptionniste vocal. Tu gères la conversation de manière naturelle et chaleureuse, mais pour tout vrai travail (recherche, opérations fichier, codage, tâches système, planification, recherches web), tu appelles la fonction ask_hermes pour déléguer à l'agent Hermes principal.

RÈGLES:
- Parle naturellement, comme une vraie personne. Garde les réponses COURTES (1-3 phrases max).
- Pour les salutations, small talk, clarifications — gère toi-même, pas besoin d'appeler Hermes.
- Pour TOUT ce qui nécessite une action, une recherche, des outils — appelle ask_hermes.
- Quand tu reçois une réponse de Hermes, relaie-la de manière conversationnelle — ne la lis pas mot pour mot, reformule pour l'oral.
- L'utilisateur parle français, réponds en français.
- Ne dis jamais "Je vais demander à Hermes" — fais-le de manière fluide. L'utilisateur doit avoir l'impression de parler à une seule entité.
- En cas de doute, appelle Hermes.
- Sois concis. C'est de la voix, pas du texte. Personne ne veut un monologue de 30 secondes.

EXEMPLES:
User: "Salut" → Salue-les chaleureusement.
User: "C'est quoi la relativité restreinte?" → Appelle ask_hermes.
User: "Crée un fichier avec les notes de physique" → Appelle ask_hermes.
User: "Il pleut dehors?" → Appelle ask_hermes (besoin de recherche web).
User: "Répète ça" → Répète, pas besoin de Hermes.
"""


async def call_hermes_api(message: str) -> str:
    """Call the Hermes API server to get a response from the main agent."""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {HERMES_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "messages": [{"role": "user", "content": message}],
                "stream": False
            }
            async with session.post(
                f"{HERMES_API_URL}/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=120)
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("choices", [{}])[0].get("message", {}).get("content", "Pas de réponse d'Hermes.")
                else:
                    text = await resp.text()
                    logger.error(f"Hermes API error {resp.status}: {text}")
                    return f"Erreur de connexion à Hermes ({resp.status})."
    except asyncio.TimeoutError:
        return "Hermes prend trop de temps à répondre. Réessaie."
    except Exception as e:
        logger.error(f"Hermes API call failed: {e}")
        return f"Erreur de connexion à Hermes: {str(e)}"


# ── Gemini Live session handler ──

async def gemini_live_session(client_ws: WebSocket):
    """Bridge between browser WebSocket and Gemini Live API via GenAI SDK."""
    await client_ws.accept()
    logger.info("Client connected")

    # Function declaration for Gemini
    tools = genai.types.Tool(function_declarations=[
        genai.types.FunctionDeclaration(
            name="ask_hermes",
            description="Demande à l'agent Hermes de l'aide pour des tâches, recherches, opérations fichier, codage, planification, ou toute action nécessitant des outils. Utilise ceci pour tout vrai travail.",
            parameters=genai.types.Schema(
                type=genai.types.Type.OBJECT,
                properties={
                    "query": genai.types.Schema(
                        type=genai.types.Type.STRING,
                        description="La question ou tâche à envoyer à Hermes"
                    )
                },
                required=["query"]
            )
        )
    ])

    config = {
        "response_modalities": ["AUDIO"],
        "speech_config": genai.types.SpeechConfig(
            voice_config=genai.types.VoiceConfig(
                prebuilt_voice_config=genai.types.PrebuiltVoiceConfig(
                    voice_name="Aoede"
                )
            )
        ),
        "system_instruction": genai.types.Content(
            parts=[genai.types.Part(text=SYSTEM_PROMPT)]
        ),
        "tools": [tools],
    }

    try:
        async with gemini_client.aio.live.connect(
            model=GEMINI_MODEL, config=config
        ) as session:
            logger.info("Connected to Gemini 3.1 Flash Live")

            # Send ready signal
            await client_ws.send_json({"type": "ready"})

            # Track if we're waiting for Hermes response
            pending_hermes = {}

            async def client_to_gemini():
                """Forward audio/data from browser to Gemini."""
                try:
                    while True:
                        data = await client_ws.receive_json()
                        msg_type = data.get("type")

                        if msg_type == "audio":
                            audio_b64 = data.get("data", "")
                            import base64
                            audio_bytes = base64.b64decode(audio_b64)
                            await session.send_realtime_input(
                                audio=genai.types.Blob(
                                    data=audio_bytes,
                                    mime_type="audio/pcm;rate=16000"
                                )
                            )

                        elif msg_type == "end":
                            break

                except WebSocketDisconnect:
                    logger.info("Client disconnected")
                except Exception as e:
                    logger.error(f"Client->Gemini error: {e}")

            async def gemini_to_client():
                """Forward responses from Gemini to browser."""
                try:
                    async for response in session.receive():
                        # Server content (audio/text response)
                        if response.server_content:
                            sc = response.server_content

                            if sc.model_turn:
                                for part in sc.model_turn.parts:
                                    if part.inline_data:
                                        import base64
                                        audio_b64 = base64.b64encode(
                                            part.inline_data.data
                                        ).decode("ascii")
                                        await client_ws.send_json({
                                            "type": "audio",
                                            "data": audio_b64,
                                            "mimeType": getattr(
                                                part.inline_data,
                                                "mime_type",
                                                "audio/pcm;rate=24000"
                                            )
                                        })
                                    if part.text:
                                        await client_ws.send_json({
                                            "type": "text",
                                            "data": part.text
                                        })

                            if sc.turn_complete:
                                await client_ws.send_json({
                                    "type": "turn_complete"
                                })

                        # Function call
                        if response.tool_call:
                            for fc in response.tool_call.function_calls:
                                if fc.name == "ask_hermes":
                                    query = fc.args.get("query", "")
                                    logger.info(f"Hermes call: {query[:100]}")

                                    await client_ws.send_json({
                                        "type": "hermes_call",
                                        "query": query
                                    })

                                    result = await call_hermes_api(query)

                                    # Send result back to Gemini
                                    tool_response = genai.types.LiveServerToolCall(
                                        function_responses=[
                                            genai.types.FunctionResponse(
                                                id=fc.id,
                                                name="ask_hermes",
                                                response={"result": result}
                                            )
                                        ]
                                    )
                                    await session.send_tool_response(
                                        function_responses=[
                                            genai.types.FunctionResponse(
                                                id=fc.id,
                                                name="ask_hermes",
                                                response={"result": result}
                                            )
                                        ]
                                    )

                                    await client_ws.send_json({
                                        "type": "hermes_response",
                                        "data": result
                                    })

                except Exception as e:
                    logger.error(f"Gemini->Client error: {e}")

            # Run both directions concurrently
            done, pending = await asyncio.wait(
                [
                    asyncio.create_task(client_to_gemini()),
                    asyncio.create_task(gemini_to_client())
                ],
                return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()

    except Exception as e:
        logger.error(f"Gemini session error: {e}")
        try:
            await client_ws.send_json({"type": "error", "message": str(e)})
        except:
            pass
    finally:
        logger.info("Session ended")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await gemini_live_session(ws)


@app.get("/")
async def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "hermes_api": HERMES_API_URL, "model": GEMINI_MODEL}


# Mount static files
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


if __name__ == "__main__":
    import uvicorn
    import ssl

    cert_path = Path(__file__).parent / "certs" / "cert.pem"
    key_path = Path(__file__).parent / "certs" / "key.pem"

    if cert_path.exists() and key_path.exists():
        uvicorn.run(app, host=HOST, port=PORT, ssl_certfile=str(cert_path), ssl_keyfile=str(key_path))
    else:
        uvicorn.run(app, host=HOST, port=PORT)
