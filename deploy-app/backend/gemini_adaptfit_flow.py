"""
AdaptFit-style pipeline: Gemini reads the video twice (draft timeline → verify), then injury adaptation is a separate LLM step in ``server._run_gemini_adaptation``.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from fastapi import HTTPException

from backend.gemini_timeline_generator import (
    DEFAULT_GEMINI_PROMPT,
    generate_timeline_from_gemini,
    verify_timeline_with_gemini,
)
from backend.yt.chapters_metadata import extract_video_metadata, fetch_video_information

log = logging.getLogger(__name__)


def _verified_segments_to_chapters(
    segments: list[dict[str, Any]],
    *,
    duration: int,
) -> list[dict[str, Any]]:
    chapters: list[dict[str, Any]] = []
    for i, seg in enumerate(segments):
        st = int(seg.get("start_time_seconds") or 0)
        nxt = segments[i + 1] if i + 1 < len(segments) else None
        nxt_st = int(nxt["start_time_seconds"]) if nxt else duration
        end = nxt_st if nxt_st > st else min(st + 30, duration)
        if end > duration:
            end = duration
        if end <= st:
            end = min(st + 15, duration) if duration > st else st + 1
        title = str(seg.get("exercise_name") or f"Segment {i + 1}").strip()
        chapters.append(
            {
                "index": i + 1,
                "title": title,
                "start_time": float(st),
                "end_time": float(max(st, end)),
                "section": (seg.get("section") or "") if isinstance(seg.get("section"), str) else "",
                "notes": (seg.get("notes") or "") if isinstance(seg.get("notes"), str) else "",
            }
        )
    return chapters


def _enrich_from_ytdlp(url: str, base: dict[str, Any]) -> dict[str, Any]:
    """Merge full yt-dlp info so duration/description/channel are available."""
    meta = extract_video_metadata(url)
    out = {**base}
    out.setdefault("title", meta.get("title"))
    out["id"] = out.get("id") or meta.get("id")
    out["duration"] = meta.get("duration")
    out["channel"] = meta.get("channel") or meta.get("uploader")
    out["webpage_url"] = out.get("webpage_url") or meta.get("webpage_url") or url
    out["description"] = (meta.get("description") or "")[:12000]
    return out


def build_video_information_gemini_adaptfit(url: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """
    1) Gemini: draft workout timeline from the YouTube video.
    2) Gemini: verify/correct the draft (same video + duration constraint).
    3) Map verified segments to ``video_information["chapters"]`` for the injury-adaptation call.

    On failure, falls back to yt-dlp metadata only (``fetch_video_information``).
    """
    try:
        meta = extract_video_metadata(url)
    except Exception as e:
        log.exception("yt-dlp could not read video URL")
        raise HTTPException(
            status_code=400,
            detail=f"Could not load YouTube metadata (check the URL): {e}",
        ) from e

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    duration = int(meta.get("duration") or 0)

    if not api_key:
        log.warning("GEMINI_API_KEY missing; using yt-dlp chapters/metadata only.")
        vi = _enrich_from_ytdlp(url, fetch_video_information(url))
        return vi, None

    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    try:
        draft = generate_timeline_from_gemini(api_key, url, DEFAULT_GEMINI_PROMPT, model=model)
        verified = verify_timeline_with_gemini(api_key, url, draft, duration, model=model)
        segments = verified.get("segments") or []
        if not segments:
            raise ValueError("Gemini returned no segments after verification")

        chapters = _verified_segments_to_chapters(segments, duration=duration)
        video_information: dict[str, Any] = {
            "title": verified.get("title") or meta.get("title"),
            "id": meta.get("id"),
            "channel": meta.get("channel") or meta.get("uploader"),
            "duration": duration,
            "webpage_url": meta.get("webpage_url") or url,
            "chapters": chapters,
            "description": (meta.get("description") or "")[:12000],
            "adaptfit_phase": "gemini_verified_timeline",
            "adaptfit_youtube_url": url,
        }
        adaptfit_payload: dict[str, Any] = {
            "generation_method": "gemini_timeline_verify",
            "draft_timeline": draft,
            "verified_timeline": verified,
        }
        return video_information, adaptfit_payload
    except HTTPException:
        raise
    except Exception as e:
        log.exception("Gemini timeline + verify failed; falling back to yt-dlp chapters.")
        vi = _enrich_from_ytdlp(url, fetch_video_information(url))
        return vi, {"generation_method": "yt_dlp_fallback", "error": str(e)}
