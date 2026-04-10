"""Legacy name; use ``adaptation_common`` and ``gemini_adaptation``. Groq removed."""

from backend.prompts.adaptation_common import (  # noqa: F401
    SYSTEM_PROMPT_JSON,
    build_user_message,
    format_video_information_from_dict,
    load_adaptation_input_json,
    video_information_from_pasted_text,
)

DEFAULT_MODEL = "gemini-2.5-flash"


def run_groq(*_args: object, **_kwargs: object) -> str:
    raise RuntimeError("Groq backend removed. Set GEMINI_API_KEY.")
