"""Groq API for injury adaptation (same JSON ``rows`` as main app)."""

from __future__ import annotations

import logging

from groq import Groq

log = logging.getLogger(__name__)


def run_groq_adaptation(
    user_message: str,
    *,
    api_key: str,
    system_prompt: str,
    model: str = "llama-3.3-70b-versatile",
    temperature: float = 0.3,
) -> str:
    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        response_format={"type": "json_object"},
        temperature=temperature,
    )
    text = (completion.choices[0].message.content or "").strip()
    if not text:
        raise ValueError("Empty response from Groq")
    return text


def _should_try_next_groq_model(exc: BaseException) -> bool:
    try:
        import groq

        if isinstance(exc, (groq.AuthenticationError, groq.PermissionDeniedError)):
            return False
        if isinstance(exc, groq.RateLimitError):
            return True
        if isinstance(exc, (groq.InternalServerError, groq.APIConnectionError, groq.APITimeoutError)):
            return True
        if isinstance(exc, groq.APIStatusError):
            return getattr(exc, "status_code", None) in (429, 502, 503)
    except Exception:
        pass
    msg = str(exc).lower()
    if "invalid api key" in msg or "incorrect api key" in msg:
        return False
    for needle in ("unavailable", "high demand", "rate limit", "overloaded", "503", "429"):
        if needle in msg:
            return True
    return False


def run_groq_adaptation_try_models(
    user_message: str,
    *,
    api_key: str,
    system_prompt: str,
    models: list[str],
    temperature: float = 0.3,
) -> str:
    cleaned = [m.strip() for m in models if m and str(m).strip()]
    if not cleaned:
        raise ValueError("No Groq models configured")

    last: BaseException | None = None
    for i, model in enumerate(cleaned):
        try:
            return run_groq_adaptation(
                user_message,
                api_key=api_key,
                system_prompt=system_prompt,
                model=model,
                temperature=temperature,
            )
        except Exception as e:
            last = e
            try:
                import groq

                if isinstance(e, (groq.AuthenticationError, groq.PermissionDeniedError)):
                    raise
            except Exception:
                pass
            if i + 1 < len(cleaned) and _should_try_next_groq_model(e):
                log.warning("Groq model %s failed (%s); trying next model.", model, e)
                continue
            raise
    assert last is not None
    raise last
