import json
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Union, List

import logging
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel, Field

# Load env from repo root and backend folder, in that order
# _ENV_ROOT = Path(__file__).resolve().parent.parent / ".env"
# _ENV_BACKEND = Path(__file__).resolve().parent / ".env"
load_dotenv()


logger = logging.getLogger("app")
logging.basicConfig(level=logging.INFO)


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


def _mode_params(mode: ModeEnum) -> Dict[str, Optional[float]]:
    if mode == ModeEnum.extract_json:
        return {"temperature": 0.0}
    return {"temperature": 0.2}


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
    if not prompt_id:
        raise HTTPException(status_code=500, detail="Server misconfiguration: Prompt ID not set for this mode.")

    # Inputs: system prompt comes from Prompt Studio (prompt_id). User prompt is req.text
    input_vars: Dict[str, Any] = {"user_prompt": req.text, "text": req.text}
    if req.mode == ModeEnum.rephrase and req.tone:
        input_vars["tone"] = req.tone.value

    params = _mode_params(req.mode)
    try:
        # Call using the saved Prompt ID via the 'prompt' parameter
        try:
            resp = client.responses.create(
                model=model,
                prompt={"id": prompt_id},
                input=input_vars,
                # temperature=params["temperature"],  # type: ignore[index]
            )
        except Exception as e_primary:
            logger.info("Prompt call with dict inputs failed; retrying with raw text input. Error: %s", e_primary)
            # Retry with raw string input (binds to the prompt's default variable)
            resp = client.responses.create(
                model=model,
                prompt={"id": prompt_id},
                input=req.text,
                # temperature=params["temperature"],  # type: ignore[index]
            )
    except Exception as e:
        # Log detailed error server-side, but return a friendly message
        logger.exception("OpenAI Responses API call failed: %s", e)
        status = getattr(e, "status_code", None)
        try:
            status = int(status) if status is not None else 502
        except Exception:
            status = 502
        message = getattr(e, "message", None) or str(e) or "Upstream AI service error. Please try again."
        # Lightweight sanitization
        if "api_key" in message.lower():
            message = "Authentication with upstream AI failed. Check API key."
        raise HTTPException(status_code=status, detail=message)

    content_text = getattr(resp, "output_text", None)
    if content_text is None:
        try:
            content_text = json.dumps(resp.dict())
        except Exception:
            content_text = ""

    usage_dict = _coerce_usage(getattr(resp, "usage", None))

    if req.mode == ModeEnum.extract_json:
        try:
            parsed = json.loads(content_text)
            result: Union[str, Dict[str, Any], Any] = parsed
        except Exception:
            result = content_text
    else:
        result = content_text

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
