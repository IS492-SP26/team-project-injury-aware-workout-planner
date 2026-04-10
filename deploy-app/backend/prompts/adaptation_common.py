"""
Shared workout-adaptation prompts and formatting (model-agnostic).

Used by the Gemini backend; formatting matches the former Groq JSON contract.
"""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent
from typing import Any

DESCRIPTION_MAX_CHARS = 12_000

SYSTEM_PROMPT_JSON = dedent("""\
    You are a rehabilitation-focused workout adaptation assistant.

    Goal:
    Review workout movements from the workout (video metadata or pasted plan) against the user's injury profile and return one JSON object with a single key "rows" whose value is an array—one object per distinct movement or segment.

    Safety rules:
    Give conservative guidance only.
    Do not diagnose.
    Do not replace in-person medical care.
    If information is missing, state brief assumptions inside the relevant "modified_alternative" or "original" field.
    Base risk on the user's injury status, pain triggers, functional limitations, and training level.
    Consider the user's goals (may be multiple) when selecting safer alternatives, but safety overrides performance goals.

    Output rules:
    Return only valid JSON. No markdown fences, no commentary, no text before or after the object.
    The response must be a JSON object with exactly one property "rows". The value of "rows" must be an array of objects. Each object has exactly these keys:
    "original" (string)
    "modified_alternative" (string)
    "risk_flag" (string, exactly one of: "Low", "Medium", "High")
    In "original", use the movement name or segment label as closely as possible from the source.
    In "modified_alternative": use a safer substitute or regression if risk_flag is "Medium" or "High"; use "Keep as is" if "Low".
    Do not omit keys. Do not use empty strings. Keep values concise (under 25 words when possible).

    Decision rules:
    High = likely inappropriate, high knee load, unstable landing/cutting/twisting, deep flexion under load, or likely symptom aggravation.
    Medium = may be possible with modification, reduced range, slower tempo, support, or lower load.
    Low = generally acceptable as shown, or with minimal caution.

    When relevant, modify by changing: range of motion, tempo, support or balance assistance, bilateral vs unilateral loading, impact level, equipment, stability demands.

    Now review the provided workout movements and user profile.
    """)

SYSTEM_PROMPT_ADAPTATION_PHASE2 = dedent("""\
    You are a rehabilitation-focused workout adaptation assistant.

    The workout has already been segmented. The workout source information below lists each movement in chronological order with time ranges (see **Chapters / segments**). Your job is ONLY to assess injury risk and suggest safer alternatives — not to re-segment the video or invent new exercises.

    Goal:
    Return one JSON object with a single key "rows" whose value is an array. Output exactly one object per segment listed under **Chapters / segments**, in the SAME ORDER. The number of rows must equal the number of chapter lines.

    If **Chapters / segments** is empty but a pasted workout plan appears under **Description**, output one row per distinct exercise line in order (top to bottom).

    Safety rules:
    Give conservative guidance only.
    Do not diagnose.
    Do not replace in-person medical care.
    If information is missing, state brief assumptions inside the relevant "modified_alternative" field.
    Base risk on the user's injury status, pain triggers, functional limitations, and training level.

    Output rules:
    Return only valid JSON. No markdown fences, no commentary.
    The response must be a JSON object with exactly one property "rows". Each object has exactly these keys:
    "original" (string) — MUST be the movement name for that segment, matching the chapter/segment title text (verbatim when possible).
    "modified_alternative" (string)
    "risk_flag" (string, exactly one of: "Low", "Medium", "High")
    In "modified_alternative": use a safer substitute or regression if risk_flag is "Medium" or "High"; use "Keep as is" if "Low".
    Do not omit keys. Do not use empty strings. Keep values concise (under 25 words when possible).

    Decision rules:
    High = likely inappropriate, high joint load, unstable landing/cutting/twisting, deep flexion under load, or likely symptom aggravation.
    Medium = may be possible with modification, reduced range, slower tempo, support, or lower load.
    Low = generally acceptable as shown, or with minimal caution.

    Now review the listed movements against the user profile.
    """)


