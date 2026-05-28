# tumelo-digital-twin

Backend entry point: `src.app.main:app`

Required environment variables:

- `OPENAI_API_KEY`: OpenAI API key used for chat completions.

Optional environment variables:

- `OPENAI_MODEL`: defaults to `gpt-4o-mini`
- `OPENAI_TIMEOUT_SECONDS`: defaults to `30`
- `OPENAI_MAX_RETRIES`: defaults to `2`
- `CONTENT_DATA_DIR`: defaults to `data` in the repo root, or `/persistent-storage/data` when that directory exists
- `CONVERSATION_STORAGE_DIR`: defaults to `CONTENT_DATA_DIR/conversations`
- `CORS_ORIGINS`: comma-separated list or JSON array, defaults to `http://localhost:3000`

Copy `.env.example` to `.env` or `backend/.env` and set the values for your environment.

Default runtime content now lives under `data/`:

```text
data/
|-- twin_profile.json
|-- summary.txt
|-- style.txt
|-- linkedin.pdf
|-- fallback_personality.txt
`-- conversations/
```

Start the backend from the repository root with:

```bash
uv run --package backend uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Install the backend plus test dependencies with:

```bash
uv sync --all-packages --group test
```

Run the backend pytest suite with:

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The twin system prompt is assembled by `src/app/domain/twin/prompt_builder.py`. `backend/context.py` now supplies prompt input data and delegates final prompt construction to that builder.

The test suite is organized by backend layer:

```text
tests/
├── api/
│   ├── test_chat_routes.py
│   └── test_health_routes.py
├── domain/
│   ├── test_prompt_builder.py
│   └── test_twin_service.py
├── infrastructure/
│   ├── test_content_loaders.py
│   ├── test_file_conversation_store.py
│   └── test_openai_client.py
└── conftest.py
```
