## Telemetry and Observability Plan

This plan defines:
- what to log in the database for production debugging and auditability
- what to log in application logs
- how to debug the critical test cases in `docs/use-cases.md`

It is intentionally minimal and practical for the current stack (FastAPI + Supabase + Groq/Gemini + YouTube parsing).

---

## Goals

- Trace one user request end-to-end across frontend, backend, and LLM calls.
- Diagnose failures quickly (validation vs external provider vs internal logic).
- Keep enough historical data to investigate regressions in adaptation quality.
- Avoid storing sensitive content that is not needed for debugging.

---

## Observability model (3 layers)

### 1) Database telemetry (durable, queryable)
Use Supabase tables as the source of truth for user-facing events and outcomes.

### 2) Structured application logs (high detail, short retention)
Use JSON logs in backend for request lifecycle, timings, and error stacks.

### 3) Test telemetry (local CI/dev only)
Capture request/response snapshots and mock call traces for failing tests.

---

## What to log in the database

Your current schema already stores useful data in:
- `public.users`
- `public.injury_assessments`
- `public.youtube_videos`

The plan below extends that with low-friction telemetry fields and one optional event table.

### A) Existing tables: required fields to keep populated

#### `public.injury_assessments`
- `user_id`
- `backend_session_id` (critical correlation key with backend session folders/logs)
- `raw_payload` (already present; keep for reproducibility of normalization bugs)
- `created_at`, `updated_at`

#### `public.youtube_videos`
- `user_id`
- `source` (`youtube` or `text`)
- `youtube_url`, `youtube_video_id` (when source is youtube)
- `backend_session_id` (same correlation purpose)
- `video_timestamps` (timeline/chapters used by adaptation)
- `analysis_rows` (final structured adaptation rows)
- `markdown_table` (UI-ready rendered output)
- `backend_payload` (raw backend response metadata)
- `created_at`, `updated_at`

These are already in schema; ensure write paths always set `backend_session_id` and `backend_payload` consistently.

### B) Add a lightweight telemetry event table (recommended)

Add table `public.backend_events` for debug-grade, append-only events:

- `id uuid primary key default gen_random_uuid()`
- `created_at timestamptz not null default timezone('utc', now())`
- `user_id uuid null references public.users(id) on delete set null`
- `backend_session_id text not null`
- `request_id text not null`
- `endpoint text not null` (e.g. `/api/survey`, `/api/adapt/workout`)
- `stage text not null`  
  - examples: `request_received`, `normalized_input_ready`, `timeline_ready`, `llm_request`, `llm_response`, `response_sent`, `error`
- `status_code integer null`
- `duration_ms integer null`
- `provider text null` (`groq`, `gemini`, `youtube`, `supabase`)
- `model text null`
- `error_code text null`
- `error_message text null` (truncate to safe length)
- `metadata jsonb not null default '{}'::jsonb` (small non-PII context)

Why this helps:
- you can reconstruct failures without digging through server logs
- useful for intermittent issues (provider overload/timeouts)
- makes test-to-prod parity easier (same stage names)

### C) Data minimization and privacy rules

Do **not** persist secrets or full prompt bodies:
- never store API keys
- do not store full provider request payloads by default
- if storing user text, prefer redacted/truncated form for telemetry

Safe to store:
- hashed request identifiers
- counts/lengths (e.g. chapter count, rows count)
- timing and status fields
- provider/model names

---

## Structured backend logs (JSON)

Emit one JSON log per major stage with these common keys:

- `ts` (ISO timestamp)
- `level` (`INFO`, `WARNING`, `ERROR`)
- `service` (`app.server` or `deploy-app/backend/server`)
- `env` (`local`, `ci`, `prod`)
- `request_id`
- `backend_session_id`
- `endpoint`
- `stage`
- `duration_ms` (when stage completes)
- `status_code` (if known)
- `provider` and `model` (if applicable)
- `error_type`, `error_message` (for failures)

### Minimum stages to log

- `request_received`
- `validation_passed` or `validation_failed`
- `session_loaded` or `session_missing`
- `timeline_fetch_started`
- `timeline_fetch_succeeded` / `timeline_fetch_failed`
- `llm_call_started`
- `llm_call_succeeded` / `llm_call_failed`
- `output_persist_succeeded` / `output_persist_failed`
- `response_sent`

This stage vocabulary should match `backend_events.stage`.

---

## Correlation IDs (critical)

