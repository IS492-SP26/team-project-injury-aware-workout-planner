function defaultApiBase() {
  if (typeof window === "undefined" || !window.location) {
    return "http://127.0.0.1:8010";
  }
  const { hostname, port, protocol } = window.location;
  const local = hostname === "localhost" || hostname === "127.0.0.1";
  const p = port || (protocol === "https:" ? "443" : "80");
  // Same FastAPI process serves deploy-app + API on 8000/8010 — use relative URLs (no cross-port fetch).
  if (local && (p === "8010" || p === "8000")) {
    return "";
  }
  // e.g. py -m http.server 4173 — call the API on its own port
  return local ? "http://127.0.0.1:8010" : "";
}

window.APP_CONFIG = window.APP_CONFIG || {
  SUPABASE_URL: "https://your-project.supabase.co",
  SUPABASE_ANON_KEY: "your-public-anon-key",
  API_BASE: defaultApiBase()
};

export const APP_CONFIG = Object.freeze(window.APP_CONFIG);
