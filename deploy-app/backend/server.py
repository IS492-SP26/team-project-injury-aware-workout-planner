from __future__ import annotations

import json
import logging
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field, model_validator

from backend.gemini_adaptfit_flow import build_video_information_gemini_adaptfit
from backend.prompts.adaptation_common import (
    SYSTEM_PROMPT_ADAPTATION_PHASE2,
    build_user_message,
    load_adaptation_input_json,
    video_information_from_pasted_text,
)
from backend.prompts.gemini_adaptation import parse_adaptation_json, run_gemini_adaptation_try_models
from backend.prompts.groq_adaptation import run_groq_adaptation_try_models

log = logging.getLogger(__name__)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


# Single env file: `deploy-app/backend/.env` (this file's directory).
load_dotenv(Path(__file__).resolve().parent / ".env")

def _sessions_root() -> Path:
    # Vercel functions cannot write back into the deployed code directory.
    # Use the OS temp area there, and keep the local folder layout for local dev.
    if os.environ.get("VERCEL"):
        return Path(tempfile.gettempdir()) / "adaptfit-sessions"
    return _repo_root() / "backend" / "sessions"


SESSIONS_DIR = _sessions_root()


def _now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _session_dir(session_id: str) -> Path:
    return (SESSIONS_DIR / session_id).resolve()


def _public_config() -> dict[str, str]:
    return {
        "SUPABASE_URL": os.environ.get("SUPABASE_URL", ""),
        "SUPABASE_ANON_KEY": os.environ.get("SUPABASE_ANON_KEY", ""),
        "API_BASE": os.environ.get("PUBLIC_API_BASE", ""),
    }


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _normalize_user_input_data(raw: dict[str, Any]) -> dict[str, Any]:
    age_raw = raw.get("age") or raw.get("inp_age") or raw.get("inp-age")
    try:
        age = int(age_raw)
    except Exception:
        age = None

    training_experience = raw.get("levelLabel") or raw.get("training_experience") or raw.get("level")
    activity_level = raw.get("activityLevelLabel") or raw.get("activity_level") or raw.get("activityLevel")

    goals = raw.get("goalLabels") or raw.get("goals")
    if isinstance(goals, str) and goals.strip():
        goals_list = [goals.strip()]
    elif isinstance(goals, list):
        goals_list = [str(x).strip() for x in goals if str(x).strip()]
    else:
        goals_list = []

    zone = raw.get("zone") or raw.get("affected_body_part")
    affected_body_part = {"knee": "Knee", "shoulder": "Shoulder"}.get(str(zone).lower(), zone)
    diagnosis = raw.get("injuryLabel") or raw.get("diagnosis") or raw.get("injury")
    date_of_injury = raw.get("date_of_injury") or raw.get("doi") or raw.get("inp-doi") or raw.get("inp_doi")

    pain = raw.get("pain_levels") or {}

    def _int(v: Any) -> int | None:
        try:
            return int(v)
        except Exception:
            return None

    daily_overall = _int(pain.get("daily_overall") if isinstance(pain, dict) else None) or _int(raw.get("pain_daily"))
    deep_squats = _int(pain.get("deep_squats") if isinstance(pain, dict) else None) or _int(raw.get("pain_squat"))
    stairs = _int(pain.get("stairs") if isinstance(pain, dict) else None) or _int(raw.get("pain_stairs"))

    functional_screening = raw.get("functional_screening")
    if not isinstance(functional_screening, list):
        functional_screening = []

    movement_limitations = raw.get("movement_limitations") or raw.get("limitations")
    if isinstance(movement_limitations, list):
        movement_limitations_list = [str(x).strip() for x in movement_limitations if str(x).strip()]
    else:
        movement_limitations_list = []

    return {
        "user_profile": {
            "age": age,
            "training_experience": training_experience,
            "activity_level": activity_level,
            "goals": goals_list,
        },
        "injury_details": {
            "affected_body_part": affected_body_part,
            "diagnosis": diagnosis,
            "date_of_injury": date_of_injury,
        },
        "assessments": {
            "pain_levels": {
                "daily_overall": daily_overall,
                "deep_squats": deep_squats,
                "stairs": stairs,
            },
            "functional_screening": functional_screening,
            "movement_limitations": movement_limitations_list,
        },
    }


