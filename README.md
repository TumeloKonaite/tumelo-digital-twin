# tumelo-digital-twin

Backend entry point: `main:app`

## Environment

Required environment variables:

- `OPENAI_API_KEY`: OpenAI API key used for chat completions.

Optional environment variables:

- `OPENAI_MODEL`: defaults to `gpt-4o-mini`
- `OPENAI_TIMEOUT_SECONDS`: defaults to `30`
- `OPENAI_MAX_RETRIES`: defaults to `2`
- `CONTENT_DATA_DIR`: defaults to `data` in the repo root, or `/persistent-storage/data` when that directory exists
- `CONVERSATION_STORAGE_DIR`: defaults to `CONTENT_DATA_DIR/conversations`
- `CORS_ORIGINS`: comma-separated list or JSON array, defaults to `http://localhost:3000`

Copy `.env.example` to `.env` and set the values for your environment.

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

## Local Development

Install runtime dependencies with `pip`:

```bash
pip install -r requirements.txt
pip install black ruff pytest pytest-asyncio httpx pre-commit
```

Or install the managed dev environment with `uv`:

```bash
uv sync --group dev --group test
```

Start the backend from the repository root:

```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Run developer checks:

```bash
black .
ruff check . --fix
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

## CI

GitHub Actions runs the backend pipeline on pushes to `main` and on pull requests. The workflow enforces:

- `ruff check .`
- `black --check .`
- `pytest`

## Deployment

Cerebrium already deploys from [cerebrium.toml](/c:/Users/l/Documents/Shadow clone/cerebrium.toml:1) using Python `3.12` and `requirements.txt`. The Docker files in this repo are for local parity and container readiness; Cerebrium continues to use its own deployment config unless you explicitly switch platforms.

The twin system prompt is assembled by [prompt_builder.py](/c:/Users/l/Documents/Shadow clone/src/app/domain/twin/prompt_builder.py:1), and the root [main.py](/c:/Users/l/Documents/Shadow clone/main.py:1) remains the app entrypoint for local and deployment usage.
