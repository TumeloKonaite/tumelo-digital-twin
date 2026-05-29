# Tumelo Digital Twin

[![Backend CI](https://github.com/TumeloKonaite/tumelo-digital-twin/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/TumeloKonaite/tumelo-digital-twin/actions/workflows/backend-ci.yml)
[![Cerebrium Deployment](https://github.com/TumeloKonaite/tumelo-digital-twin/actions/workflows/cerebrium-deploy.yml/badge.svg)](https://github.com/TumeloKonaite/tumelo-digital-twin/actions/workflows/cerebrium-deploy.yml)

An AI portfolio app with:

- a FastAPI backend in `src/`
- a Next.js frontend in `frontend/`
- custom profile and prompt data in `data/`
- GitHub Actions pipelines for CI and Cerebrium deployment

The backend entrypoint is `main:app`.

## Repository Layout

```text
.
|-- data/                     Runtime content for the digital twin
|-- frontend/                 Next.js UI
|-- src/                      FastAPI application code
|-- tests/                    Backend test suite
|-- .github/workflows/        CI and deployment workflows
|-- cerebrium.toml            Cerebrium deployment config
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
4. Copy `.env.example` to `.env` and add your OpenAI key.

```bash
cp .env.example .env
```

On PowerShell, use:

```powershell
Copy-Item .env.example .env
```

Required environment variable:

- `OPENAI_API_KEY`: OpenAI API key used for chat completions

Optional environment variables:

- `OPENAI_MODEL`: defaults to `gpt-4o-mini`
- `OPENAI_TIMEOUT_SECONDS`: defaults to `30`
- `OPENAI_MAX_RETRIES`: defaults to `2`
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
- [`.github/workflows/cerebrium-deploy.yml`](.github/workflows/cerebrium-deploy.yml): deploys the backend to Cerebrium

The Cerebrium setup below follows the official guide: [Cerebrium CI/CD Pipelines](https://cerebrium.ai/docs/deployments/ci-cd).

### Set Up Cerebrium Deployment for Your Own Fork

1. Create your Cerebrium projects in the Cerebrium dashboard and note each project ID.
2. Use separate `dev` and `prod` projects if you want safe promotion between environments.
3. In the Cerebrium dashboard, open `API Keys`, create a Service Account for GitHub Actions, and copy the generated token.
4. In GitHub, open your fork and go to `Settings -> Environments`.
5. Create environments named `dev` and `prod`.
6. In each environment, add these secrets:
   - `CEREBRIUM_SERVICE_ACCOUNT_TOKEN`
   - `CEREBRIUM_PROJECT_ID`
7. Set the `dev` environment's `CEREBRIUM_PROJECT_ID` to your development Cerebrium project, and the `prod` environment's value to your production project.
8. In Cerebrium, configure your runtime app secrets, including `OPENAI_API_KEY`.
9. Push to `main` to deploy production, or use `workflow_dispatch` to trigger a manual `dev` or `prod` deployment from the Actions tab.

### Current Workflow Behavior

- `backend-ci.yml` runs on every pull request and on pushes to `main`
- `cerebrium-deploy.yml` runs on pushes to `main`
- `cerebrium-deploy.yml` also supports manual runs with a `dev` or `prod` input
- pull requests targeting `main` or `development` deploy to `dev`
- forked pull requests do not deploy, because repository secrets are not exposed to untrusted forks

## Deployment Notes

### Backend on Cerebrium

The backend deploys using [`cerebrium.toml`](cerebrium.toml), Python `3.12`, and `requirements.txt`.

### Frontend on Vercel

If you deploy the frontend separately on Vercel:

1. Import the repository into Vercel.
2. Set the project `Root Directory` to `frontend`.
3. Keep the framework preset as `Next.js`.
4. Add `NEXT_PUBLIC_API_BASE_URL` to point at your deployed backend URL.

## Useful Files

- [`main.py`](main.py): root backend entrypoint
- [`src/app/main.py`](src/app/main.py): FastAPI app factory and router wiring
- [`src/app/domain/twin/prompt_builder.py`](src/app/domain/twin/prompt_builder.py): builds the system prompt
- [`cerebrium.toml`](cerebrium.toml): Cerebrium deployment configuration
