import json
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Union, List

import logging
from dotenv import load_dotenv
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from pydantic import BaseModel, Field


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
    if not obj:
        return {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    def _from_attr_or_key(o: Any, key: str) -> Optional[int]:
        try:
            v = getattr(o, key)
            if isinstance(v, (int, float)):
                return int(v)
        except Exception:
            pass
        if isinstance(o, dict):
            v = o.get(key)
            if isinstance(v, (int, float)):
                return int(v)
        return None

    def _first_of(o: Any, keys: List[str]) -> Optional[int]:
        for k in keys:
            v = _from_attr_or_key(o, k)
            if v is not None:
                return v
        return None

    prompt_tokens = _first_of(obj, ["prompt_tokens", "input_tokens", "input_token_count"])
    completion_tokens = _first_of(obj, ["completion_tokens", "output_tokens", "output_token_count"])
    total_tokens = _first_of(obj, ["total_tokens", "token_count"])  # some SDKs expose only total

    if total_tokens is None and (prompt_tokens is not None or completion_tokens is not None):
        total_tokens = (prompt_tokens or 0) + (completion_tokens or 0)

    return {
        "prompt_tokens": prompt_tokens or 0,
        "completion_tokens": completion_tokens or 0,
        "total_tokens": total_tokens or 0,
    }


def call_openai(req: RunRequest) -> Dict[str, Any]:
    client = get_client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    prompt_id = _get_prompt_id_for_mode(req.mode)
    if not prompt_id:
        raise HTTPException(status_code=500, detail="Server misconfiguration: Prompt ID not set for this mode.")

    content_parts: List[Dict[str, Any]] = [
        {"type": "input_text", "text": req.text}
    ]
    if req.mode == ModeEnum.rephrase and req.tone:
        content_parts.append({"type": "input_text", "text": f"tone: {req.tone.value}"})

    params = _mode_params(req.mode)
    try:
        try:
            resp = client.responses.create(
                model=model,
                prompt={"id": prompt_id},
                input=[{"role": "user", "content": content_parts}],
                **params,
            )
        except Exception as e_primary:
            logger.info("Prompt call with dict inputs failed; retrying with raw text input. Error: %s", e_primary)
            resp = client.responses.create(
                model=model,
                prompt={"id": prompt_id},
                input=req.text,
                **params,
            )
    except Exception as e:
        logger.exception("OpenAI Responses API call failed: %s", e)
        status = getattr(e, "status_code", None)
        try:
            status = int(status) if status is not None else 502
        except Exception:
            status = 502
        message = getattr(e, "message", None) or str(e) or "Upstream AI service error. Please try again."
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


RATE_BUCKETS: Dict[str, List[float]] = {}


def _client_key(request: Request) -> str:
    xff = request.headers.get("x-forwarded-for") or request.client.host if request.client else "unknown"
    return (xff.split(",")[0] if xff else "unknown").strip()


def _rate_limit_or_raise(request: Request) -> None:
    limit = int(os.getenv("RATE_LIMIT_REQUESTS", "20"))
    window_sec = int(os.getenv("RATE_LIMIT_WINDOW_SEC", "60"))
    if limit <= 0 or window_sec <= 0:
        return

    key = _client_key(request)
    now = time.time()
    window_start = now - window_sec

    timestamps = RATE_BUCKETS.get(key, [])
    timestamps = [t for t in timestamps if t >= window_start]
    if len(timestamps) >= limit:
        oldest = min(timestamps)
        remaining = window_sec - int(now - oldest)
        headers = {"Retry-After": str(max(1, remaining))}
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.", headers=headers)
    timestamps.append(now)
    RATE_BUCKETS[key] = timestamps


@app.post("/api/run", response_model=RunResponse)
async def run(req: RunRequest, request: Request) -> RunResponse:
    _rate_limit_or_raise(request)
    if req.mode == ModeEnum.rephrase and not req.tone:
        raise HTTPException(status_code=400, detail="Tone is required when mode = rephrase.")

    try:
        payload = call_openai(req)
        return RunResponse(**payload)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Unexpected server error. Please try again.")