def format_video_information_from_dict(v: dict, *, fallback_url: str = "") -> str:
    """
    Build the LLM-facing video block from a dict (JSON ``video_information`` or yt-dlp-style fields).
    Chapters may include ``index`` or rely on list order.
    """
    title = v.get("title") or "Unknown title"
    vid = v.get("id") or ""
    channel = v.get("channel") or v.get("uploader") or ""
    duration = v.get("duration")
    duration_s = f"{duration}s" if duration is not None else "unknown"
    webpage = v.get("webpage_url") or fallback_url

    chapters = v.get("chapters") or []
    chapter_lines = []
    for i, ch in enumerate(chapters, start=1):
        idx = ch.get("index")
        if idx is None:
            idx = i
        st = ch.get("start_time")
        et = ch.get("end_time")
        name = ch.get("title") or f"Chapter {idx}"
        chapter_lines.append(f"  {idx}. [{st} – {et} s] {name}")
    chapters_block = "\n".join(chapter_lines) if chapter_lines else "  (No chapter markers in metadata.)"

    desc = (v.get("description") or "").strip()
    if len(desc) > DESCRIPTION_MAX_CHARS:
        desc = desc[:DESCRIPTION_MAX_CHARS] + "\n\n[Description truncated for length.]"

    return dedent(f"""\
        - **Title:** {title}
        - **Video ID:** {vid}
        - **Channel:** {channel}
        - **Duration:** {duration_s}
        - **URL:** {webpage}

        **Chapters / segments (from platform metadata):**
        {chapters_block}

        **Description (may list exercises):**
        {desc if desc else "(No description available.)"}
        """)


PASTED_PLAN_TITLE = "User-pasted workout plan"


def video_information_from_pasted_text(raw_text: str) -> dict[str, Any]:
    """Build a ``video_information``-shaped dict for a pasted text workout."""
    text = (raw_text or "").strip()
    text = "\n".join(line.rstrip() for line in text.splitlines())
    if len(text) > DESCRIPTION_MAX_CHARS:
        text = text[:DESCRIPTION_MAX_CHARS] + "\n\n[Description truncated for length.]"
    return {
        "title": PASTED_PLAN_TITLE,
        "id": "",
        "channel": "",
        "webpage_url": "",
        "chapters": [],
        "description": text,
        "workout_source": "pasted_text",
    }


def load_adaptation_input_json(path: str | Path) -> tuple[str, str]:
    """
    Load ``user_input_data`` and ``video_information`` from a JSON file.
    Returns (user_block, video_block) for ``build_user_message``.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Input JSON not found: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    user_obj = data.get("user_input_data")
    video_obj = data.get("video_information")
    if user_obj is None:
        raise ValueError("JSON must contain a top-level 'user_input_data' object.")
    if video_obj is None:
        raise ValueError("JSON must contain a top-level 'video_information' object.")
    if not isinstance(user_obj, dict):
        raise TypeError("'user_input_data' must be a JSON object.")
    if not isinstance(video_obj, dict):
        raise TypeError("'video_information' must be a JSON object.")
    try:
        profile = user_obj.get("user_profile")
        if isinstance(profile, dict):
            goals = profile.get("goals")
            goal = profile.get("goal")
            if goals is None and isinstance(goal, str) and goal.strip():
                profile["goals"] = [goal.strip()]
    except Exception:
        pass
    user_block = json.dumps(user_obj, indent=2, ensure_ascii=False)
    video_block = format_video_information_from_dict(video_obj)
    return user_block, video_block


def build_user_message(user_input_data: str, video_information: str) -> str:
    """Supply user and video context only; formatting rules live in the system prompt."""
    return dedent(f"""\
        User profile, injury detail, and functional assessment:

        {user_input_data.strip()}

        ---

        Workout source information (video metadata or pasted plan — movements / segments):

        {video_information.strip()}
        """)
