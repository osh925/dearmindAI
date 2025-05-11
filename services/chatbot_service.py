import os
from typing import List
from google import genai
from google.genai.types import GenerateContentConfig, Content, Part as GenaiPart
from utils.utils import fetch_chat_history, fetch_diary_by_date

# ─── INIT GENAI CLIENT ─────────────────────────────────────────────────────────
PROJECT_ID = "sc2025-test"
REGION     = "us-central1"
# CREDS      = "./sc2025-test-2612809344af.json"
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDS
## GCP Automatically detects service account (I hope so)

client = genai.Client(vertexai=True, project=PROJECT_ID, location=REGION)

# ─── BOT PERSONA & GREETING ────────────────────────────────────────────────────
SYSTEM_INSTRUCTION = (
    "You are DearMind, an empathetic art-therapy companion. "
    "Speak in a calm, encouraging tone with expertise in Psychological counseling, but be sure to maintain a friendly and buddy vibe. "
    "Recall everything the user has shared in this session."
)
STATIC_GREETING = (
    "Hello! It’s wonderful to meet you, and I’m genuinely happy you’re here. "
    "I’m here to listen and gently guide you as you express yourself through art and language. "
    "How can I support you with your feelings today?"
)

def get_initial_greeting() -> str:
    """
    Returns the one‐time greeting shown when the user first opens the chat.
    You could also fetch today's diary here and append it if desired.
    """
    return STATIC_GREETING

def chat_with_history(user_message: str, token: str) -> str:
    """
    1) Fetch prior chat turns (up to ~20) from external service.
    2) Fetch today’s diary entries and inject them into the system context.
    3) If no prior turns, return a static greeting.
    4) Otherwise start a Gemini chat with both persona+diary context and history baked in,
       then send the new user message and return the assistant’s reply.
    """
    # 1) Fetch chat history
    history_json = fetch_chat_history(token=token)

    # 2) Always fetch today’s diary and append to system context
    diaries = fetch_diary_by_date(token=token)
    diaries = []
    diary_block = "\n".join(f"- {d}" for d in diaries)
    extended_system = SYSTEM_INSTRUCTION
    if diary_block:
        extended_system += "\n\nUser's diary for today:\n" + diary_block


    # 4) Map history into GenAI Content objects
    history: List[Content] = []
    for turn in history_json:
        role = turn["role"]
        # Gemini expects "user" or "model"
        genai_role = "user" if role == "user" else "model"
        history.append(
            Content(
                role=genai_role,
                parts=[GenaiPart(text=turn["content"])]
            )
        )

    # 5) Start a new chat with persona+diary context + prior history
    chat = client.chats.create(
        model="gemini-2.0-flash",
        config=GenerateContentConfig(system_instruction=extended_system),
        history=history
    )

    # 6) Send the new user message
    response = chat.send_message(user_message)
    return response.text
