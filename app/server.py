from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

import app.prompts.prompt_groq as groq_runner
from app.util.yt_split.chapters_metadata import fetch_video_information


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


SESSIONS_DIR = _repo_root() / "app" / "prompts" / "sessions"


def _now_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _session_dir(session_id: str) -> Path:
    return (SESSIONS_DIR / session_id).resolve()


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _normalize_user_input_data(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Map onboarding raw payload into the `user_input_data` schema consumed by Groq.
    """
    # Age
    age_raw = raw.get("age") or raw.get("inp_age") or raw.get("inp-age")
    try:
        age = int(age_raw)
    except Exception:
        age = None

    # Training experience
    training_experience = raw.get("levelLabel") or raw.get("training_experience") or raw.get("level")

    # Activity level (new module in onboarding)
    activity_level = raw.get("activityLevelLabel") or raw.get("activity_level") or raw.get("activityLevel")

    # Goals (multi-select)
    goals = raw.get("goalLabels") or raw.get("goals")
    if isinstance(goals, str) and goals.strip():
        goals_list = [goals.strip()]
    elif isinstance(goals, list):
        goals_list = [str(x).strip() for x in goals if str(x).strip()]
    else:
        goals_list = []

    # Injury details
    zone = raw.get("zone") or raw.get("affected_body_part")
    affected_body_part = {"knee": "Knee", "shoulder": "Shoulder"}.get(str(zone).lower(), zone)
    diagnosis = raw.get("injuryLabel") or raw.get("diagnosis") or raw.get("injury")
    date_of_injury = raw.get("date_of_injury") or raw.get("doi") or raw.get("inp-doi") or raw.get("inp_doi")

    # Pain levels
    pain = raw.get("pain_levels") or {}

    def _int(v: Any) -> int | None:
        try:
            return int(v)
        except Exception:
            return None

    daily_overall = _int(pain.get("daily_overall") if isinstance(pain, dict) else None) or _int(raw.get("pain_daily"))
    deep_squats = _int(pain.get("deep_squats") if isinstance(pain, dict) else None) or _int(raw.get("pain_squat"))
    stairs = _int(pain.get("stairs") if isinstance(pain, dict) else None) or _int(raw.get("pain_stairs"))

    # Functional screening
    functional_screening = raw.get("functional_screening")
    if not isinstance(functional_screening, list):
        functional_screening = []

    # Movement limitations
    movement_limitations = raw.get("movement_limitations") or raw.get("limitations")
    if isinstance(movement_limitations, list):
        movement_limitations_list = [str(x).strip() for x in movement_limitations if str(x).strip()]
    else:
        movement_limitations_list = []

    user_input_data = {
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
    return user_input_data


def _json_rows_to_markdown_table(rows: list[dict[str, Any]]) -> str:
    headers = ["time_range", "original", "modified_alternative", "risk_flag"]
    lines = [
        " | ".join(headers),
        " | ".join(["---", "---", "---", "---"]),
    ]
    for r in rows:
        t = str(r.get("time_range", "")).replace("\n", " ").strip()
        o = str(r.get("original", "")).replace("\n", " ").strip()
        m = str(r.get("modified_alternative", "")).replace("\n", " ").strip()
        f = str(r.get("risk_flag", "")).replace("\n", " ").strip()
        lines.append(f"{t} | {o} | {m} | {f}")
    return "\n".join(lines).strip() + "\n"


def _format_ts(seconds: Any) -> str:
    try:
        s = float(seconds)
    except Exception:
        return ""
    if s < 0:
        s = 0.0
    whole = int(round(s))
    mm = whole // 60
    ss = whole % 60
    return f"{mm:02d}:{ss:02d}"


def _attach_time_ranges(rows: list[dict[str, Any]], video_information: dict[str, Any]) -> None:
    chapters = (video_information.get("chapters") or []) if isinstance(video_information, dict) else []
    if isinstance(chapters, list):
        for i, r in enumerate(rows):
            ch = chapters[i] if i < len(chapters) and isinstance(chapters[i], dict) else None
            if isinstance(ch, dict):
                st = ch.get("start_time")
                et = ch.get("end_time")
                r["start_time"] = st
                r["end_time"] = et
                st_s = _format_ts(st)
                et_s = _format_ts(et)
                r["time_range"] = f"{st_s}–{et_s}" if st_s or et_s else ""
            else:
                r.setdefault("time_range", "")


def _run_groq_adaptation(
    session_id: str,
    user_input_data: dict[str, Any],
    video_information: dict[str, Any],
    output_format: Literal["json", "markdown", "both"],
) -> tuple[list[dict[str, Any]], str, Path, Path, Path]:
    """Persist combined input, run Groq, persist outputs. Returns rows, md_table, paths."""
    sdir = _session_dir(session_id)
    combined = {
        "user_input_data": user_input_data,
        "video_information": video_information,
    }
    stamp = _now_stamp()
    combined_path = sdir / f"workout_adaptation_input_{stamp}.json"
    _write_json(combined_path, combined)

    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not set on the server")

    user_md, video_block = groq_runner.load_adaptation_input_json(combined_path)
    user_message = groq_runner.build_user_message(user_md, video_block)
    reply = groq_runner.run_groq(
        user_message,
        api_key=api_key,
        system_prompt=groq_runner.SYSTEM_PROMPT_JSON,
        model=os.environ.get("GROQ_MODEL", groq_runner.DEFAULT_MODEL),
        temperature=float(os.environ.get("GROQ_TEMPERATURE", "0.3")),
    )

    try:
        rows = json.loads(reply)
        if not isinstance(rows, list):
            raise ValueError("Groq JSON output is not a list")
        rows = [r for r in rows if isinstance(r, dict)]
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to parse Groq JSON output: {e}") from e

    _attach_time_ranges(rows, video_information)

    result_json_path = sdir / f"workout_adaptation_output_{stamp}.json"
    _write_json(result_json_path, rows)

    md_table = _json_rows_to_markdown_table(rows)
    result_md_path = sdir / f"workout_adaptation_output_{stamp}.md"
    result_md_path.write_text(md_table, encoding="utf-8")

    return rows, md_table, combined_path, result_json_path, result_md_path


class SurveyIn(BaseModel):
    raw: dict[str, Any] = Field(default_factory=dict)


class SurveyOut(BaseModel):
    session_id: str
    user_input_data: dict[str, Any]
    saved_path: str


class AdaptYoutubeIn(BaseModel):
    session_id: str
    youtube_url: str
    output_format: Literal["json", "markdown", "both"] = "both"


class AdaptYoutubeOut(BaseModel):
    session_id: str
    youtube_url: str
    combined_input_json_path: str
    result_json_path: str
    result_markdown_path: str | None = None
    result_json: list[dict[str, Any]] | None = None
    result_markdown_table: str | None = None


class AdaptWorkoutIn(BaseModel):
    session_id: str
    output_format: Literal["json", "markdown", "both"] = "both"
    source: Literal["youtube", "text"]
    youtube_url: str | None = None
    workout_text: str | None = None

    @model_validator(mode="after")
    def _require_fields_for_source(self) -> AdaptWorkoutIn:
        if self.source == "youtube":
            if not (self.youtube_url or "").strip():
                raise ValueError("youtube_url is required when source is youtube")
        elif self.source == "text":
            if not (self.workout_text or "").strip():
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


app = FastAPI(title="AdaptFit AI Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    # Demo-friendly: allow requests from file:// (Origin: null) and any local dev host.
    # We don't use cookies for auth here, so disable credentials to avoid CORS incompatibilities.
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/survey", response_model=SurveyOut)
def api_survey(payload: SurveyIn) -> SurveyOut:
    session_id = uuid.uuid4().hex
    user_input_data = _normalize_user_input_data(payload.raw)
    sdir = _session_dir(session_id)

    saved_path = sdir / "user_input_data.json"
    _write_json(saved_path, user_input_data)
    _write_json(sdir / "survey_raw.json", payload.raw)

    return SurveyOut(
        session_id=session_id,
        user_input_data=user_input_data,
        saved_path=str(saved_path),
    )


@app.post("/api/adapt/workout", response_model=AdaptWorkoutOut)
def api_adapt_workout(payload: AdaptWorkoutIn) -> AdaptWorkoutOut:
    sdir = _session_dir(payload.session_id)
    user_path = sdir / "user_input_data.json"
    if not user_path.is_file():
        raise HTTPException(status_code=404, detail="session_id not found (missing user_input_data.json)")

    user_input_data = json.loads(user_path.read_text(encoding="utf-8"))

    if payload.source == "youtube":
        url = (payload.youtube_url or "").strip()
        video_information = fetch_video_information(url)
        youtube_url_out: str | None = url
    else:
        text = (payload.workout_text or "").strip()
        video_information = groq_runner.video_information_from_pasted_text(text)
        youtube_url_out = None

    rows, md_table, combined_path, result_json_path, result_md_path = _run_groq_adaptation(
        payload.session_id,
        user_input_data,
        video_information,
        payload.output_format,
    )

    out = AdaptWorkoutOut(
        session_id=payload.session_id,
        source=payload.source,
        youtube_url=youtube_url_out,
        combined_input_json_path=str(combined_path),
        result_json_path=str(result_json_path),
        result_markdown_path=str(result_md_path),
    )
    if payload.output_format in ("json", "both"):
        out.result_json = rows
    if payload.output_format in ("markdown", "both"):
        out.result_markdown_table = md_table
    return out


@app.post("/api/adapt/youtube", response_model=AdaptYoutubeOut)
def api_adapt_youtube(payload: AdaptYoutubeIn) -> AdaptYoutubeOut:
    """Backward-compatible alias for `POST /api/adapt/workout` with source=youtube."""
    sdir = _session_dir(payload.session_id)
    user_path = sdir / "user_input_data.json"
    if not user_path.is_file():
        raise HTTPException(status_code=404, detail="session_id not found (missing user_input_data.json)")

    user_input_data = json.loads(user_path.read_text(encoding="utf-8"))
    video_information = fetch_video_information(payload.youtube_url)

    rows, md_table, combined_path, result_json_path, result_md_path = _run_groq_adaptation(
        payload.session_id,
        user_input_data,
        video_information,
        payload.output_format,
    )

    out = AdaptYoutubeOut(
        session_id=payload.session_id,
        youtube_url=payload.youtube_url,
        combined_input_json_path=str(combined_path),
        result_json_path=str(result_json_path),
        result_markdown_path=str(result_md_path),
    )

    if payload.output_format in ("json", "both"):
        out.result_json = rows
    if payload.output_format in ("markdown", "both"):
        out.result_markdown_table = md_table
    return out