Every request should carry and propagate:

- `request_id`: per HTTP request (new UUID if header absent)
- `backend_session_id`: cross-request user workflow id (already in API/session model)

Recommended behavior:
- accept incoming `X-Request-Id` from frontend; generate if missing
- include `request_id` in response headers for UI-side bug reports
- store both IDs in DB records and logs

---

## Debugging plan for the critical tests

Reference tests in `docs/use-cases.md`: E2E-1..E2E-6 and Unit-1..Unit-3.

### Global debug checklist (for any failing test)

1. Capture failing test name and request payload.
2. Read response status + error body.
3. Find `request_id` and `backend_session_id` from response/logs.
4. Query DB rows linked to those IDs.
5. Compare stage logs to identify first failed stage.
6. Re-run same test with verbose logs and deterministic mocks.

### E2E-1 Health check fails

Likely causes:
- app not booted
- route mismatch (`/health` vs `/api/health`)

Debug:
- verify startup logs
- hit endpoint manually with TestClient in isolation
- ensure no middleware crash before route resolution

### E2E-2 Survey creation fails

Likely causes:
- payload drift in frontend fields
- normalization regression
- session directory write issue

Debug:
- inspect normalized object in logs at `normalized_input_ready`
- check DB (`injury_assessments`) and filesystem session write
- run Unit-1 to isolate normalization logic from API wiring

### E2E-3 Adapt text path fails

Likely causes:
- session lookup failure
- mock not applied to LLM function
- parse/output formatting regression

Debug:
- confirm `session_loaded` stage exists
- assert mocked LLM function call count and returned payload
- inspect persisted output row count and markdown generation

### E2E-4 Adapt YouTube path fails

Likely causes:
- YouTube timeline builder mock not patched at correct import path
- time-range attachment mismatch
- provider fallback branch unexpectedly triggered

Debug:
- log chapter count at `timeline_fetch_succeeded`
- verify `_attach_time_ranges` behavior with Unit-3
- verify provider/model in stage logs

### E2E-5 Missing session should be 404 but is not

Likely causes:
- stale session file from previous test
- test not using isolated temp directory

Debug:
- force unique temp sessions root per test run
- print resolved session directory path in test logs
- assert no pre-existing `user_input_data.json`

### E2E-6 Validation errors (422) not returned

Likely causes:
- Pydantic model validator behavior changed
- endpoint bypassing expected model

Debug:
- inspect request body sent by test
- run endpoint with minimal payload in isolated test
- verify model validator branch for `source="youtube"` and `source="text"`

### Unit test debugging shortcuts

- Unit-1 failures: snapshot expected normalized schema and compare key-by-key.
- Unit-2 failures: add table-driven assertions for edge cases (`None`, strings, negative numbers).
- Unit-3 failures: test chapter list lengths 0, 1, and less than rows length.

---

## Minimal dashboards / SQL checks

Use simple SQL queries in Supabase to spot systemic failures.

### Error rate by endpoint (if using `backend_events`)

```sql
select endpoint,
       count(*) filter (where stage = 'error') as errors,
       count(*) as total,
       round(100.0 * count(*) filter (where stage = 'error') / nullif(count(*), 0), 2) as error_pct
from public.backend_events
where created_at >= now() - interval '24 hours'
group by endpoint
order by error_pct desc;
```

### Slow requests (>2s)

```sql
select endpoint, request_id, backend_session_id, duration_ms, created_at
from public.backend_events
where stage = 'response_sent'
  and duration_ms > 2000
order by duration_ms desc
limit 100;
```

### Adaptation output sanity

```sql
select id, source, youtube_video_id,
       jsonb_array_length(analysis_rows) as rows_count,
       created_at
from public.youtube_videos
order by created_at desc
limit 50;
```

---

## Rollout plan (low effort)

1. Add `request_id` generation + propagation in backend middleware.
2. Standardize JSON log format with the stage names above.
3. Ensure `backend_session_id` is always written to Supabase rows.
4. Add optional `backend_events` table and write only key stages.
5. Update test fixtures to print `request_id` and set isolated temp session roots.
6. Add CI artifact upload of failed test request/response snapshots.

---

## Definition of done

Telemetry is “good enough” when:
- every critical API request is traceable with `request_id` + `backend_session_id`
- failures can be located to a specific stage in under 5 minutes
- E2E failures in CI include enough logs/artifacts to reproduce locally
- no secrets are stored in database telemetry or logs

