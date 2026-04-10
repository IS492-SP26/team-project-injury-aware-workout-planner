export const STORAGE_KEYS = {
  backendSessionId: "adaptfit_backend_session_id",
  latestVideoId: "adaptfit_latest_video_id",
  latestResults: "adaptfit_latest_results",
  onboardingDraft: "adaptfit_onboarding_draft",
  readinessSnapshot: "adaptfit_readiness_snapshot"
};

export function saveStorage(key, value) {
  localStorage.setItem(key, JSON.stringify(value));
}

export function readStorage(key, fallback = null) {
  const raw = localStorage.getItem(key);
  if (!raw) return fallback;
  try {
    return JSON.parse(raw);
  } catch {
    return fallback;
  }
}

export function clearStorage(key) {
  localStorage.removeItem(key);
}

export function setStatus(el, message, tone = "muted") {
  if (!el) return;
  el.textContent = message || "";
  el.dataset.tone = tone;
}

export function routeTo(path) {
  window.location.href = path;
}

export function formatTimestampRange(row) {
  if (!row) return "";
  if (row.time_range) return row.time_range;

  const stSrc = row.start_time_seconds ?? row.start_time;
  const etSrc = row.end_time_seconds ?? row.end_time;
  if (stSrc == null && etSrc == null) return "";

  const toClock = (input) => {
    if (input == null || Number.isNaN(Number(input))) return "";
    const total = Math.max(0, Math.round(Number(input)));
    const mins = Math.floor(total / 60);
    const secs = total % 60;
    return `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
  };

  const start = toClock(stSrc);
  const end = toClock(etSrc);
  if (start && end) return `${start}-${end}`;
  return start || end;
}

