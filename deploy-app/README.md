# deploy-app

Deployable AdaptFit AI MVP with:

- Supabase auth and persistence
- separate pages for sign-in, onboarding, workout import, and results
- its own FastAPI analysis backend at `POST /api/survey` and `POST /api/adapt/workout`
- Vercel-ready static hosting config

## Pages

- `index.html` - sign in / sign up
- `onboarding-basic.html` - basic profile
- `onboarding-injury.html` - body part and diagnosis
- `onboarding-assessment.html` - timeline, pain, and screening
- `onboarding-goals.html` - goals and activity level
- `workouts.html` - import YouTube or pasted workout text
- `results.html` - saved analysis results

## Local setup

1. Create a Supabase project.
2. Run the SQL in [`supabase/schema.sql`](C:/Users/vinit/IS492-SP26-Project/team-project-injury-aware-workout-planner/deploy-app/supabase/schema.sql).
3. Copy values from `assets/js/config.example.js` into `assets/js/config.js`.
4. Fill in your Supabase URL and anon key.
5. Leave `API_BASE` blank for Vercel so the frontend uses same-origin `/api`.
6. For local development, either set `API_BASE` to your local backend URL or run the backend from `deploy-app/backend/server.py`.
7. Serve this folder with any static server.

Example:

```powershell
cd deploy-app
py -m http.server 4173
```

Then open:

`http://127.0.0.1:4173`

## Current architecture

- Supabase handles:
  - auth
  - app user profile persistence
  - injury assessment persistence
  - stored workout/video analysis history
- `deploy-app/backend` handles:
  - normalization of onboarding data into the adaptation API input shape
  - YouTube chapter extraction
  - workout adaptation analysis

## Deployment notes

- `api/index.py` exposes the FastAPI app from `deploy-app/backend/server.py`
- the frontend will call `/api/...` automatically when `API_BASE` is blank
- for local static hosting without the Vercel function runtime, point `API_BASE` at your local backend
