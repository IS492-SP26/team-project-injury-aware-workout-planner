import { APP_CONFIG } from "./config.js";

function resolveApiBase() {
  const configured = String(APP_CONFIG.API_BASE || "").trim();
  if (!configured) {
    return typeof window !== "undefined" ? `${window.location.origin}/api` : "/api";
  }
  return configured.replace(/\/+$/, "");
}

function networkErrorMessage(cause) {
  const base =
    resolveApiBase() ||
    (typeof window !== "undefined" ? `${window.location.origin}/api` : "http://127.0.0.1:8010/api");
  const isHttpsPage =
    typeof window !== "undefined" && window.location?.protocol === "https:";
  const isHttpApi = String(base).startsWith("http:");
  if (isHttpsPage && isHttpApi) {
    return (
      "This page is HTTPS but the analysis API is HTTP; the browser blocks that. " +
      "For local testing open the app over HTTP, e.g. http://127.0.0.1:4173/workouts.html " +
      "(run: py -m http.server 4173 in the deploy-app folder)."
    );
  }
  const original = cause?.message || String(cause);
  return (
    `Could not reach the analysis API at ${base}. ` +
    "Start the deploy-app backend: py -m uvicorn backend.server:app --reload --port 8010 " +
    "(run it from the deploy-app folder, or leave API_BASE blank when deployed on Vercel). " +
    `(${original})`
  );
}

async function fetchApi(path, init) {
  const base = resolveApiBase();
  const url = `${base}${path}`;
  let res;
  try {
    res = await fetch(url, init);
  } catch (e) {
    throw new Error(networkErrorMessage(e));
  }
  return res;
}

export async function submitSurveyToBackend(raw) {
  const res = await fetchApi("/api/survey", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ raw })
  });

  if (!res.ok) {
    throw new Error(`Survey save failed (${res.status}): ${await res.text()}`);
  }

  return res.json();
}

export async function analyzeWorkoutWithBackend(payload) {
  const res = await fetchApi("/api/adapt/workout", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!res.ok) {
    throw new Error(`Workout analysis failed (${res.status}): ${await res.text()}`);
  }

  return res.json();
}
