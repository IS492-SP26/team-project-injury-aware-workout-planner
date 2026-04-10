import { requireUser, signOut } from "./app-shell.js";
import {
  PLAYBACK_WINDOW_SIZE,
  findActiveSegmentIndex,
  findPlaybackWindowStart,
  resolvePlaybackDocument
} from "./adaptfit-playback-format.js";
import { hasSupabaseConfig, requireSupabase } from "./supabase-client.js";
import { STORAGE_KEYS, formatTimestampRange, readStorage, routeTo } from "./state.js";
import { createPollingPlayer, extractYouTubeVideoId } from "./youtube-player.js";

const resultsMain = document.getElementById("results-main");
const emptyState = document.getElementById("empty-state");
const metadata = document.getElementById("result-metadata");
const segmentsSection = document.getElementById("segments-section");
const segmentsLayout = document.getElementById("segments-layout");
const videoColumn = document.getElementById("video-column");
const segmentScroll = document.getElementById("segment-scroll");
const playbackCaption = document.getElementById("playback-caption");
const syncHint = document.getElementById("sync-hint");

let playerControl = null;
let flowSegmentsRef = /** @type {Array<Record<string, unknown>>} */ ([]);
let lastFlowUpdateKey = "";
/** Markdown saved with the row (used by Copy Markdown; no on-page preview). */
let markdownExport = "";

function riskClass(flag) {
  const value = String(flag || "").toLowerCase();
  if (value === "high") return "high";
  if (value === "medium") return "medium";
  if (value === "safe") return "low";
  return "low";
}

