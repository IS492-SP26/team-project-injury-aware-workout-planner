from __future__ import annotations

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
except ImportError as exc:
    raise SystemExit("Missing dependency. Install with: pip install yt-dlp") from exc


def extract_video_metadata(url: str) -> dict[str, Any]:
    """Full yt-dlp info dict (duration, description, chapters, …)."""
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
    }
    with YoutubeDL(opts) as ydl:
        return ydl.extract_info(url, download=False)


def fetch_video_information(url: str) -> dict[str, Any]:
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    chapters = info.get("chapters") or []
    return {
        "id": info.get("id"),
        "title": info.get("title"),
        "channel": info.get("channel") or info.get("uploader"),
        "duration": info.get("duration"),
        "webpage_url": info.get("webpage_url") or url,
        "description": info.get("description") or "",
        "chapters": [
            {
                "index": index + 1,
                "title": (chapter or {}).get("title"),
                "start_time": (chapter or {}).get("start_time"),
                "end_time": (chapter or {}).get("end_time"),
            }
            for index, chapter in enumerate(chapters)
        ],
    }

