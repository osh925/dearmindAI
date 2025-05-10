# routers/reward_router.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from services.reward_service import generate_reward

router = APIRouter()

class RewardRequest(BaseModel):
    images: List[str] = Field(
        ..., description="List of base64-encoded images"
    )
    style: str = Field(
        ..., description='Art style: one of "sketch","line_drawing","oil_painting","watercolor"'
    )
    diaries: Optional[List[str]] = Field(
        None, description="Optional list of recent diary text entries"
    )

class RewardResult(BaseModel):
    image: str  = Field(..., description="Base64-encoded PNG of the generated painting")
    letter: str = Field(..., description="Generated letter")

@router.post("/reward", response_model=RewardResult)
async def generate_reward_endpoint(req: RewardRequest):
    try:
        out = generate_reward(req.images, req.style, req.diaries)
        return RewardResult(image=out.image_b64, letter=out.letter)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
