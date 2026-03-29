# Fashion Expo Review Repo

Clean review repository for jury access. This monorepo contains:

- `frontend/` - main Expo React Native client
- `frontend-tryon-mvp/` - separate Expo + Convex try-on MVP frontend
- `backend/` - FastAPI server

The repository was prepared without git history, without local environment files, and without private runtime artifacts such as the backend SQLite database and uploaded media.

## What Was Removed

- Git metadata from the original private repositories
- Local `.env` files
- The backend `fashion.db`
- Local media and temporary backend files
- Frontend build caches and `node_modules`

## Run The Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

The backend seeds demo data on startup and serves the API at `http://127.0.0.1:8000`.

If OpenRouter is not needed during review, leave `OPENROUTER_API_KEY` empty in `backend/.env`.

## Run The Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm start
```

By default the example environment points to `http://127.0.0.1:8000`.

## Run The Secondary Frontend MVP

```bash
cd frontend-tryon-mvp
npm install
copy .env.example .env.local
npm start
```

This MVP uses Convex and BytePlus Seedream environment variables from `frontend-tryon-mvp/.env.example`.

## Notes For Reviewers

- Backend demo users are documented in `backend/README.md`.
- Main frontend app flow and screens are documented in `frontend/README.md`.
- The secondary try-on prototype is documented in `frontend-tryon-mvp/README.md`.
- The frontend also includes a production backend URL in `frontend/app.json`, but local review can override it with `EXPO_PUBLIC_API_URL` from `.env`.