def _json_rows_to_markdown_table(rows: list[dict[str, Any]]) -> str:
    headers = ["Current workout", "Risk", "Modified workout"]
    lines = [
        " | ".join(headers),
        " | ".join(["---", "---", "---"]),
    ]
    for row in rows:
        original = str(row.get("original", "")).replace("\n", " ").strip()
        modified = str(row.get("modified_alternative", "")).replace("\n", " ").strip()
        risk_flag = str(row.get("risk_flag", "")).replace("\n", " ").strip()
        lines.append(f"{original} | {risk_flag} | {modified}")
    return "\n".join(lines).strip() + "\n"


def _format_ts(seconds: Any) -> str:
    try:
        value = float(seconds)
    except Exception:
        return ""
    if value < 0:
        value = 0.0
    whole = int(round(value))
    minutes = whole // 60
    secs = whole % 60
    return f"{minutes:02d}:{secs:02d}"


def _gemini_temperature() -> float:
    raw = os.environ.get("GEMINI_TEMPERATURE", "0.3")
    try:
        return float((raw or "0.3").strip())
    except (TypeError, ValueError):
        return 0.3


def _groq_temperature() -> float:
    raw = os.environ.get("GROQ_TEMPERATURE", "0.3")
    try:
        return float((raw or "0.3").strip())
    except (TypeError, ValueError):
        return 0.3


def _adaptation_backend() -> str:
    explicit = (os.environ.get("ADAPTATION_BACKEND") or "").strip().lower()
    if explicit in ("groq", "gemini"):
        return explicit
    if os.environ.get("GROQ_API_KEY", "").strip():
        return "groq"
    return "gemini"


def _groq_failure_is_invalid_key_only(exc: BaseException) -> bool:
    try:
        import groq

        if isinstance(exc, groq.AuthenticationError):
            return True
    except Exception:
        pass
    msg = str(exc).lower()
    if "invalid api key" in msg or "incorrect api key" in msg:
        return True
    return "401" in msg and "api key" in msg


def _adaptation_fallback_gemini_enabled() -> bool:
    return os.environ.get("ADAPTATION_FALLBACK_GEMINI", "1").strip().lower() not in ("0", "false", "no")


def _groq_model_candidates() -> list[str]:
    combined = (os.environ.get("GROQ_ADAPTATION_MODELS") or "").strip()
    if combined:
        out = [m.strip() for m in combined.split(",") if m.strip()]
    else:
        primary = (os.environ.get("GROQ_ADAPTATION_MODEL") or "llama-3.3-70b-versatile").strip()
        fallbacks = (os.environ.get("GROQ_ADAPTATION_MODEL_FALLBACKS") or "").strip()
        out = [primary] if primary else ["llama-3.3-70b-versatile"]
        if fallbacks:
            out.extend(m.strip() for m in fallbacks.split(",") if m.strip())
    seen: set[str] = set()
    deduped: list[str] = []
    for m in out:
        if m not in seen:
            seen.add(m)
            deduped.append(m)
    return deduped


