from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.api.routes.chat import router as chat_router
from src.app.api.routes.contact import router as contact_router
from src.app.api.routes.health import router as health_router
from src.app.core.config import Settings
from src.app.core.dependencies import initialize_dependencies


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI()
    initialize_dependencies(app, settings=settings)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=app.state.settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():
        return {"message": "AI Digital Twin API with Memory"}

    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(contact_router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
