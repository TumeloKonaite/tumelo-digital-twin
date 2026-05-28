# tumelo-digital-twin

Backend entry point: `src.app.main:app`

Start the backend from the repository root with:

```bash
uv run --package backend uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Run the backend API tests with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests
```

The twin system prompt is assembled by `src/app/domain/twin/prompt_builder.py`. `backend/context.py` now supplies prompt input data and delegates final prompt construction to that builder.
