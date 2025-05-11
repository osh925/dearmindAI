# services/reward_service.py

import os
import base64
import re
import tempfile
from io import BytesIO
from types import SimpleNamespace
from typing import Optional

import vertexai
from vertexai.preview.vision_models import ImageGenerationModel
from vertexai.preview.generative_models import GenerativeModel, Part
import vertexai.preview.generative_models as generative_models
from time import sleep

from PIL import Image
import requests

# ─── CONFIG & INIT (run once per process) ───────────────────────────────────────
PROJECT_ID = "sc2025-test"
REGION     = "us-central1"

vertexai.init(project=PROJECT_ID, location=REGION)

# Preload both Imagen variants
IMAGE_MODEL_002 = ImageGenerationModel.from_pretrained("imagegeneration@002")
IMAGE_MODEL_006 = ImageGenerationModel.from_pretrained("imagegeneration@006")

# Gemini for letter generation
TEXT_MODEL = GenerativeModel("gemini-2.0-flash")

# Text safety & generation settings
GEN_TEXT_CFG = {"max_output_tokens": 150, "temperature": 0.8, "top_p": 0.9}
SAFETY = {
    generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH:       generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT:        generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}


# ─── MAIN SERVICE FUNCTION ─────────────────────────────────────────────────────
def generate_reward(
    user_images: list[str],
    art_style: str,
    diaries: Optional[list[str]] = None,
    retry_attempts: int = 3
) -> SimpleNamespace:
    """
    Returns SimpleNamespace(
        image_b64=<base64 PNG of the generated painting>,
        letter=<generated congratulatory letter>
    )
    """
    diaries = diaries or []
    diary_snips = "\n".join(f"- {d}" for d in diaries)

    # 1) Choose which Imagen model based on style
    if art_style in ("watercolor", "oil_painting"):
        img_model = IMAGE_MODEL_002
    else:
        img_model = IMAGE_MODEL_006

    # 2) Build the image prompt
    image_prompt = (
        "Create an inspirational painting in "
        f"{art_style}.\n"
        "Include motifs that reflect soothing vibe if appropriate. "
        "Do not draw overly abstract pictures. "
        "Avoid portrait of a person. "
        "Also try to reflect user's emotions (not the direct anecdotes but the emotions) from their recent diary entries. Here are some of them\n"
        f"{diary_snips}"
    )

    # 3) Generate (with retry)
    for attempt in range(1, retry_attempts+1):
        try:
            imgs = img_model.generate_images(
                prompt=image_prompt,
                number_of_images=1,
                add_watermark=False
            )
            reward_img = imgs[0]
            break
        except Exception as e:
            if attempt == retry_attempts:
                raise RuntimeError(f"Image generation failed after {retry_attempts} attempts: {e}")
            sleep(1)  # back-off briefly

    # 4) Encode the reward image to base64
    img_bytes = None

    # reward_img 자체가 PIL 이미지인 경우
    if isinstance(reward_img, Image.Image):
        pil_img = reward_img

    # reward_img.image 속성에 PIL 이미지가 담겨있는 경우
    elif hasattr(reward_img, "image") and isinstance(reward_img.image, Image.Image):
        pil_img = reward_img.image

    else:
        pil_img = None

    if pil_img:
        # 메모리 버퍼에 PNG로 저장
        buf = BytesIO()
        pil_img.save(buf, format="PNG")
        img_bytes = buf.getvalue()
    else:
        # Fallback: 임시 파일에 저장 후 읽기
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            try:
                # reward_img.save(path) 만 지원하는 객체라면 이 분기로 옴
                reward_img.save(tmp.name)
                tmp.flush()
                with open(tmp.name, "rb") as f:
                    img_bytes = f.read()
            finally:
                os.unlink(tmp.name)

    # 최종 Base64 인코딩 결과
    reward_b64 = base64.b64encode(img_bytes).decode("utf-8")

    # 5) Prepare parts for letter generation
    letter_prompt = (
        f"You are a friendly app character on a picture diary app. "
        f"Here are some of user's recent diary entries and user's drawngs:\n"
        f"{diary_snips}\n\n"
        "Write a short letter (2–3 sentences) praising their work and "
        "encouraging them to keep up caring themselves emotionally. You should focus on user's emotions from their diary entries.\n"
        "Try to avoid direct mentions about user's drawings and content of diaries. Instead focus on their feelings and emotions.\n"
        "And always maintain friendly and soothing vibe, try to write your letter as if you're one of user's close friends."
    )
    parts = [Part.from_text(letter_prompt)]

    # 6) Decode user-uploaded images (for context) and append
    for img_str in user_images:
        try:
            if img_str.startswith("http://") or img_str.startswith("https://"):
                # URL 인 경우 HTTP GET
                resp = requests.get(img_str, timeout=5)
                resp.raise_for_status()
                img_bytes = resp.content
            else:
                # Base64 인 경우 디코딩
                img_bytes = base64.b64decode(img_str)
        except Exception as e:
            raise RuntimeError(f"사용자 이미지 처리 중 오류: {e}")

        # MIME type 추론(필요시). 여기서는 PNG 고정
        parts.append(Part.from_data(data=img_bytes, mime_type="image/png"))

    # 7) Call Gemini to generate the letter
    resp = TEXT_MODEL.generate_content(
        parts,
        generation_config=GEN_TEXT_CFG,
        safety_settings=SAFETY,
        stream=False
    )
    letter = getattr(resp, "text", None) or resp.candidates[0].content.text

    # 8) Return both pieces
    return SimpleNamespace(image_b64=reward_b64, letter=letter)
