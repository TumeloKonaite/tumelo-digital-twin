from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from src.app.api.schemas.chat import ChatRequest, ChatResponse
from src.app.domain.twin.service import TwinService


router = APIRouter()
twin_service = TwinService()


def get_twin_service() -> TwinService:
    return twin_service


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, service: TwinService = Depends(get_twin_service)):
    try:
        result = service.chat(request.message, request.session_id)
        return ChatResponse(response=result.response, session_id=result.session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, service: TwinService = Depends(get_twin_service)):
    try:
        result = service.stream_chat(request.message, request.session_id)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return StreamingResponse(
        result.stream,
        media_type="text/plain; charset=utf-8",
        headers={"X-Session-Id": result.session_id},
    )


@router.get("/sessions")
async def list_sessions(service: TwinService = Depends(get_twin_service)):
    return {"sessions": service.list_sessions()}
