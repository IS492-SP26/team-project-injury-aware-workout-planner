## Minimal tests for critical paths

This document lists **minimal, high-value tests** that cover the critical paths of this repo:
- **Local demo**: `adaptfit_app.html` + FastAPI backend at `app/server.py`
- **Deployable MVP**: `deploy-app/*` frontend + FastAPI backend at `deploy-app/backend/server.py` (exposed via `deploy-app/api/index.py`)

The focus is on **end-to-end API behavior** plus a few **unit tests** for “pure” helpers. External dependencies (YouTube + Groq/Gemini + Supabase) should be mocked/stubbed.

---

## Critical use cases (what must not break)

### Use case A — Create a session from onboarding (Survey)
- **Actor**: user
- **Goal**: submit onboarding answers and get a `session_id`
- **Backend endpoints**:
  - Local demo: `POST /api/survey` (`app/server.py`)
  - Deploy app: `POST /api/survey` (`deploy-app/backend/server.py`)
- **Expected**:
  - Response includes `session_id`
  - Normalized `user_input_data` shape is present
  - Session file is persisted (`user_input_data.json`) to the session directory

### Use case B — Adapt a YouTube workout (core value)
- **Actor**: user
- **Goal**: provide `session_id` + YouTube URL and receive risky segments + safer alternatives
- **Backend endpoints**:
  - Local demo: `POST /api/adapt/workout` with `source="youtube"` (`app/server.py`)
  - Deploy app: `POST /api/adapt/workout` with `source="youtube"` (`deploy-app/backend/server.py`)
- **Expected**:
  - Returns a list of adaptation rows (JSON) and/or a markdown table (depending on `output_format`)
  - Includes time ranges when chapters are available
  - Persists combined input + output artifacts in the session folder

### Use case C — Adapt pasted workout text (fallback path)
- **Actor**: user
- **Goal**: adapt a workout when YouTube extraction isn’t used
- **Backend endpoints**:
  - Local demo: `POST /api/adapt/workout` with `source="text"` (`app/server.py`)
  - Deploy app: `POST /api/adapt/workout` with `source="text"` (`deploy-app/backend/server.py`)
- **Expected**:
  - Same output structure as YouTube flow, but no dependency on YouTube metadata

### Use case D — Correct failure modes (safety + debuggability)
- **Missing session**: adapting with an unknown `session_id` returns **404**
- **Missing required fields**: invalid payload returns **422**
- **Missing API keys (local demo)**: when adaptation backend requires keys, returns a clear **5xx** error message (e.g. missing `GROQ_API_KEY` / `GEMINI_API_KEY`)

---

## Minimal E2E tests (API-level, with mocks)

These are the “ship it” tests: they validate request/response contracts and persistence without hitting real external services.

### E2E-1 — Health check
- **Target**: `GET /health` (local) and `GET /api/health` (deploy backend supports both)
- **Assert**:
  - `200` status
  - JSON body equals `{"status":"ok"}` (or equivalent)

### E2E-2 — Survey creates session and persists `user_input_data.json`
- **Call**: `POST /api/survey` with a minimal realistic payload:
  - Age, levelLabel (or `level`), zone (knee/shoulder), injuryLabel, pain fields
- **Assert**:
  - `200`
  - Response has `session_id` (non-empty string)
  - Response has `user_input_data.user_profile`, `injury_details`, `assessments`
  - A `user_input_data.json` file was written in the session folder

### E2E-3 — Adapt (text) happy path (mock LLM call)
- **Setup**:
  - Create a session via the survey endpoint (E2E-2)
  - Mock/stub the LLM adaptation function so it returns a deterministic JSON list, e.g.:
    - `[{ "original":"Squats", "modified_alternative":"Box squats (partial range)", "risk_flag":"knee flexion" }]`
- **Call**: `POST /api/adapt/workout` with:
  - `source="text"`
  - `workout_text="..."`
  - `output_format="json"` (or `"both"`)
- **Assert**:
  - `200`
  - Response includes `result_json` (list of dicts)
  - If `output_format` includes markdown, `result_markdown_table` is non-empty and contains headers
  - Output artifacts were persisted in the session folder (input + output)

### E2E-4 — Adapt (YouTube) happy path (mock YouTube timeline + mock LLM)
- **Setup**:
  - Create a session via survey
  - Mock the YouTube metadata/timeline builder:
    - Local demo: mock `app.util.yt_split.chapters_metadata.fetch_video_information`
    - Deploy backend: mock `backend.gemini_adaptfit_flow.build_video_information_gemini_adaptfit`
  - Mock the LLM adaptation call (Groq/Gemini) to return deterministic rows
- **Call**: `POST /api/adapt/workout` with `source="youtube"` and a sample YouTube URL
- **Assert**:
  - `200`
  - At least one result row includes `time_range` when chapters are provided
  - Response echoes `youtube_url` for youtube source

### E2E-5 — Adapt with missing session returns 404
- **Call**: `POST /api/adapt/workout` with a random `session_id` that does not exist
- **Assert**:
  - `404`
  - Error detail mentions missing `user_input_data.json` (or “session not found”)

### E2E-6 — Validation errors for missing required fields
- **Call**: `POST /api/adapt/workout` with:
  - `source="youtube"` but missing/blank `youtube_url`
  - `source="text"` but missing/blank `workout_text`
- **Assert**:
  - `422` (FastAPI validation)
  - Error body points to the missing field requirement

---

## Minimal unit tests (pure helpers / deterministic logic)

These tests are quick, stable, and catch regressions in the most reused logic.

### Unit-1 — Normalize survey payload → `user_input_data` shape
- **Target**:
  - Local demo: `_normalize_user_input_data` in `app/server.py`
  - Deploy backend: `_normalize_user_input_data` in `deploy-app/backend/server.py`
- **Given**: payload variations (e.g. `inp_age` vs `age`, `zone` casing)
- **Assert**:
  - Output has keys: `user_profile`, `injury_details`, `assessments`
  - Goals parsing: string vs list produces a list
  - Knee/shoulder mapping normalizes `"knee" -> "Knee"`, `"shoulder" -> "Shoulder"`

### Unit-2 — Time formatting helper
- **Target**: `_format_ts`
- **Assert**:
  - `0 -> "00:00"`
  - `61 -> "01:01"`
  - negative values clamp to `"00:00"`
  - non-numeric returns empty string

### Unit-3 — Chapter time-range attachment
- **Target**: `_attach_time_ranges`
- **Given**:
  - `rows=[{...}, {...}]`
  - `video_information={"chapters":[{"start_time":0,"end_time":30},{"start_time":30,"end_time":60}]}`
- **Assert**:
  - Rows get `start_time`, `end_time`, and `time_range`
  - If chapters missing or shorter than rows, remaining rows still have `time_range` (empty string)

---

## Implementation notes (so tests stay minimal)

### Recommended test approach
- Use **pytest** + FastAPI’s **TestClient**.
- Use monkeypatch/mocks to avoid:
  - network calls to YouTube (`yt-dlp` or any chapter builder)
  - calls to Groq/Gemini
  - any real Supabase access

### Keeping file persistence testable
- Patch the session directory root in tests to a temp folder so tests don’t write into the repo.
  - Local demo uses `SESSIONS_DIR` under `app/prompts/sessions`
  - Deploy backend uses OS temp on Vercel and `deploy-app/backend/sessions` locally

### Minimal “definition of done”
If you implement only **E2E-1 through E2E-6** and **Unit-1 through Unit-3**, you’ll cover:
- the full happy path from onboarding → adaptation output
- the core contracts of the API
- the most common regressions (validation, session persistence, timeline formatting)

