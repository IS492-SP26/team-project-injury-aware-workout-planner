/**
 * Maps Groq analysis rows into the same JSON shape as AdaptFitAI `data/workout_video.json`
 * (`youtube_video_id`, `title`, `segments[]` with `start_time_seconds`, `workout`,
 * `modified_workout_text`, `risk_flag`, `modified_workout_gif_url`, optional `section` / `notes`).
 */

import { extractYouTubeVideoId } from "./youtube-player.js";

export const ADAPTFIT_SAFE_LABEL = "Proceed with Current workout";

/**
 * Infer start/end seconds on raw API rows (same rules as results playback).
 * @param {Array<Record<string, unknown>>} rows
 */
function inferTimesOnAnalysisRows(rows) {
  const list = (rows || []).map((r) => ({ ...r }));
  for (let i = 0; i < list.length; i += 1) {
    let st = list[i].start_time;
    let et = list[i].end_time;
    st = st != null && st !== "" ? Number(st) : NaN;
    et = et != null && et !== "" ? Number(et) : NaN;
    const next = list[i + 1];
    const nextSt = next != null && next.start_time != null && next.start_time !== "" ? Number(next.start_time) : NaN;
    if (!Number.isFinite(et)) {
      if (Number.isFinite(nextSt)) et = nextSt;
      else if (Number.isFinite(st)) et = st + 30;
      else et = NaN;
    }
    if (!Number.isFinite(st)) st = 0;
    if (Number.isFinite(et) && et <= st) et = st + 15;
    list[i].start_time = st;
    list[i].end_time = et;
  }
  return list;
}

/**
 * @param {Array<Record<string, unknown>>} rows - Groq `result_json` rows
 * @returns {Array<Record<string, unknown>>} AdaptFit-style `segments`
 */
export function segmentsFromAnalysisRows(rows) {
  const inferred = inferTimesOnAnalysisRows(rows);
  return inferred.map((r, i) => {
    const workout = String(r.original ?? "").trim() || `Segment ${i + 1}`;
    const mod = String(r.modified_alternative ?? "").trim();
    return {
      start_time_seconds: Number.isFinite(Number(r.start_time)) ? Number(r.start_time) : 0,
      end_time_seconds: Number.isFinite(Number(r.end_time)) ? Number(r.end_time) : 0,
      workout,
      risk_flag: String(r.risk_flag ?? "low"),
      modified_workout_text: mod || ADAPTFIT_SAFE_LABEL,
      modified_workout_gif_url: null,
      section: r.section != null ? String(r.section) : null,
      notes: r.notes != null ? String(r.notes) : null
    };
  });
}

/**
 * Normalize segment times (infer missing ends) on AdaptFit-shaped segments.
 * @param {Array<Record<string, unknown>>} segments
 */
export function normalizeSegmentsForPlayback(segments) {
  const list = (segments || []).map((s) => ({ ...s }));
  for (let i = 0; i < list.length; i += 1) {
    let st = list[i].start_time_seconds;
    let et = list[i].end_time_seconds;
    st = st != null && st !== "" ? Number(st) : NaN;
    et = et != null && et !== "" ? Number(et) : NaN;
    const next = list[i + 1];
    const nextSt =
      next != null && next.start_time_seconds != null && next.start_time_seconds !== ""
        ? Number(next.start_time_seconds)
        : NaN;
    if (!Number.isFinite(et)) {
      if (Number.isFinite(nextSt)) et = nextSt;
      else if (Number.isFinite(st)) et = st + 30;
      else et = NaN;
    }
    if (!Number.isFinite(st)) st = 0;
    if (Number.isFinite(et) && et <= st) et = st + 15;
    list[i].start_time_seconds = st;
    list[i].end_time_seconds = et;
  }
  return list;
}

/**
 * @param {Array<Record<string, unknown>>} segments
 * @param {number} t - current time seconds
 */
export function findActiveSegmentIndex(segments, t) {
  const sec = Math.floor(Number(t) || 0);
  for (let i = 0; i < segments.length; i += 1) {
    const st = Number(segments[i].start_time_seconds);
    const et = Number(segments[i].end_time_seconds);
    if (Number.isFinite(st) && Number.isFinite(et) && sec >= st && sec < et) return i;
  }
  return -1;
}

/** How many segment cards to show beside the player (sliding window). */
export const PLAYBACK_WINDOW_SIZE = 3;

