import json
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel, Field

load_dotenv()


class ModeEnum(str, Enum):
    summarize = "summarize"
    rephrase = "rephrase"
    extract_json = "extract_json"
    classify = "classify"


class ToneEnum(str, Enum):
    casual = "casual"
    professional = "professional"
    friendly = "friendly"


class RunRequest(BaseModel):
    mode: ModeEnum
    text: str = Field(min_length=1, max_length=5000)
    tone: Optional[ToneEnum] = None


class RunResponse(BaseModel):
    result: Union[str, Dict[str, Any], List[Any]]
    usage: Dict[str, int]


def get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Server misconfiguration: OPENAI_API_KEY is not set.")
    return OpenAI(api_key=api_key)


def build_messages(req: RunRequest) -> List[Dict[str, str]]:
    system_instructions = "You are a careful assistant. Follow the requested mode exactly."
    user_prompt = ""

    if req.mode == ModeEnum.summarize:
        user_prompt = (
            "Summarize the following text clearly and concisely. Focus on the key points.\n\n" + req.text
        )
    elif req.mode == ModeEnum.rephrase:
        tone_text = req.tone.value if req.tone else "neutral"
        user_prompt = (
            f"Rephrase the following text in a {tone_text} tone. Keep meaning faithful; improve clarity.\n\n" + req.text
        )
    elif req.mode == ModeEnum.extract_json:
        user_prompt = (
            "Extract structured data as a JSON object from the following text. "
            "Return ONLY valid JSON with double-quoted keys/strings, no code fences.\n\n" + req.text
        )
    elif req.mode == ModeEnum.classify:
        user_prompt = (
            "Determine the overall sentiment (positive, neutral, or negative) of the following text. "
            "Reply with a short sentence naming the sentiment.\n\n" + req.text
        )

    return [
        {"role": "system", "content": system_instructions},
        {"role": "user", "content": user_prompt},
    ]


def _get_prompt_id_for_mode(mode: ModeEnum) -> Optional[str]:
    if mode == ModeEnum.summarize:
        return os.getenv("SUMMARIZE_PROMPT_ID")
    if mode == ModeEnum.rephrase:
        return os.getenv("REPHRASE_PROMPT_ID")
    if mode == ModeEnum.extract_json:
        return os.getenv("EXTRACT_JSON_PROMPT_ID")
    if mode == ModeEnum.classify:
        return os.getenv("CLASSIFY_SENTIMENT_PROMPT_ID")
    return None


def _coerce_usage(obj: Any) -> Dict[str, int]:
    try:
        return {
            "prompt_tokens": int(getattr(obj, "prompt_tokens", 0) or 0),
            "completion_tokens": int(getattr(obj, "completion_tokens", 0) or 0),
            "total_tokens": int(getattr(obj, "total_tokens", 0) or 0),
        }
    except Exception:
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}


def call_openai(req: RunRequest) -> Dict[str, Any]:
    client = get_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    prompt_id = _get_prompt_id_for_mode(req.mode)
    if prompt_id:
        try:
            resp = client.responses.create(
                model=model,
                prompt_id=prompt_id,
                input={
                    "mode": req.mode.value,
                    "text": req.text,
                    "tone": req.tone.value if req.tone else None,
                },
                temperature=0.0 if req.mode == ModeEnum.extract_json else 0.2,
                response_format={"type": "json_object"} if req.mode == ModeEnum.extract_json else None,
            )
        except Exception:
            # Fall back to inline prompt if prompt call fails
            prompt_id = None
        else:
            # Extract text content
            content_text = getattr(resp, "output_text", None)
            if content_text is None:
                # Best-effort fallback to raw structure
                try:
                    content_text = json.dumps(resp.dict())
                except Exception:
                    content_text = ""

            usage_dict = _coerce_usage(getattr(resp, "usage", None))

            if req.mode == ModeEnum.extract_json:
                try:
                    parsed = json.loads(content_text)
                    result: Union[str, Dict[str, Any], List[Any]] = parsed
                except Exception:
                    result = content_text
            else:
                result = content_text

            return {"result": result, "usage": usage_dict}

    # Fallback: inline messages via Chat Completions
    messages = build_messages(req)
    try:
        if req.mode == ModeEnum.extract_json:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.0,
                response_format={"type": "json_object"},
            )
        else:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.2,
            )
    except Exception:
        raise HTTPException(status_code=502, detail="Upstream AI service error. Please try again.")

    content = completion.choices[0].message.content if completion.choices else ""
    usage_dict = _coerce_usage(getattr(completion, "usage", None))

    if req.mode == ModeEnum.extract_json:
        try:
            parsed = json.loads(content)
            result = parsed
        except Exception:
            result = content
    else:
        result = content

    return {"result": result, "usage": usage_dict}


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/run", response_model=RunResponse)
async def run(req: RunRequest) -> RunResponse:
    if req.mode == ModeEnum.rephrase and not req.tone:
        raise HTTPException(status_code=422, detail="Tone is required when mode = rephrase.")

    try:
        payload = call_openai(req)
        return RunResponse(**payload)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected server error. Please try again.")


# Health check
@app.get("/health")
async def health():
    return {"ok": True}


# Static frontend (serve ../frontend)
FRONTEND_DIR = str(Path(__file__).resolve().parent.parent / "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="static")
