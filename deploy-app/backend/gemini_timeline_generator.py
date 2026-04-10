from __future__ import annotations

import json
from typing import Any

from google import genai
from google.genai import types


GEMINI_TIMELINE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Video title."},
        "youtube_url": {"type": "string", "description": "Original YouTube URL."},
        "segments": {
            "type": "array",
            "description": "Chronological list of workout transitions.",
            "items": {
                "type": "object",
                "properties": {
                    "start_time_seconds": {
                        "type": "integer",
                        "description": "Exact second when the work interval for the movement begins.",
                    },
                    "exercise_name": {
                        "type": "string",
                        "description": "Exact on-screen workout label or precise movement name.",
                    },
                    "section": {
                        "type": "string",
                        "description": "Optional section name such as Warm-up, HIIT, Round 1, Cool Down.",
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional note about uncertainty or transition nuance.",
                    },
                },
                "required": ["start_time_seconds", "exercise_name"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "youtube_url", "segments"],
    "additionalProperties": False,
}


DEFAULT_GEMINI_PROMPT = """Analyze this YouTube video and create a chronological workout timeline based on the on-screen exercise titles and countdown timer.

Rules:
1. Only use exercise names explicitly shown in the video graphics, or when the trainer clearly switches to a new movement.
2. Capture the exact second when the work interval begins for each new move.
3. Do not guess or generalize exercise names.
4. Include the warm-up, the full HIIT workout, and the cool down.
5. If an on-screen label appears before the movement begins, use the time the actual work interval starts.
6. Return the segments in chronological order.
7. If uncertain, use the notes field briefly.
"""

VERIFY_GEMINI_PROMPT_TEMPLATE = """You are validating and correcting a previously generated workout timeline for a YouTube workout video.

Task:
Review the provided draft timeline against the same video and return a corrected version.

Strict rules:
1. Keep timestamps chronological.
2. Remove hallucinated adjacent duplicates unless the same workout is clearly repeated as a separate work interval.
3. Preserve real left/right or side-specific variants.
4. Prefer the exact on-screen exercise label when visible.
5. Do not invent new workouts unless they are clearly supported by the video.
6. If a timestamp appears too early because of preview text, move it to the actual work interval start.
7. Keep the warm-up, main workout, and cool down if present.
8. The total schedule must fit naturally within the actual video duration of {video_duration_seconds} seconds.
9. If the draft timeline extends beyond the video duration, re-time the whole schedule logically instead of simply truncating the last entries.
10. Preserve workout order unless there is clear evidence the order is wrong.
11. Preserve legitimate repeated workouts if they are clearly separate intervals in the video.
12. In structured workout videos, most work intervals should have similar durations. Use that as a consistency check unless the video clearly switches format between rounds, rest blocks, or cool down.
13. If one segment duration is a strong outlier compared with neighboring workouts, re-check it against the video and normalize it when appropriate.
14. Make the final segment end at or before the actual video duration.
15. Return JSON only in the same schema.

Here is the draft timeline to verify and correct:
{draft_json}
"""


def generate_timeline_from_gemini(
    api_key: str,
    youtube_url: str,
    prompt: str,
    model: str = "gemini-2.5-flash",
) -> dict[str, Any]:
    client = genai.Client(api_key=api_key)
    video_part = types.Part(
        file_data=types.FileData(file_uri=youtube_url.strip(), mime_type="video/*")
    )
    text_part = types.Part(text=prompt)
    response = client.models.generate_content(
        model=model,
        contents=[types.Content(role="user", parts=[video_part, text_part])],
        config=types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
            response_json_schema=GEMINI_TIMELINE_SCHEMA,
        ),
    )

    text = response.text or ""
    if not text.strip():
        raise ValueError("Gemini returned an empty timeline response")
    return json.loads(text)


def verify_timeline_with_gemini(
    api_key: str,
    youtube_url: str,
    draft_payload: dict[str, Any],
    video_duration_seconds: int,
    model: str = "gemini-2.5-flash",
) -> dict[str, Any]:
    client = genai.Client(api_key=api_key)
    verify_prompt = VERIFY_GEMINI_PROMPT_TEMPLATE.format(
        draft_json=json.dumps(draft_payload, indent=2),
        video_duration_seconds=video_duration_seconds,
    )
    video_part = types.Part(
        file_data=types.FileData(file_uri=youtube_url.strip(), mime_type="video/*")
    )
    text_part = types.Part(text=verify_prompt)
    response = client.models.generate_content(
        model=model,
        contents=[types.Content(role="user", parts=[video_part, text_part])],
        config=types.GenerateContentConfig(
            temperature=0.0,
            response_mime_type="application/json",
            response_json_schema=GEMINI_TIMELINE_SCHEMA,
        ),
    )

    text = response.text or ""
    if not text.strip():
        raise ValueError("Gemini returned an empty verification response")
    return json.loads(text)