def _gemini_adaptation_model_candidates() -> list[str]:
    """Models for adaptation step, tried in order if one returns overload / transient errors."""
    combined = (os.environ.get("GEMINI_ADAPTATION_MODELS") or "").strip()
    if combined:
        out = [m.strip() for m in combined.split(",") if m.strip()]
    else:
        primary = (os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash").strip()
        fallbacks = (os.environ.get("GEMINI_ADAPTATION_MODEL_FALLBACKS") or "").strip()
        out = [primary] if primary else ["gemini-2.5-flash"]
        if fallbacks:
            out.extend(m.strip() for m in fallbacks.split(",") if m.strip())
        else:
            out.extend(
                m
                for m in (
                    "gemini-2.0-flash",
                    "gemini-2.5-flash-lite",
                    "gemini-1.5-flash",
                )
                if m not in out
            )
    seen: set[str] = set()
    deduped: list[str] = []
    for m in out:
        if m not in seen:
            seen.add(m)
            deduped.append(m)
    return deduped


def _attach_time_ranges(rows: list[dict[str, Any]], video_information: dict[str, Any]) -> None:
    chapters = (video_information.get("chapters") or []) if isinstance(video_information, dict) else []
    if not isinstance(chapters, list):
        return

    for index, row in enumerate(rows):
        chapter = chapters[index] if index < len(chapters) and isinstance(chapters[index], dict) else None
        if not isinstance(chapter, dict):
            row.setdefault("time_range", "")
            continue
        start_time = chapter.get("start_time")
        end_time = chapter.get("end_time")
        row["start_time"] = start_time
        row["end_time"] = end_time
        start_label = _format_ts(start_time)
        end_label = _format_ts(end_time)
        row["time_range"] = f"{start_label}-{end_label}" if start_label or end_label else ""


def _valid_reuse_video_information(vi: Any) -> bool:
    """True when client-sent cached timeline has chapters usable for adaptation."""
    if not isinstance(vi, dict):
        return False
    ch = vi.get("chapters")
    if not isinstance(ch, list) or len(ch) == 0:
        return False
    for c in ch:
        if isinstance(c, dict) and isinstance(c.get("start_time"), (int, float)):
            return True
    return False


def _video_information_from_reuse(youtube_url: str, cached: dict[str, Any]) -> dict[str, Any]:
    """Reuse saved Gemini timestamps directly without re-fetching YouTube metadata."""
    chapters = list(cached.get("chapters") or [])
    duration = 0
    for chapter in chapters:
        if isinstance(chapter, dict):
            try:
                duration = max(duration, int(chapter.get("end_time") or 0))
            except Exception:
                continue
    out = dict(cached)
    out["title"] = cached.get("title") or cached.get("video_title") or "Workout Video"
    out["duration"] = int(cached.get("duration") or duration or 0)
    out["id"] = cached.get("id") or cached.get("youtube_video_id") or ""
    out["channel"] = cached.get("channel") or ""
    out["webpage_url"] = cached.get("webpage_url") or youtube_url
    out["description"] = cached.get("description") or ""
    out["chapters"] = chapters
    out["adaptfit_phase"] = "reused_saved_timeline"
    out["adaptfit_youtube_url"] = youtube_url
    return out


def _run_gemini_adaptation(
    session_id: str,
    user_input_data: dict[str, Any],
    video_information: dict[str, Any],
    output_format: Literal["json", "markdown", "both"],
) -> tuple[list[dict[str, Any]], str, Path, Path, Path]:
    session_dir = _session_dir(session_id)
    stamp = _now_stamp()
    combined = {
        "user_input_data": user_input_data,
        "video_information": video_information,
    }
    combined_path = session_dir / f"workout_adaptation_input_{stamp}.json"
    _write_json(combined_path, combined)

    user_block, video_block = load_adaptation_input_json(combined_path)
    user_message = build_user_message(user_block, video_block)

    backend = _adaptation_backend()
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()

    reply: str | None = None
    try:
        if backend == "groq":
            if not groq_key:
                raise HTTPException(
                    status_code=500,
                    detail="ADAPTATION_BACKEND=groq but GROQ_API_KEY is not set",
                )
            try:
                reply = run_groq_adaptation_try_models(
                    user_message,
                    api_key=groq_key,
                    system_prompt=SYSTEM_PROMPT_ADAPTATION_PHASE2,
                    models=_groq_model_candidates(),
                    temperature=_groq_temperature(),
                )
            except Exception as groq_exc:
                if gemini_key and _adaptation_fallback_gemini_enabled():
                    log.warning("Groq adaptation failed (%s); falling back to Gemini.", groq_exc)
                    try:
                        reply = run_gemini_adaptation_try_models(
                            user_message,
                            api_key=gemini_key,
                            system_prompt=SYSTEM_PROMPT_ADAPTATION_PHASE2,
                            models=_gemini_adaptation_model_candidates(),
                            temperature=_gemini_temperature(),
                        )
                    except Exception as gem_exc:
                        if _groq_failure_is_invalid_key_only(groq_exc):
                            raise HTTPException(
                                status_code=502,
                                detail=(
                                    "GROQ_API_KEY is invalid or revoked (401). Replace it at "
                                    "https://console.groq.com/keys or set ADAPTATION_BACKEND=gemini in your "
                                    "environment so adaptation uses only Gemini (skips Groq). "
                                    f"Gemini attempt(s) also failed: {gem_exc!s}"
                                ),
                            ) from gem_exc
                        raise HTTPException(
                            status_code=502,
                            detail=(
                                f"Groq failed: {groq_exc!s}. "
                                f"Gemini fallback also failed: {gem_exc!s}"
                            ),
                        ) from gem_exc
                elif not gemini_key:
                    if _groq_failure_is_invalid_key_only(groq_exc):
                        raise HTTPException(
                            status_code=502,
                            detail=(
                                "Invalid GROQ_API_KEY. Replace it with a key from https://console.groq.com/keys "
                                "or set GEMINI_API_KEY so adaptation can fall back, or use ADAPTATION_BACKEND=gemini."
                            ),
                        ) from groq_exc
                    raise HTTPException(
                        status_code=503,
                        detail=(
                            "Groq request failed and GEMINI_API_KEY is not set. "
                            "Add GEMINI_API_KEY for automatic fallback when Groq is overloaded, "
                            "or try again later."
                        ),
                    ) from groq_exc
                else:
                    raise HTTPException(
                        status_code=503,
                        detail=(
                            f"Groq adaptation failed: {groq_exc!s}. "
                            "Set ADAPTATION_FALLBACK_GEMINI=1 to use Gemini when Groq fails, "
                            "or ADAPTATION_BACKEND=gemini to skip Groq."
                        ),
                    ) from groq_exc
        else:
            if not gemini_key:
                raise HTTPException(
                    status_code=500,
                    detail="GEMINI_API_KEY is not set (needed when ADAPTATION_BACKEND=gemini or no GROQ_API_KEY)",
                )
            reply = run_gemini_adaptation_try_models(
                user_message,
                api_key=gemini_key,
                system_prompt=SYSTEM_PROMPT_ADAPTATION_PHASE2,
                models=_gemini_adaptation_model_candidates(),
                temperature=_gemini_temperature(),
            )
    except HTTPException:
        raise
    except Exception as exc:
        label = "Groq" if backend == "groq" else "Gemini"
        raise HTTPException(status_code=502, detail=f"{label} adaptation request failed: {exc}") from exc

    if reply is None:
        raise HTTPException(status_code=502, detail="Adaptation produced no response")

    try:
        rows = parse_adaptation_json(reply)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to parse adaptation JSON output: {exc}") from exc

    _attach_time_ranges(rows, video_information)

    result_json_path = session_dir / f"workout_adaptation_output_{stamp}.json"
    _write_json(result_json_path, rows)

    markdown_table = _json_rows_to_markdown_table(rows)
    result_md_path = session_dir / f"workout_adaptation_output_{stamp}.md"
    result_md_path.write_text(markdown_table, encoding="utf-8")

    return rows, markdown_table, combined_path, result_json_path, result_md_path


class SurveyIn(BaseModel):
    raw: dict[str, Any] = Field(default_factory=dict)


class SurveyOut(BaseModel):
    session_id: str
    user_input_data: dict[str, Any]
    saved_path: str


class AdaptWorkoutIn(BaseModel):
    session_id: str
    output_format: Literal["json", "markdown", "both"] = "both"
    source: Literal["youtube", "text"]
    youtube_url: str | None = None
    workout_text: str | None = None
    user_input_data: dict[str, Any] | None = None
    # Same video as a prior run: skip Gemini timeline; use these chapters for adaptation.
    reuse_video_information: dict[str, Any] | None = Field(default=None)

    @model_validator(mode="after")
    def _require_fields_for_source(self) -> "AdaptWorkoutIn":
        if self.source == "youtube" and not (self.youtube_url or "").strip():
            raise ValueError("youtube_url is required when source is youtube")
        if self.source == "text" and not (self.workout_text or "").strip():
            raise ValueError("workout_text is required when source is text")
        return self


class AdaptWorkoutOut(BaseModel):
    session_id: str
    source: Literal["youtube", "text"]
    youtube_url: str | None = None
    combined_input_json_path: str
    result_json_path: str
    result_markdown_path: str | None = None
    result_json: list[dict[str, Any]] | None = None
    result_markdown_table: str | None = None
    video_information: dict[str, Any] | None = None
    reuse_timeline_used: bool = False


app = FastAPI(title="Deploy App Analysis Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/public-config")
@app.get("/api/public-config")
def public_config() -> Response:
    payload = json.dumps(_public_config(), ensure_ascii=False)
    body = f"window.APP_CONFIG = Object.assign(window.APP_CONFIG || {{}}, {payload});"
    return Response(content=body, media_type="application/javascript")


@app.post("/survey", response_model=SurveyOut)
@app.post("/api/survey", response_model=SurveyOut)
def api_survey(payload: SurveyIn) -> SurveyOut:
    session_id = uuid.uuid4().hex
    user_input_data = _normalize_user_input_data(payload.raw)
    session_dir = _session_dir(session_id)

    saved_path = session_dir / "user_input_data.json"
    _write_json(saved_path, user_input_data)
    _write_json(session_dir / "survey_raw.json", payload.raw)

    return SurveyOut(
        session_id=session_id,
        user_input_data=user_input_data,
        saved_path=str(saved_path),
    )


@app.post("/adapt/workout", response_model=AdaptWorkoutOut)
@app.post("/api/adapt/workout", response_model=AdaptWorkoutOut)
def api_adapt_workout(payload: AdaptWorkoutIn) -> AdaptWorkoutOut:
    session_dir = _session_dir(payload.session_id)
    user_path = session_dir / "user_input_data.json"
    if user_path.is_file():
        user_input_data = json.loads(user_path.read_text(encoding="utf-8"))
    elif payload.user_input_data is not None:
        user_input_data = payload.user_input_data
        _write_json(user_path, user_input_data)
    else:
        raise HTTPException(status_code=404, detail="session_id not found (missing user_input_data.json)")

    reuse_timeline_used = False
    video_information: dict[str, Any]
    youtube_url: str | None

    if payload.source == "youtube":
        youtube_url = (payload.youtube_url or "").strip()
        if payload.reuse_video_information is not None and _valid_reuse_video_information(
            payload.reuse_video_information
        ):
            try:
                video_information = _video_information_from_reuse(
                    youtube_url, dict(payload.reuse_video_information)
                )
                reuse_timeline_used = True
            except Exception as exc:
                log.warning("Saved timeline reuse failed; regenerating with Gemini. %s", exc)
                video_information, _ = build_video_information_gemini_adaptfit(youtube_url)
        else:
            video_information, _ = build_video_information_gemini_adaptfit(youtube_url)
    else:
        youtube_url = None
        video_information = video_information_from_pasted_text((payload.workout_text or "").strip())

    rows, markdown_table, combined_path, result_json_path, result_md_path = _run_gemini_adaptation(
        payload.session_id,
        user_input_data,
        video_information,
        payload.output_format,
    )

    response = AdaptWorkoutOut(
        session_id=payload.session_id,
        source=payload.source,
        youtube_url=youtube_url,
        combined_input_json_path=str(combined_path),
        result_json_path=str(result_json_path),
        result_markdown_path=str(result_md_path),
        video_information=video_information if payload.source == "youtube" else None,
        reuse_timeline_used=reuse_timeline_used,
    )
    if payload.output_format in ("json", "both"):
        response.result_json = rows
    if payload.output_format in ("markdown", "both"):
        response.result_markdown_table = markdown_table
    return response

