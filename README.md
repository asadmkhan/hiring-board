# Hiring Board

Recruiters get job applications from a matching system. Until now they worked through them in a spreadsheet. This app does the same job in a browser. You can search and filter the list, open one application, change its status, write a note, and ask an AI model what it thinks of the fit. The AI score sits next to the score the matcher already gave.

## Run it

You need Docker, uv and Node 22.12 or newer. uv is a Python tool, get it from https://docs.astral.sh/uv/.

Start the database and the API:

```
docker compose up -d --wait db
cd backend
uv sync
uv run python -m scripts.import_csv
uv run uvicorn app.main:app --reload --port 8000
```

Start the frontend in a second terminal:

```
cd frontend
npm install
npm run dev
```

Now open http://localhost:5173. The API docs are at http://localhost:8000/docs.

The import command empties the database and loads the three CSV files from backend/data. Run it again whenever you want a clean start.

If you only have Docker, run this instead and open http://localhost:8080:

```
docker compose up -d --build
docker compose run --rm api python -m scripts.import_csv
```

In this setup the API reads its keys from backend/.env as well. Only Ollama is different, because localhost inside a container is not your machine. Put OLLAMA_URL=http://host.docker.internal:11434 in a file called .env next to docker-compose.yml.

## Settings

The app runs without any settings file. You only need one for the AI providers. Copy backend/.env.example to backend/.env and put in the keys you have. ANTHROPIC_API_KEY for Claude, OPENAI_API_KEY for OpenAI, OLLAMA_URL for a local Ollama, usually http://localhost:11434. A provider with an empty value does not show up in the app. With no keys at all you still get the mock scorer. Keys stay on the server and never go to the browser.

The same file sets the model names. CLAUDE_MODEL is claude-haiku-4-5, OPENAI_MODEL is gpt-6-luna and OLLAMA_MODEL is llama3.2:3b unless you change them. For Ollama, pull the model first with ollama pull llama3.2:3b.

If port 5432 is already in use on your machine, put POSTGRES_PORT=5434 in that root .env file and use the same port in DATABASE_URL inside backend/.env.

## Tests

Backend: cd backend and run uv run pytest. Frontend: cd frontend and run npm test. The backend tests use an in memory SQLite database and the frontend tests fake the API. Nothing needs Docker and nothing calls a real model.

## How it is built

```
backend/
  app/
    main.py      creates the app and plugs in the routers
    config.py    settings, read from backend/.env
    db.py        database connection and session
    routers/     takes the HTTP request, sends the answer back
    services/    the rules, like when a status date changes or when a model gets called
    queries.py   reads from the database
    models.py    the tables
    schemas.py   what requests and responses look like
    scoring/     the prompt and one class per provider: mock, Claude, OpenAI, Ollama
  scripts/       the CSV import
  data/          the three CSV files
  tests/         pytest, runs on SQLite
frontend/src/
  components/    the list, the filters, the detail panel, the AI score widget
  api.ts         every call to the backend
```

The backend has three layers. The router takes the request and hands it down. The service applies the rules. The queries and models talk to the database. Each layer only calls the one under it. A simple read with no rules goes straight from router to query.

Scoring works like this. Each provider is a small class with one method, score. It gets the job and the candidate and gives back a number from 0 to 100 and one sentence. The service first checks if a score for this application and this provider is already stored. If yes, it returns that and no model is called, even when that provider is switched off by now. If not, it calls the provider once and stores the answer. If the call fails, nothing is stored and the API returns a clear error. The page then says the score is unavailable. It never shows a made up number.

The prompt only has the facts that matter for the fit. Job title, family, seniority, city and country. Years of experience, preferred family, city and country of the candidate. No name and no email.

## API

| Call | What it does |
|---|---|
| `GET /applications` | The list. Filters: `status` (new, in_review, shortlisted, rejected, hired), `country`, `job_family`, and `q` for a text search on candidate name and job title. Sort: `sort` is created_at or match_score, `order` is asc or desc. Paging: `page` from 1, `page_size` up to 100. Returns the rows and the total count. |
| `GET /applications/{id}` | One application with its candidate, job, note and stored AI scores. |
| `PATCH /applications/{id}` | Change `status`, `note` or both. |
| `POST /applications/{id}/llm-score` | Ask one provider for a score. Body: `{"provider": "mock"}`, or claude, openai, ollama. Returns the score and whether it was reused from the store. |
| `GET /llm-providers` | The providers this server offers. |
| `GET /filter-options` | The countries and job families in the data. |

An unknown id gives 404. Any bad input gives 422 with the reason. A provider that fails, or is not set up and has no stored score, gives 502 with a plain message.

## Choices I made

Country in the filter means the country of the job. That is how recruiters filter.

Any status can go to any other status. Nobody asked for rules about that.

The status date only changes when the status changes. Saving only a note does not touch it.

The list is newest first. A page has 20 rows, 100 at most. Ties are sorted by the application id, so pages never shuffle.

One AI score per application and provider, kept for good. Opening the same application twice never calls the model twice.

Claude Haiku 4.5 is the main model. The team already uses Claude, Haiku is the cheapest Claude model, and it returns clean JSON. At the listed prices one call costs well under a cent. OpenAI and a local Ollama model work the same way, so you can compare what they say.

The mock scorer replaces a real model. Same input, same answer, made from a few simple rules. It exists so the app works without a key and it is labelled as mock everywhere.

Postgres runs in Docker because that is what the team uses. Tests use SQLite because it is fast and needs nothing installed.

The frontend is plain React with Vite. It is one page talking to a separate API, so Next.js would add a server for nothing.

## What is not there

No login, the tool lives inside the company network. No way to add applications, they come from the matching system's export. No re-scoring, a stored score is final. No history of status changes, only the latest status and date. Filters are not in the URL, so you cannot share a filtered view as a link. No database migrations, the import rebuilds the tables.

## What I would do next

A history table for status changes. Re-scoring that keeps the old score. Filters and page in the URL. A page that shows where the AI score and the rule score disagree the most. A few browser tests.
