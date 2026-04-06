#!/usr/bin/env python3
"""
Download a YouTube video with yt-dlp and split it into separate files using chapter
metadata from the site (same end result as the CLI flag ``--split-chapters``).

When using the Python API, ``split_chapters=True`` is *not* wired up; you must add
the ``FFmpegSplitChapters`` entry to ``postprocessors`` (this script does that).
See: https://github.com/yt-dlp/yt-dlp

Dependencies:
  pip install yt-dlp
  pip install certifi   (recommended on macOS if you see CERTIFICATE_VERIFY_FAILED)
  ffmpeg and ffprobe on your PATH (required for merge/split)

On macOS with python.org builds, you can also run ``Install Certificates.command`` from the Python folder in Applications.

Reference: https://github.com/yt-dlp/yt-dlp
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path


def _use_certifi_ca_bundle() -> None:
    """Use certifi's Mozilla CA bundle for HTTPS (fixes common macOS SSL errors)."""
    try:
        import certifi
    except ImportError:
        return
    bundle = certifi.where()
    if not bundle:
        return
    os.environ.setdefault("SSL_CERT_FILE", bundle)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", bundle)


# Set CA paths before importing yt-dlp so urllib3/requests pick them up.
_use_certifi_ca_bundle()

try:
    from yt_dlp import YoutubeDL
    from yt_dlp.utils import sanitize_filename
except ImportError:
    print("Missing dependency. Install with: pip install yt-dlp", file=sys.stderr)
    raise SystemExit(1) from None

# Default: single video (playlist/query params stripped so we do not fetch the whole list)
DEFAULT_URL = "https://www.youtube.com/watch?v=AS7t3doAEdw&list=PL2ov72VWpiOpzZHrFcq2-k8U6l-lGLa9Y&index=3"


def _resolve_ffmpeg() -> str | None:
    """
    Return path to the ffmpeg binary.

    Checks PATH, FFMPEG_BINARY, then common install locations (Homebrew on Apple
    Silicon / Intel macOS) so runs from IDEs still find ffmpeg when PATH is minimal.
    """
    env = os.environ.get("FFMPEG_BINARY", "").strip()
    if env:
        p = Path(env).expanduser()
        if p.is_file():
            return str(p.resolve())
    w = shutil.which("ffmpeg")
    if w:
        return w
    for candidate in (
        Path("/opt/homebrew/bin/ffmpeg"),
        Path("/usr/local/bin/ffmpeg"),
    ):
        if candidate.is_file():
            return str(candidate.resolve())
    return None


def _require_ffmpeg() -> str:
    """Merge (best video + audio) and split-chapters both need ffmpeg."""
    path = _resolve_ffmpeg()
    if path:
        return path
    print(
        "ffmpeg was not found. It is required to:\n"
        "  - merge separate video and audio streams (format bv*+ba/b), and\n"
        "  - split the file by chapter markers.\n\n"
        "Install ffmpeg, then try again. Examples:\n"
        "  macOS (Homebrew):  brew install ffmpeg\n"
        "  Ubuntu/Debian:     sudo apt install ffmpeg\n"
        "  Windows:           https://ffmpeg.org/download.html\n\n"
        "Or set FFMPEG_BINARY to the full path of the ffmpeg executable.\n",
        file=sys.stderr,
    )
    raise SystemExit(1)


def _chapters_manifest_hook(output_dir: Path):
    """
    After SplitChapters finishes, write ``<sanitized title>.json`` next to the video files
    (inside the per-video folder created from ``%(title)s/`` in outtmpl).
    """
    output_dir = output_dir.resolve()

    def hook(d: dict) -> None:
        if d.get("status") != "finished" or d.get("postprocessor") != "SplitChapters":
            return
        info = d.get("info_dict") or {}
        chapters = info.get("chapters") or []
        if not chapters:
            return
        vid = info.get("id") or "video"
        raw_title = info.get("title")
        if raw_title:
            file_stem = sanitize_filename(str(raw_title), restricted=False)
            if not file_stem or file_stem.strip("_") == "":
                file_stem = vid
        else:
            file_stem = vid
        fp = info.get("filepath")
        if fp:
            dest_dir = Path(fp).resolve().parent
        else:
            dest_dir = output_dir / file_stem
        dest_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "id": vid,
            "title": info.get("title"),
            "webpage_url": info.get("webpage_url"),
            "chapters": [
                {
                    "index": i + 1,
                    "title": c.get("title"),
                    "start_time": c.get("start_time"),
                    "end_time": c.get("end_time"),
                }
                for i, c in enumerate(chapters)
            ],
        }
        path = dest_dir / f"{file_stem}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return hook


