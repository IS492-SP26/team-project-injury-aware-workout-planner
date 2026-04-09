#!/usr/bin/env python3
from __future__ import annotations

"""
Metadata-only chapter extraction using yt-dlp (no download, no ffmpeg).

Returns a dict compatible with the `video_information` object in:
`app/prompts/workout_adaptation_input.json`.
"""

import os
from typing import Any


def _use_certifi_ca_bundle() -> None:
    try:
        import certifi  # type: ignore
    except ImportError:
        return
    bundle = certifi.where()
    if bundle:
        os.environ.setdefault("SSL_CERT_FILE", bundle)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", bundle)


_use_certifi_ca_bundle()

try:
    from yt_dlp import YoutubeDL  # type: ignore
except ImportError as e:  # pragma: no cover
    raise SystemExit("Missing dependency. Install with: pip install yt-dlp") from e


def fetch_video_information(url: str) -> dict[str, Any]:
    """
    Extract YouTube metadata (including chapters if available) without downloading.
    """
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    chapters = info.get("chapters") or []
    payload = {
        "id": info.get("id"),
        "title": info.get("title"),
        "webpage_url": info.get("webpage_url") or url,
        "chapters": [
            {
                "index": i + 1,
                "title": (c or {}).get("title"),
                "start_time": (c or {}).get("start_time"),
                "end_time": (c or {}).get("end_time"),
            }
            for i, c in enumerate(chapters)
        ],
    }
    return payload

