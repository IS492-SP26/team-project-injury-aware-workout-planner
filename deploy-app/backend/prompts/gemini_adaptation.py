"""
Gemini API for injury-aware workout adaptation (JSON rows).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from google import genai
from google.genai import types

log = logging.getLogger(__name__)

# Schema matches SYSTEM_PROMPT_JSON in adaptation_common (object with "rows" array).
ADAPTATION_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "rows": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "original": {"type": "string"},
                    "modified_alternative": {"type": "string"},
                    "risk_flag": {
                        "type": "string",
                        "enum": ["Low", "Medium", "High"],
                    },
                },
                "required": ["original", "modified_alternative", "risk_flag"],
            },
        }
    },
    "required": ["rows"],
    "additionalProperties": False,
}


def run_gemini_adaptation(
    user_message: str,
    *,
    api_key: str,
    system_prompt: str,
    model: str = "gemini-2.5-flash",
    temperature: float = 0.3,
) -> str:
    """
    Returns raw JSON text (object with \"rows\" array) from Gemini.
    """
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=[
            {
                "role": "user",
                "parts": [{"text": user_message}],
            }
        ],
        config=types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            response_json_schema=ADAPTATION_RESPONSE_SCHEMA,
            system_instruction=system_prompt,
        ),
    )
    text = (response.text or "").strip()
    if not text:
        raise ValueError("Empty response from Gemini")
    return text


def _should_try_next_gemini_model(exc: BaseException) -> bool:
    """True when trying another model might help (overload / rate limit), not auth/config errors."""
    msg = str(exc).lower()
    if "api key" in msg and ("invalid" in msg or "not valid" in msg):
        return False
    if "permission" in msg or "403" in msg:
        return False
    for needle in (
        "503",
        "429",
        "unavailable",
        "high demand",
        "overloaded",
        "resource exhausted",
        "deadline",
        "timeout",
        "502",
        "504",
    ):
        if needle in msg:
            return True
    return False


def run_gemini_adaptation_try_models(
    user_message: str,
    *,
    api_key: str,
    system_prompt: str,
    models: list[str],
    temperature: float = 0.3,
) -> str:
    """Try models in order; on transient errors, continue to the next model."""
    cleaned = [m.strip() for m in models if m and str(m).strip()]
    if not cleaned:
        raise ValueError("No Gemini models configured")

    last: BaseException | None = None
    for i, model in enumerate(cleaned):
        try:
            return run_gemini_adaptation(
                user_message,
                api_key=api_key,
                system_prompt=system_prompt,
                model=model,
                temperature=temperature,
            )
        except Exception as e:
            last = e
            if i + 1 < len(cleaned) and _should_try_next_gemini_model(e):
                log.warning("Gemini model %s failed (%s); trying next model.", model, e)
                continue
            raise
    assert last is not None
    raise last


def parse_adaptation_json(reply: str) -> list[dict[str, Any]]:
    """Parse Gemini JSON into a list of row dicts (supports legacy bare array)."""
    data = json.loads(reply)
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    if isinstance(data, dict) and "rows" in data:
        rows = data["rows"]
        if isinstance(rows, list):
            return [r for r in rows if isinstance(r, dict)]
    raise ValueError("Expected JSON object with 'rows' array or a JSON array")
