# Hiring Board

Small internal tool for recruiters to work through job applications.

## Quick start

Needs Docker and [uv](https://docs.astral.sh/uv/).

```
docker compose up -d
cd backend
uv sync
uv run python -m scripts.import_csv
uv run uvicorn app.main:app --reload --port 8000
```

The import wipes the database and loads the three CSV files from `backend/data`. Run it again any time.

Setup and architecture notes will be added as the project grows.
