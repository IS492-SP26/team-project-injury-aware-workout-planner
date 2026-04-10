"""
AdaptFit-style pipeline: Gemini reads the YouTube URL directly twice
(draft timeline -> verify), then injury adaptation is a separate LLM
step in ``server._run_gemini_adaptation``.
"""

from __future__ import annotations

import logging
import os
from statistics import median
from typing import Any

from fastapi import HTTPException

from backend.gemini_timeline_generator import (
    DEFAULT_GEMINI_PROMPT,
    generate_timeline_from_gemini,
    verify_timeline_with_gemini,
)

log = logging.getLogger(__name__)


def _extract_youtube_video_id(youtube_url: str) -> str:
    youtube_url = (youtube_url or "").strip()
    if "watch?v=" in youtube_url:
        return youtube_url.split("watch?v=", 1)[1].split("&", 1)[0]
    if "youtu.be/" in youtube_url:
        return youtube_url.split("youtu.be/", 1)[1].split("?", 1)[0]
    if "/shorts/" in youtube_url:
        return youtube_url.split("/shorts/", 1)[1].split("?", 1)[0]
    return ""


def _dedupe_consecutive_segment_starts(starts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for item in sorted(starts, key=lambda segment: int(segment["start_time_seconds"])):
        if not cleaned:
            cleaned.append(item)
            continue
        previous = cleaned[-1]
        same_name = previous["exercise_name"].strip().lower() == item["exercise_name"].strip().lower()
        close_in_time = abs(int(item["start_time_seconds"]) - int(previous["start_time_seconds"])) <= 20
        if same_name and close_in_time:
            continue
        cleaned.append(item)
    return cleaned


def _merge_repeated_consecutive_segments(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    directional_terms = ("left", "right", "leg", "arm", "side")
    removed_offset = 0

    for raw_segment in segments:
        segment = dict(raw_segment)
        segment["start_time_seconds"] = max(0, int(segment["start_time_seconds"]) - removed_offset)
        segment["end_time_seconds"] = max(0, int(segment["end_time_seconds"]) - removed_offset)

        if not merged:
            merged.append(segment)
            continue

        previous = merged[-1]
        same_workout = previous["workout"].strip().lower() == segment["workout"].strip().lower()
        same_section = previous.get("section", "").strip().lower() == segment.get("section", "").strip().lower()
        previous_notes = previous.get("notes", "").strip().lower()
        current_notes = segment.get("notes", "").strip().lower()
        has_directional_note = any(term in previous_notes or term in current_notes for term in directional_terms)

        if same_workout and same_section and not has_directional_note:
            removed_offset += max(0, int(segment["end_time_seconds"]) - int(segment["start_time_seconds"]))
            continue

        merged.append(segment)

    return merged


def _build_payload_from_segment_starts(
    title: str,
    youtube_url: str,
    starts: list[dict[str, Any]],
) -> dict[str, Any]:
    if not starts:
        raise ValueError("No workout segments were found in the Gemini timeline.")

    starts = _dedupe_consecutive_segment_starts(starts)
    deduped: list[dict[str, Any]] = []
    seen_times: set[int] = set()

    for item in starts:
        start_time = int(item["start_time_seconds"])
        if start_time in seen_times:
            continue
        deduped.append(item)
        seen_times.add(start_time)

    segments: list[dict[str, Any]] = []
    for index, item in enumerate(deduped):
        next_item = deduped[index + 1] if index + 1 < len(deduped) else None
        end_time = int(next_item["start_time_seconds"]) if next_item else int(item["start_time_seconds"]) + 40
        if end_time <= int(item["start_time_seconds"]):
            end_time = int(item["start_time_seconds"]) + 40

        segments.append(
            {
                "start_time_seconds": int(item["start_time_seconds"]),
                "end_time_seconds": end_time,
                "workout": item["exercise_name"],
                "section": item.get("section", ""),
                "notes": item.get("notes", ""),
            }
        )

    segments = _merge_repeated_consecutive_segments(segments)
    return {
        "youtube_video_id": _extract_youtube_video_id(youtube_url),
        "title": title or "Workout Video",
        "youtube_url": youtube_url,
        "segments": segments,
        "generation_method": "gemini_url_prompt",
    }


def _estimate_duration_seconds(payload: dict[str, Any]) -> int:
    segments = payload.get("segments") or []
    if not isinstance(segments, list) or not segments:
        return 0

    starts = sorted(int(segment.get("start_time_seconds") or 0) for segment in segments)
    if len(starts) == 1:
        return starts[0] + 40

    gaps = [later - earlier for earlier, later in zip(starts, starts[1:]) if later > earlier]
    typical_gap = int(median(gaps)) if gaps else 40
    typical_gap = max(15, typical_gap)
    return starts[-1] + typical_gap


def _enforce_uniform_section_durations(payload: dict[str, Any], video_duration_seconds: int) -> dict[str, Any]:
    segments = [dict(segment) for segment in payload.get("segments", [])]
    if len(segments) < 2:
        return payload

    sections: list[list[dict[str, Any]]] = []
    current_group: list[dict[str, Any]] = []
    current_section = None

    for segment in segments:
        section = segment.get("section", "") or ""
        if current_group and section != current_section:
            sections.append(current_group)
            current_group = []
        current_group.append(segment)
        current_section = section

    if current_group:
        sections.append(current_group)

    normalized: list[dict[str, Any]] = []
    next_group_start_hard_limit = video_duration_seconds

    for group_index in range(len(sections) - 1, -1, -1):
        group = sections[group_index]
        group_start = int(group[0]["start_time_seconds"])
        group_end_limit = next_group_start_hard_limit
        if group_index + 1 < len(sections):
            group_end_limit = int(sections[group_index + 1][0]["start_time_seconds"])

        count = len(group)
        available = max(1, group_end_limit - group_start)
        raw_durations = [
            max(1, int(item["end_time_seconds"]) - int(item["start_time_seconds"]))
            for item in group
        ]
        target_duration = max(10, round((sum(raw_durations) / len(raw_durations)) / 5) * 5)
        max_uniform_duration = max(10, available // count)
        duration = min(target_duration, max_uniform_duration)

        if duration * count > available:
            duration = max(10, available // count)

        rebuilt: list[dict[str, Any]] = []
        for index, item in enumerate(group):
            rebuilt_item = dict(item)
            start = group_start + (index * duration)
            end = start + duration
            if index == count - 1:
                end = group_end_limit
            rebuilt_item["start_time_seconds"] = start
            rebuilt_item["end_time_seconds"] = max(start + 1, end)
            rebuilt.append(rebuilt_item)

        sections[group_index] = rebuilt
        next_group_start_hard_limit = group_start

    for group in sections:
        normalized.extend(group)

    payload["segments"] = normalized
    return payload


def _clamp_payload_to_duration(payload: dict[str, Any], video_duration_seconds: int) -> dict[str, Any]:
    if video_duration_seconds <= 0:
        return payload

    segments = payload.get("segments", [])
    clamped: list[dict[str, Any]] = []
    for segment in segments:
        item = dict(segment)
        item["start_time_seconds"] = min(max(0, int(item["start_time_seconds"])), video_duration_seconds)
        item["end_time_seconds"] = min(max(0, int(item["end_time_seconds"])), video_duration_seconds)
        if item["end_time_seconds"] <= item["start_time_seconds"]:
            continue
        clamped.append(item)

    payload["segments"] = clamped
    return payload


def _reconcile_gemini_payloads(
    draft_payload: dict[str, Any],
    verified_payload: dict[str, Any],
    youtube_url: str,
) -> dict[str, Any]:
    draft = _build_payload_from_segment_starts(
        draft_payload.get("title") or "Workout Video",
        youtube_url,
        draft_payload.get("segments") or [],
    )
    verified = _build_payload_from_segment_starts(
        verified_payload.get("title") or draft.get("title") or "Workout Video",
        youtube_url,
        verified_payload.get("segments") or [],
    )

    draft_segments = draft.get("segments", [])
    verified_segments = verified.get("segments", [])
    if not draft_segments:
        return verified
    if not verified_segments:
        return draft

    reconciled: list[dict[str, Any]] = []
    used_verified: set[int] = set()

    for draft_segment in draft_segments:
        draft_name = draft_segment["workout"].strip().lower()
        draft_start = int(draft_segment["start_time_seconds"])
        match_index = None

        for index, verified_segment in enumerate(verified_segments):
            if index in used_verified:
                continue
            verified_name = verified_segment["workout"].strip().lower()
            verified_start = int(verified_segment["start_time_seconds"])
            same_name = draft_name == verified_name
            close_time = abs(draft_start - verified_start) <= 25
            if same_name or close_time:
                match_index = index
                break

        if match_index is None:
            reconciled.append(draft_segment)
            continue

        used_verified.add(match_index)
        verified_segment = verified_segments[match_index]
        merged_segment = dict(draft_segment)
        merged_segment["workout"] = verified_segment.get("workout", draft_segment["workout"])
        merged_segment["start_time_seconds"] = min(
            int(draft_segment["start_time_seconds"]),
            int(verified_segment["start_time_seconds"]),
        )
        merged_segment["end_time_seconds"] = max(
            int(draft_segment["end_time_seconds"]),
            int(verified_segment["end_time_seconds"]),
        )
        if verified_segment.get("section"):
            merged_segment["section"] = verified_segment["section"]
        if verified_segment.get("notes"):
            merged_segment["notes"] = verified_segment["notes"]
        reconciled.append(merged_segment)

    for index, verified_segment in enumerate(verified_segments):
        if index not in used_verified:
            reconciled.append(verified_segment)

    reconciled.sort(key=lambda segment: int(segment["start_time_seconds"]))
    return {
        "youtube_video_id": _extract_youtube_video_id(youtube_url),
        "title": verified.get("title") or draft.get("title") or "Workout Video",
        "youtube_url": youtube_url,
        "segments": reconciled,
        "generation_method": "gemini_reconciled",
    }


def _payload_to_chapters(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chapters: list[dict[str, Any]] = []
    for index, segment in enumerate(segments, start=1):
        chapters.append(
            {
                "index": index,
                "title": str(segment.get("workout") or f"Segment {index}").strip(),
                "start_time": float(int(segment.get("start_time_seconds") or 0)),
                "end_time": float(int(segment.get("end_time_seconds") or 0)),
                "section": str(segment.get("section") or "").strip(),
                "notes": str(segment.get("notes") or "").strip(),
            }
        )
    return chapters


def build_video_information_gemini_adaptfit(url: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """
    1) Gemini: draft workout timeline directly from the YouTube URL.
    2) Gemini: verify/correct that draft with the same URL.
    3) Map the reconciled segments to ``video_information["chapters"]`` for the
       injury-adaptation call.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set")

    model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    try:
        draft = generate_timeline_from_gemini(api_key, url, DEFAULT_GEMINI_PROMPT, model=model)
        draft_payload = _build_payload_from_segment_starts(
            draft.get("title") or "Workout Video",
            url,
            draft.get("segments") or [],
        )
        estimated_duration = _estimate_duration_seconds(draft_payload)
        if estimated_duration <= 0:
            estimated_duration = 60

        verified = verify_timeline_with_gemini(api_key, url, draft, estimated_duration, model=model)
        final_payload = _reconcile_gemini_payloads(draft, verified, url)
        final_payload = _enforce_uniform_section_durations(final_payload, estimated_duration)
        final_payload = _clamp_payload_to_duration(final_payload, estimated_duration)

        segments = final_payload.get("segments") or []
        if not segments:
            raise ValueError("Gemini returned no segments after reconciliation")

        chapters = _payload_to_chapters(segments)
        final_duration = max(
            estimated_duration,
            max(int(segment.get("end_time_seconds") or 0) for segment in segments),
        )
        video_information: dict[str, Any] = {
            "title": final_payload.get("title") or draft.get("title") or "Workout Video",
            "id": _extract_youtube_video_id(url),
            "channel": "",
            "duration": final_duration,
            "webpage_url": url,
            "chapters": chapters,
            "description": "",
            "adaptfit_phase": "gemini_verified_timeline",
            "adaptfit_youtube_url": url,
        }
        adaptfit_payload: dict[str, Any] = {
            "generation_method": "gemini_url_prompt",
            "draft_timeline": draft,
            "verified_timeline": verified,
            "reconciled_timeline": final_payload,
            "estimated_duration_seconds": final_duration,
        }
        return video_information, adaptfit_payload
    except HTTPException:
        raise
    except Exception as exc:
        log.exception("Gemini URL timeline generation failed.")
        raise HTTPException(
            status_code=400,
            detail=f"Could not generate workout timestamps from Gemini for this YouTube URL: {exc}",
        ) from exc
