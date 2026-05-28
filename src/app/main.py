import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.api.routes.chat import router as chat_router
from src.app.api.routes.health import router as health_router


app = FastAPI()

origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "AI Digital Twin API with Memory"}


app.include_router(health_router)
app.include_router(chat_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
