from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from uuid import UUID
from app.config import settings
from app.api import api_router
from app.utils.websocket import manager
from app.database import get_engine, Base, get_session_factory
from app.services.template_engine import seed_system_templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed system templates
    session_factory = get_session_factory()
    async with session_factory() as session:
        await seed_system_templates(session)
        await session.commit()

    yield

    # Shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="경리 업무 리마인더 - 클라우드 동기화 기반 자동 일정 관리 시스템",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터
app.include_router(api_router)


# WebSocket 엔드포인트
@app.websocket("/ws/{company_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    company_id: UUID,
    token: str = Query(None),
):
    # 간단한 토큰 검증
    if not token:
        await websocket.close(code=4001, reason="Authentication required")
        return

    try:
        from app.utils.security import decode_token
        payload = decode_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=4001, reason="Invalid token")
            return
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await manager.connect(websocket, company_id)

    try:
        while True:
            data = await websocket.receive_json()
            # 클라이언트에서 보낸 메시지를 같은 회사의 다른 클라이언트에 전달
            await manager.broadcast_to_company(company_id, data, exclude=websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, company_id)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.APP_NAME}