/**
 * First segment index to show in a sliding window so the active segment stays visible
 * (shows up to {@link PLAYBACK_WINDOW_SIZE} cards: current + upcoming when possible).
 * @param {Array<Record<string, unknown>>} segments
 * @param {number} t - current time seconds
 */
export function findPlaybackWindowStart(segments, t) {
  const n = segments && segments.length ? segments.length : 0;
  if (n === 0) return 0;
  const windowSize = Math.min(PLAYBACK_WINDOW_SIZE, n);
  const sec = Math.floor(Number(t) || 0);
  const active = findActiveSegmentIndex(segments, t);
  if (active >= 0) {
    return Math.min(active, Math.max(0, n - windowSize));
  }
  for (let i = 0; i < n; i += 1) {
    const st = Number(segments[i].start_time_seconds);
    if (Number.isFinite(st) && sec < st) {
      return Math.min(i, Math.max(0, n - windowSize));
    }
  }
  return Math.max(0, n - windowSize);
}

/**
 * @param {Array<Record<string, unknown>>} analysisRows
 * @param {{ youtubeUrl?: string | null, title?: string | null }} meta
 * @returns {{ youtube_video_id: string | null, title: string, segments: Array<Record<string, unknown>> }}
 */
export function buildAdaptFitPlaybackDocument(analysisRows, meta = {}) {
  const segments = normalizeSegmentsForPlayback(segmentsFromAnalysisRows(analysisRows));
  const url = (meta.youtubeUrl || "").trim();
  const vid = url ? extractYouTubeVideoId(url) : "";
  return {
    youtube_video_id: vid || null,
    title: (meta.title && String(meta.title).trim()) || "AdaptFit analysis",
    segments
  };
}

function parsePayload(raw) {
  if (raw == null || raw === "") return null;
  if (typeof raw === "object") return raw;
  if (typeof raw === "string") {
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }
  return null;
}

/**
 * Prefer `backend_payload.playback_workout` saved at analyze time; otherwise rebuild from `analysis_rows`.
 * @param {Record<string, unknown>} record - `youtube_videos` row
 */
export function resolvePlaybackDocument(record) {
  const payload = parsePayload(record.backend_payload);
  const saved = payload?.playback_workout;
  if (saved && typeof saved === "object" && Array.isArray(saved.segments) && saved.segments.length) {
    return {
      youtube_video_id: saved.youtube_video_id ?? null,
      title: typeof saved.title === "string" ? saved.title : "AdaptFit analysis",
      segments: normalizeSegmentsForPlayback(saved.segments)
    };
  }
  const rows = record.analysis_rows || [];
  return buildAdaptFitPlaybackDocument(rows, {
    youtubeUrl: record.youtube_url,
    title: record.video_title
  });
}

/**
 * Build `reuse_video_information` for POST /api/adapt/workout from a saved `youtube_videos` row.
 * Prefers `backend_payload.video_information` from a prior API response; otherwise derives chapters from playback segments.
 * @param {Record<string, unknown>} record
 * @returns {Record<string, unknown> | null}
 */
export function buildReuseVideoInformationForApi(record) {
  if (!record || typeof record !== "object") return null;
  const payload = parsePayload(record.backend_payload);
  const vi = payload?.video_information;
  if (vi && typeof vi === "object" && Array.isArray(vi.chapters) && vi.chapters.length) {
    return /** @type {Record<string, unknown>} */ ({ ...vi });
  }
  const playback = resolvePlaybackDocument(record);
  const segs = playback.segments || [];
  if (!segs.length) return null;
  const chapters = segs.map((s, i) => ({
    index: i + 1,
    title: String(s.workout || `Segment ${i + 1}`).slice(0, 500),
    start_time: Number(s.start_time_seconds) || 0,
    end_time: Number(s.end_time_seconds) || 0,
    section: s.section != null ? String(s.section) : "",
    notes: s.notes != null ? String(s.notes) : ""
  }));
  const duration = chapters.reduce((m, c) => Math.max(m, Number(c.end_time) || 0), 0);
  return {
    title: playback.title,
    id: playback.youtube_video_id || null,
    duration,
    webpage_url: record.youtube_url || "",
    chapters,
    description: "",
    adaptfit_phase: "reconstructed_from_saved_segments"
  };
}
