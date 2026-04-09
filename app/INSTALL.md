# AdaptFit AI — Local Install & Run (Demo)

This project is a local demo web app:
- Frontend: `adaptfit_app.html`
- Backend API: FastAPI (`app/server.py`)

## Prerequisites
- Python 3.10+ (recommended)

## 1) Install Python dependencies
From the repo root:

```bash
python3 -m pip install -r requirements.txt
```

## 2) Set your Groq API key
Copy the example env file and fill in your key:

```bash
cp app/.env.example .env
```

Edit `.env` and set:

```
GROQ_API_KEY=your_key_here
```

## 3) Start the backend
From the repo root:

```bash
python3 -m uvicorn app.server:app --reload --port 8000
```

## 4) Start a local static server for the HTML
From the repo root (in a second terminal):

```bash
python3 -m http.server 5173
```

## 5) Open the app
In your browser:
- `http://localhost:5173/adaptfit_app.html`

## Troubleshooting
- If you see `GROQ_API_KEY is not set`: make sure you created `.env` at the repo root and set the key.
- If the page shows `Load failed`: make sure both servers are running (API on `:8000`, static server on `:5173`).

