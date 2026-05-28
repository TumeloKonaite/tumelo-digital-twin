from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.api.routes.chat import router as chat_router
from src.app.api.routes.health import router as health_router
from src.app.core.config import Settings, get_settings
from src.app.domain.twin.service import TwinService


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or get_settings()

    app = FastAPI()
    app.state.settings = runtime_settings
    app.state.twin_service = TwinService(settings=runtime_settings)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=runtime_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():
        return {"message": "AI Digital Twin API with Memory"}

    app.include_router(health_router)
    app.include_router(chat_router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
