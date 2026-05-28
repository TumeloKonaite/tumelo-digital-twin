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

Run the backend API tests with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests
```

The twin system prompt is assembled by `src/app/domain/twin/prompt_builder.py`. `backend/context.py` now supplies prompt input data and delegates final prompt construction to that builder.
