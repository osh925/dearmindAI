# services/analyze_service.py

import os
import base64
import re
from types import SimpleNamespace
from typing import Optional

import vertexai
import vertexai.preview.generative_models as generative_models
from vertexai.preview.generative_models import GenerativeModel, Part
from vertexai.preview import rag

# ─── CONFIG & INIT ─────────────────────────────────────────────────────────────
PROJECT_ID = "sc2025-test"
REGION     = "us-central1"

vertexai.init(project=PROJECT_ID, location=REGION)

# ─── MODELS & RAG SETUP (once per process) ────────────────────────────────────
MODEL_NAME = "gemini-1.5-flash-002"
model      = GenerativeModel(MODEL_NAME)

# RAG corpus you already created
CORPUS_NAME = "projects/60897742987/locations/us-central1/ragCorpora/2305843009213693952"

# Generation & safety settings
generation_config = {
    "max_output_tokens": 8192,
    "temperature":       1,
    "top_p":             0.95,
}
safety_settings = {
    generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH:      generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT:        generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

# ─── CORE LOGIC ────────────────────────────────────────────────────────────────

def extract_emotion_severity(output: str) -> tuple[str, str]:
    """
    Parse out a JSON array ["emotion","severity"] from the model output.
    Fall back to a simple keyword scan if parsing fails.
    Internally uses lowercase emotion/severity, but returns uppercase mapped values.
    """
    # 1) Strict JSON array match
    m = re.search(
        r'\[\s*"(?P<emotion>positive|depressed|anxious|angry)"\s*,\s*'
        r'"(?P<severity>safe|emergency)"\s*\]',
        output,
        flags=re.IGNORECASE
    )
    if m:
        raw_emo = m.group("emotion").lower()
        raw_sev = m.group("severity").lower()
    else:
        # 2) Keyword fallback
        low = output.lower()
        found = False
        for emo in ("positive","depressed","anxious","angry"):
            if emo in low:
                raw_emo = emo
                raw_sev = "emergency" if "emergency" in low else "safe"
                found = True
                break
        if not found:
            # 3) Default
            raw_emo, raw_sev = "positive", "safe"

    # 매핑 테이블: 내부 raw → 최종 반환값
    EMOTION_MAP = {
        "positive": "HAPPY",
        "depressed": "GLOOMY",
        "anxious": "ANXIOUS",
        "angry":   "ANGRY",
    }
    SEVERITY_MAP = {
        "safe":      "SAFE",
        "emergency": "EMERGENCY",
    }

    # 최종 반환은 매핑된 대문자 값
    return EMOTION_MAP.get(raw_emo, raw_emo.upper()), SEVERITY_MAP.get(raw_sev, raw_sev.upper())


def analyze_diary(
    image_b64: str,
    subject: str,
    writing_text: Optional[str] = None
) -> SimpleNamespace:
    """
    Decode the image, do RAG+multimodal generation, parse emotion+severity,
    and return an object with .emotion and .severity.
    """

    # ── 1) Decode the image part from Base64 ────────────────────────────────────
    image_bytes = base64.b64decode(image_b64)
    image_part  = Part.from_data(data=image_bytes, mime_type="image/png")

    # ── 2) Text-only retrieval from your RAG corpus ───────────────────────────
    retrieval_prompt = (
        f"<context>Your role is an art therapist; my role is a client. "
        f"You instructed me to draw {subject}.</context> "
        "<question>What insight can you offer from art therapy theory? "
        "Also judge if the client’s feelings are negative. "
        "If negative, pick one: anxiety, depression, or anger.</question>"
    )
    rr = rag.retrieval_query(
        rag_resources=[rag.RagResource(rag_corpus=CORPUS_NAME)],
        text=retrieval_prompt,
        similarity_top_k=5,
        vector_distance_threshold=0.5,
    )
    retrieved = " ".join([c.text for c in rr.contexts.contexts])

    # ── 3) Build the final multimodal prompt ─────────────────────────────────
    final_prompt = (
        retrieval_prompt +
        "\n\nAdditional Context from Retrieval:\n" +
        retrieved +
        "\n\nNow interpret the attached artwork and writing." +
        "\nAnd if you detect any negative feelings, suggest if the client shows "
        "a tendency toward suicidal or self-harm—only if you’re quite sure." +
        "\n\n**EXACTLY** output _only_ a JSON array of two strings like [\"emotion\",\"severity\"] "
        "where emotion ∈ {\"positive\",\"depressed\",\"anxious\",\"angry\"} and "
        "severity ∈ {\"safe\",\"emergency\"}. NO OTHER TEXT or explanation."
    )

    # ── 4) Assemble Parts & call the model ────────────────────────────────────
    parts = [final_prompt, image_part]
    if writing_text:
        try:
            parts.append(Part.from_text(writing_text))
        except AttributeError:
            parts.append(writing_text)

    response = model.generate_content(
        parts,
        generation_config=generation_config,
        safety_settings=safety_settings,
        stream=False,
    )
    raw = getattr(response, "text", None) or response.candidates[0].content.text

    # ── 5) Parse out emotion + severity ───────────────────────────────────────
    emotion, severity = extract_emotion_severity(raw)
    return SimpleNamespace(emotion=emotion, severity=severity)