function escapeHtml(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function hasUsableTimestamps(segments) {
  return (segments || []).some(
    (s) => Number.isFinite(Number(s.start_time_seconds)) || Number.isFinite(Number(s.end_time_seconds))
  );
}

function formatSegmentRangeSeconds(seg) {
  const st = Number(seg.start_time_seconds);
  const et = Number(seg.end_time_seconds);
  if (Number.isFinite(st) && Number.isFinite(et)) {
    return `${Math.floor(st)}s - ${Math.floor(et)}s`;
  }
  return formatTimestampRange(seg) || "—";
}

/**
 * @param {Array<Record<string, unknown>>} segments
 * @param {number} currentSecond
 * @param {boolean} canSync
 */
function renderWorkoutFlowWindow(segments, currentSecond, canSync) {
  segmentScroll.innerHTML = "";
  const list = segments || [];
  const n = list.length;
  if (n === 0) return;

  const windowSize = Math.min(PLAYBACK_WINDOW_SIZE, n);
  const activeIdx = canSync ? findActiveSegmentIndex(list, currentSecond) : -1;
  const windowStart = canSync ? findPlaybackWindowStart(list, currentSecond) : 0;

  for (let k = 0; k < windowSize; k += 1) {
    const segIndex = windowStart + k;
    const seg = list[segIndex];
    if (!seg) break;

    const card = document.createElement("article");
    card.className = "segment-card";
    card.dataset.segmentIndex = String(segIndex);
    const isCurrent = activeIdx >= 0 && segIndex === activeIdx;
    if (isCurrent) card.classList.add("segment-card--active");

    const head = document.createElement("div");
    head.className = "segment-card__head";
    const rangeLabel = formatSegmentRangeSeconds(seg);
    if (canSync) {
      head.textContent = isCurrent
        ? `Current Workout (${rangeLabel})`
        : `Upcoming (${rangeLabel})`;
    } else {
      head.textContent = `Workout (${rangeLabel})`;
    }

    const table = document.createElement("table");
    table.className = "segment-card__table";
    table.innerHTML = `
      <thead>
        <tr>
          <th>Workout</th>
          <th>Risk flag</th>
          <th>Modified workout</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>${escapeHtml(String(seg.workout ?? "").trim() || "—")}</td>
          <td><span class="risk-badge ${riskClass(seg.risk_flag)}">${escapeHtml(String(seg.risk_flag ?? "low"))}</span></td>
          <td>${escapeHtml(String(seg.modified_workout_text ?? ""))}</td>
        </tr>
      </tbody>
    `;

    card.appendChild(head);
    card.appendChild(table);
    segmentScroll.appendChild(card);
  }
}

/**
 * @param {Array<Record<string, unknown>>} segments
 * @param {number} currentSecond
 * @param {boolean} canSync
 */
function updateWorkoutFlow(segments, currentSecond, canSync) {
  const list = segments || [];
  const activeIdx = canSync ? findActiveSegmentIndex(list, currentSecond) : -1;
  const ws = canSync ? findPlaybackWindowStart(list, currentSecond) : 0;
  const key = `${ws}|${activeIdx}|${canSync}|${list.length}`;
  if (key === lastFlowUpdateKey && segmentScroll.childElementCount > 0) return;
  lastFlowUpdateKey = key;
  renderWorkoutFlowWindow(list, currentSecond, canSync);
}

function teardownPlayer() {
  if (playerControl) {
    playerControl.destroy();
    playerControl = null;
  }
  const mount = document.getElementById("yt-player-mount");
  if (mount) mount.innerHTML = "";
}

function parseJsonObject(raw) {
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

/** Scan nested JSON for any string that looks like a YouTube URL. */
function walkForYoutubeUrl(val, depth) {
  const d = depth ?? 0;
  if (d > 14) return "";
  if (typeof val === "string") {
    const t = val.trim();
    if ((/youtube\.com|youtu\.be/i.test(t) || /\/watch\?v=/.test(t)) && extractYouTubeVideoId(t)) {
      return t;
    }
    return "";
  }
  if (Array.isArray(val)) {
    for (let i = 0; i < val.length; i += 1) {
      const u = walkForYoutubeUrl(val[i], d + 1);
      if (u) return u;
    }
    return "";
  }
  if (val && typeof val === "object") {
    const keys = Object.keys(val);
    for (let i = 0; i < keys.length; i += 1) {
      const u = walkForYoutubeUrl(val[keys[i]], d + 1);
      if (u) return u;
    }
  }
  return "";
}

function resolveYoutubeUrl(record) {
  const a = (record.youtube_url || "").trim();
  if (a) return a;
  const payload = parseJsonObject(record.backend_payload);
  if (!payload) return "";
  const b = (payload.youtube_url || "").trim();
  if (b) return b;
  return walkForYoutubeUrl(payload, 0);
}

/** @param {Array<Record<string, unknown>>} segments - AdaptFit-shaped */
function setupPlayback(record, segments) {
  teardownPlayer();
  const url = resolveYoutubeUrl(record);
  const videoId = extractYouTubeVideoId(url);
  const canSync = hasUsableTimestamps(segments);

  videoColumn.classList.toggle("hidden", !videoId);
  segmentsLayout.classList.toggle("results-playback-grid--split", Boolean(videoId));
  segmentsLayout.classList.toggle("results-playback-grid--single", !videoId);

  playbackCaption.textContent = "";
  syncHint.classList.add("hidden");
  syncHint.textContent = "";

  if (videoId) {
    playbackCaption.textContent = "Playback syncs with chapter timestamps from the analysis.";
    const mount = document.getElementById("yt-player-mount");
    if (!canSync) {
      syncHint.textContent =
        "No per-chapter timestamps were attached to this run, so the list will not auto-highlight during playback.";
      syncHint.classList.remove("hidden");
    }
    playerControl = createPollingPlayer(mount, videoId, {
      intervalMs: 500,
      onSecond: (second) => {
        updateWorkoutFlow(flowSegmentsRef, second, canSync);
      },
      onFallbackEmbed: () => {
        playbackCaption.textContent =
          "Showing an embedded player. If the video appears but segments do not highlight, allow YouTube in your browser or try Chrome.";
      }
    });
  } else if (record.source === "youtube") {
    syncHint.textContent =
      "No video URL on this saved row (check Supabase youtube_url) or re-run analysis from Workouts.";
    syncHint.classList.remove("hidden");
  } else {
    syncHint.textContent =
      "Pasted-text analyses have no YouTube player; scroll the adapted exercises on the right.";
    syncHint.classList.remove("hidden");
  }
}

if (!hasSupabaseConfig()) {
  emptyState.classList.remove("hidden");
  emptyState.textContent = "Add your Supabase URL and anon key in assets/js/config.js before viewing saved results.";
  if (resultsMain) resultsMain.classList.add("hidden");
} else {
  const supabase = requireSupabase();
  const user = await requireUser("/index.html");
  if (!user) throw new Error("Authentication redirect failed.");

  document.getElementById("sign-out-btn").addEventListener("click", signOut);

  async function loadRecord() {
    const id = new URLSearchParams(window.location.search).get("id") || readStorage(STORAGE_KEYS.latestVideoId);
    if (!id) return null;

    const { data, error } = await supabase
      .from("youtube_videos")
      .select("*")
      .eq("id", id)
      .eq("user_id", user.id)
      .maybeSingle();

    if (error) throw error;
    return data;
  }

  try {
    const record = await loadRecord();
    if (!record) {
      emptyState.classList.remove("hidden");
      if (resultsMain) resultsMain.classList.add("hidden");
    } else {
      emptyState.classList.add("hidden");
      if (resultsMain) resultsMain.classList.remove("hidden");

      const playback = resolvePlaybackDocument(record);
      const segments = playback.segments;
      flowSegmentsRef = segments;
      lastFlowUpdateKey = "";
      markdownExport = String(record.markdown_table ?? "");

      const canFlow = hasUsableTimestamps(segments);
      updateWorkoutFlow(segments, 0, canFlow);
      metadata.textContent = `${record.source === "youtube" ? "YouTube analysis" : "Text analysis"} saved ${new Date(record.created_at).toLocaleString()}`;

      segmentsSection.classList.remove("hidden");
      setupPlayback(record, segments);
    }
  } catch (error) {
    emptyState.classList.remove("hidden");
    emptyState.textContent = error.message || "Failed to load results.";
    if (resultsMain) resultsMain.classList.add("hidden");
    teardownPlayer();
  }
}

document.getElementById("copy-markdown-btn").addEventListener("click", async () => {
  if (!markdownExport.trim()) return;
  await navigator.clipboard.writeText(markdownExport);
});

document.getElementById("new-analysis-btn").addEventListener("click", () => routeTo("/workouts.html"));
