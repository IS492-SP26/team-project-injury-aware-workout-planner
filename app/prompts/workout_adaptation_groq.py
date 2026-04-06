#!/usr/bin/env python3
"""
Rehabilitation-focused workout adaptation via Groq (Llama 3.3 70B).

By default, reads ``user_input_data`` and ``video_information`` from
``workout_adaptation_input.json`` next to this script (no YouTube URL required).
Optionally, pass a YouTube URL to pull metadata with yt-dlp and use Markdown user data.

Setup:
  Put your key in the project root ``.env`` as ``GROQ_API_KEY=gsk_...`` (no quotes needed), or:
  export GROQ_API_KEY="gsk_..."
  pip install groq yt-dlp
  pip install certifi   # optional; helps TLS on some macOS setups

Example (fetch video from YouTube):
  python app/prompts/workout_adaptation_groq.py \\
    --user-markdown path/to/profile.md \\
    "https://www.youtube.com/watch?v=VIDEO_ID"

Example (default — edit ``workout_adaptation_input.json`` beside this script):
  python app/prompts/workout_adaptation_groq.py

Example (custom JSON path):
  python app/prompts/workout_adaptation_groq.py --input-json path/to/custom.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from textwrap import dedent


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_dotenv() -> None:
    """Load repo-root ``.env`` into ``os.environ`` (no ``python-dotenv`` required)."""
    env_path = _repo_root() / ".env"
    if not env_path.is_file():
        return
    try:
        text = env_path.read_text(encoding="utf-8-sig")
    except OSError:
        return
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if not key:
            continue
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        os.environ.setdefault(key, val)

    try:
        from dotenv import load_dotenv  # type: ignore[import-untyped]

        load_dotenv(env_path, override=False)
    except ImportError:
        pass


def _use_certifi_ca_bundle() -> None:
    try:
        import certifi
    except ImportError:
        return
    bundle = certifi.where()
    if bundle:
        os.environ.setdefault("SSL_CERT_FILE", bundle)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", bundle)


_load_dotenv()
_use_certifi_ca_bundle()

try:
    from groq import Groq
    from yt_dlp import YoutubeDL
except ImportError as e:
    print("Missing dependency. Install with: pip install groq yt-dlp", file=sys.stderr)
    raise SystemExit(1) from e


DEFAULT_MODEL = "llama-3.3-70b-versatile"
DEFAULT_WORKOUT_INPUT_JSON = Path(__file__).resolve().parent / "workout_adaptation_input.json"
DESCRIPTION_MAX_CHARS = 12_000

SYSTEM_PROMPT = dedent("""\
    You are a rehabilitation-focused workout adaptation assistant.
    You are not a substitute for in-person medical care; give practical, conservative
    exercise guidance only. If information is missing, state assumptions briefly.

    Respond in clear Markdown with these sections:
    ## Summary
    Brief overview for this user and video.

    ## Movement risk review
    A table or bullet list: each distinct movement or segment from the video, with
    risk level **High**, **Medium**, or **Low**, one-line rationale tied to the user's profile.

    ## Modified alternatives
    For every **High** and **Medium** risk item, suggest 1 concrete alternative
    movements or regressions (equipment, range, tempo, support, unilateral vs bilateral).

    ## Cautions
    When to stop, seek clinician input, or avoid the workout entirely.
    """)


def load_user_markdown(path: str | Path | None) -> str:
    """Load raw markdown from a path, or stdin when path is '-' or None."""
    if path is None or str(path) == "-":
        return sys.stdin.read()
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"User markdown file not found: {p}")
    return p.read_text(encoding="utf-8")


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


def fetch_video_information(url: str) -> str:
    """Return a human-readable block for the LLM by fetching public YouTube metadata."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "skip_download": True,
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    return format_video_information_from_dict(
        {
            "title": info.get("title"),
            "id": info.get("id"),
            "channel": info.get("channel") or info.get("uploader"),
            "duration": info.get("duration"),
            "webpage_url": info.get("webpage_url") or url,
            "chapters": info.get("chapters") or [],
            "description": info.get("description") or "",
        },
        fallback_url=url,
    )


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
    user_block = json.dumps(user_obj, indent=2, ensure_ascii=False)
    video_block = format_video_information_from_dict(video_obj)
    return user_block, video_block


def build_user_message(user_input_data: str, video_information: str) -> str:
    return dedent(f"""\
        Use the following user profile, injury detail, and functional assessment data:

        {user_input_data.strip()}

        ---

        The user wants to continue following a YouTube workout video. The video information is as follows:

        {video_information.strip()}

        ---

        Your task is:
        1. Flag each movement with a high, medium, or low risk level.
        2. Suggest modified alternative movements for all high- and medium-risk movements.

        Follow the response structure described in your system instructions.
        """)


def run_groq(
    user_message: str,
    *,
    api_key: str,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.3,
) -> str:
    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model=model,
        temperature=temperature,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    return (completion.choices[0].message.content or "").strip()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Adapt a YouTube workout to the user's rehab context via Groq."
    )
    parser.add_argument(
        "youtube_url",
        nargs="?",
        default=None,
        help="If set, fetch video metadata from YouTube instead of using JSON.",
    )
    parser.add_argument(
        "--input-json",
        metavar="PATH",
        help=(
            "JSON with 'user_input_data' and 'video_information'. "
            f"If you omit this and no YouTube URL is given, uses {DEFAULT_WORKOUT_INPUT_JSON.name} "
            "next to this script."
        ),
    )
    parser.add_argument(
        "-u",
        "--user-markdown",
        default="-",
        metavar="PATH",
        help="With a YouTube URL: markdown user data (default: read stdin). Ignored when using JSON-only mode.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("GROQ_MODEL", DEFAULT_MODEL),
        help=f"Groq chat model id (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.3,
        help="Sampling temperature (default: 0.3).",
    )
    args = parser.parse_args()

    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        print(
            "GROQ_API_KEY is not set. Export it, e.g. export GROQ_API_KEY='gsk_...'",
            file=sys.stderr,
        )
        raise SystemExit(1)

    if args.youtube_url:
        try:
            user_md = load_user_markdown(args.user_markdown)
        except FileNotFoundError as e:
            print(e, file=sys.stderr)
            raise SystemExit(1) from e

        try:
            video_block = fetch_video_information(args.youtube_url)
        except Exception as e:
            print(f"Failed to fetch video metadata: {e}", file=sys.stderr)
            raise SystemExit(1) from e
    else:
        json_path = Path(args.input_json) if args.input_json else DEFAULT_WORKOUT_INPUT_JSON
        if not json_path.is_file():
            print(
                "No YouTube URL was given.\n"
                f"Expected JSON at: {json_path}\n"
                "Create that file, or pass --input-json PATH, or pass a YouTube URL as the first argument.",
                file=sys.stderr,
            )
            raise SystemExit(1)
        try:
            user_md, video_block = load_adaptation_input_json(json_path)
        except (FileNotFoundError, ValueError, TypeError, json.JSONDecodeError) as e:
            print(f"Failed to load JSON input: {e}", file=sys.stderr)
            raise SystemExit(1) from e

    user_message = build_user_message(user_md, video_block)
    try:
        reply = run_groq(
            user_message,
            api_key=api_key,
            model=args.model,
            temperature=args.temperature,
        )
    except Exception as e:
        print(f"Groq API error: {e}", file=sys.stderr)
        raise SystemExit(1) from e

    print(reply)


if __name__ == "__main__":
    main()
