from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from services.analyze_service import analyze_diary

router = APIRouter()

class AnalyzeRequest(BaseModel):
    image: str = Field(..., description="Required base64 encoded image string")
    subject: str = Field(..., description="Required drawing subject")
    text: Optional[str] = Field(None, description="Optional text input")

class AnalyzeResult(BaseModel):
    emotion: str
    severity: str

@router.post("/analyze", response_model=AnalyzeResult)
async def interpret_diary(req: AnalyzeRequest):
    try:
        input_text = req.text or ""
        result = analyze_diary(req.image, req.subject, input_text)
        return AnalyzeResult(emotion=result.emotion, severity=result.severity)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))