# Hiring Board

Small internal tool for recruiters to work through job applications.

## Quick start

Needs Docker, [uv](https://docs.astral.sh/uv/) and Node.

```
docker compose up -d db
cd backend
uv sync
uv run python -m scripts.import_csv
uv run uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The import wipes the database and loads the three CSV files from `backend/data`. Run it again any time.

## Whole stack in Docker

```
docker compose up -d --build
docker compose run --rm api python -m scripts.import_csv
```

Open http://localhost:8080. Provider keys are read from `backend/.env`. Changing the CSV files needs a rebuild before the import sees them.

Setup and architecture notes will be added as the project grows.