def build_options(
    output_dir: Path,
    *,
    ffmpeg_location: str | None = None,
    no_check_certificate: bool = False,
    write_info_json: bool = False,
    force_keyframes_at_cuts: bool = False,
) -> dict:
    """Options passed to yt-dlp's Python API (mirror of common CLI flags)."""
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    opts: dict = {
        # One video only when the link also contains &list=...
        "noplaylist": True,
        # Best video+audio, merged (needs ffmpeg)
        "format": "bv*+ba/b",
        "merge_output_format": "mp4",
        # NOTE: Unlike the yt-dlp CLI, YoutubeDL ignores bare split_chapters=True.
        # Register the postprocessor explicitly (same as --split-chapters).
        "postprocessors": [
            {
                "key": "FFmpegSplitChapters",
                "force_keyframes": force_keyframes_at_cuts,
            },
        ],
        # Root output dir; each video goes under a subfolder named from its title.
        "paths": {"home": str(output_dir)},
        "outtmpl": {
            "default": "%(title)s/%(title)s [%(id)s].%(ext)s",
            "chapter": "%(title)s/%(section_number)03d - %(section_title)s [%(id)s].%(ext)s",
            # Keeps .info.json beside the video when --write-info-json is used
            "infojson": "%(title)s/%(title)s [%(id)s].info.json",
        },
        "postprocessor_hooks": [_chapters_manifest_hook(output_dir)],
    }
    if write_info_json:
        opts["writeinfojson"] = True
    if ffmpeg_location:
        # Same as CLI --ffmpeg-location (binary path or its directory)
        opts["ffmpeg_location"] = ffmpeg_location
    if no_check_certificate:
        opts["nocheckcertificate"] = True
    return opts


def download_and_split(
    url: str,
    output_dir: Path,
    *,
    ffmpeg_location: str | None = None,
    no_check_certificate: bool = False,
    write_info_json: bool = False,
    force_keyframes_at_cuts: bool = False,
) -> int:
    """
    Returns yt-dlp's exit code (0 = success).
    Output layout: ``output_dir/<sanitized title>/`` with the merged file, chapter clips,
    and ``<title>.json`` (sanitized). If the video has no chapters, you typically get one full file only.
    """
    opts = build_options(
        output_dir,
        ffmpeg_location=ffmpeg_location,
        no_check_certificate=no_check_certificate,
        write_info_json=write_info_json,
        force_keyframes_at_cuts=force_keyframes_at_cuts,
    )
    with YoutubeDL(opts) as ydl:
        return ydl.download([url])


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download a YouTube URL and split into chapter files via yt-dlp."
    )
    parser.add_argument(
        "url",
        nargs="?",
        default=DEFAULT_URL,
        help=f"YouTube URL (default: {DEFAULT_URL})",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "downloads",
        help="Root directory; each video is stored in a subfolder named from its title (default: ./downloads next to this script)",
    )
    parser.add_argument(
        "--no-check-certificates",
        action="store_true",
        help="Disable TLS certificate verification (insecure; only if SSL errors remain).",
    )
    parser.add_argument(
        "--write-info-json",
        action="store_true",
        help="Also write yt-dlp's full %(title)s [%(id)s].info.json (includes raw chapters).",
    )
    parser.add_argument(
        "--force-keyframes-at-cuts",
        action="store_true",
        help="Re-encode around chapter cuts for cleaner splits (slow; optional).",
    )
    args = parser.parse_args()

    ffmpeg_path = _require_ffmpeg()
    code = download_and_split(
        args.url,
        args.output_dir,
        ffmpeg_location=ffmpeg_path,
        no_check_certificate=args.no_check_certificates,
        write_info_json=args.write_info_json,
        force_keyframes_at_cuts=args.force_keyframes_at_cuts,
    )
    if code != 0:
        raise SystemExit(code)


if __name__ == "__main__":
    main()
