from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel, Field
from services.chatbot_service import chat_with_history, get_initial_greeting
from utils.auth import extract_bearer_token

router = APIRouter()

class ChatRequest(BaseModel):
    message: str = Field(..., description="User's message text")

class ChatResponse(BaseModel):
    reply: str = Field(..., description="Assistant's response")

@router.get("/chat/init", response_model=ChatResponse)
async def init_chat():
    """
    Called when the chat UI first loads.
    Returns the static greeting (and any initial context).
    """
    try:
        greeting = get_initial_greeting()
        return ChatResponse(reply=greeting)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest, request: Request):
    """
    Called whenever the user sends a new message.
    """
    try:
        token = extract_bearer_token(request)
        answer = chat_with_history(req.message, token)
        return ChatResponse(reply=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
