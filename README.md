# Tumelo Digital Twin

[![Backend CI](https://github.com/TumeloKonaite/tumelo-digital-twin/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/TumeloKonaite/tumelo-digital-twin/actions/workflows/backend-ci.yml)
[![Deploy to Modal](https://github.com/TumeloKonaite/tumelo-digital-twin/actions/workflows/deploy-modal.yml/badge.svg)](https://github.com/TumeloKonaite/tumelo-digital-twin/actions/workflows/deploy-modal.yml)

An AI portfolio app with:

- a FastAPI backend in `src/`
- a Next.js frontend in `frontend/`
- custom profile and prompt data in `data/`
- GitHub Actions pipelines for CI and Modal deployment

The backend entrypoint is `main:app`.

## Repository Layout

```text
.
|-- data/                     Runtime content for the digital twin
|-- frontend/                 Next.js UI
|-- src/                      FastAPI application code
|-- tests/                    Backend test suite
|-- .github/workflows/        CI and deployment workflows
|-- modal_app.py              Modal ASGI deployment entrypoint
|-- requirements.txt          Backend runtime dependencies
`-- pyproject.toml            Tooling and test configuration
```

## Create Your Own Copy

1. Fork this repository on GitHub.
2. Clone your fork locally:

```bash
git clone https://github.com/<your-username>/tumelo-digital-twin.git
cd tumelo-digital-twin
```

3. Replace the sample profile content in `data/` with your own:
   - `data/twin_profile.json`
   - `data/summary.txt`
   - `data/style.txt`
   - `data/fallback_personality.txt`
   - `data/linkedin.pdf`
4. Copy `.env.example` to `.env`. Add your OpenAI key if you want chat completions enabled.

```bash
cp .env.example .env
```

On PowerShell, use:

```powershell
Copy-Item .env.example .env
```

Optional environment variables:

- `OPENAI_API_KEY`: enables chat completions; when unset, the API still starts but `/chat` and `/chat/stream` return `503`
- `OPENAI_MODEL`: defaults to `gpt-4o-mini`
- `OPENAI_TIMEOUT_SECONDS`: defaults to `30`
- `OPENAI_MAX_RETRIES`: defaults to `2`
- `DATABASE_URL`: enables contact submission persistence; when unset, the API still starts but contact submissions are not stored
- `CONTENT_DATA_DIR`: defaults to `data` in the repo root, or `/persistent-storage/data` when that directory exists
- `CONVERSATION_STORAGE_DIR`: defaults to `CONTENT_DATA_DIR/conversations`
- `CORS_ORIGINS`: comma-separated list or JSON array, defaults to `http://localhost:3000`

Default runtime content lives under `data/`:

```text
data/
|-- twin_profile.json
|-- summary.txt
|-- style.txt
|-- linkedin.pdf
|-- fallback_personality.txt
`-- conversations/
```

## Run Locally

### Backend

Install dependencies with `uv`:

```bash
uv sync --group dev --group test
```

Or with `pip`:

```bash
pip install -r requirements.txt
pip install black ruff pytest pytest-asyncio httpx pre-commit
```

Start the backend from the repository root:

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The backend will be available at `http://localhost:8000`.

### Frontend

Install frontend dependencies:

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Start the frontend:

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`.

## Developer Checks

Run the backend quality checks from the repository root:

```bash
ruff check . --fix
black --check .
pytest
pre-commit install
pre-commit run --all-files
```

## Docker

Run the backend locally with Docker Compose:

```bash
docker compose up --build
```

The Compose setup mounts `src/`, `main.py`, and `data/` for local iteration while keeping runtime defaults aligned with the container path `/app/data`.

## CI/CD

This repository includes two GitHub Actions workflows:

- [`.github/workflows/backend-ci.yml`](.github/workflows/backend-ci.yml): runs `ruff check .`, `black --check .`, and `pytest`
- [`.github/workflows/deploy-modal.yml`](.github/workflows/deploy-modal.yml): deploys the backend to Modal

### Current Workflow Behavior

- `backend-ci.yml` runs on every pull request and on pushes to `main`
- `deploy-modal.yml` runs on pushes to `main`
- `deploy-modal.yml` also supports manual runs from the Actions tab

## Deployment Notes

### Backend on Modal

The backend deploys to Modal using [`modal_app.py`](modal_app.py). The Modal image uses Python `3.12`, installs from `requirements.txt`, and packages `src/`, `data/`, and `main.py` without changing the existing FastAPI app structure.

Create the runtime secret before the first deploy:

```bash
modal secret create digital-twin-api-secrets OPENAI_API_KEY=your_openai_key
```

Add any other environment variables your app needs to the same secret, for example `DATABASE_URL`, `CORS_ORIGINS`, or `ENVIRONMENT`.

For local Modal testing:

```bash
pip install modal
modal setup
modal serve modal_app.py
```

For deployment:

```bash
modal deploy modal_app.py
```

For GitHub Actions deployment, add these repository secrets:

- `MODAL_TOKEN_ID`
- `MODAL_TOKEN_SECRET`

### Frontend on Vercel

If you deploy the frontend separately on Vercel:

1. Import the repository into Vercel.
2. Set the project `Root Directory` to `frontend`.
3. Keep the framework preset as `Next.js`.
4. Add `NEXT_PUBLIC_API_BASE_URL` to point at your deployed backend URL.

## Useful Files

- [`main.py`](main.py): root backend entrypoint
- [`modal_app.py`](modal_app.py): Modal deployment wrapper for the FastAPI app
- [`src/app/main.py`](src/app/main.py): FastAPI app factory and router wiring
- [`src/app/domain/twin/prompt_builder.py`](src/app/domain/twin/prompt_builder.py): builds the system prompt
