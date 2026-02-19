import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from uuid import UUID
from app.config import settings
from app.api import api_router
from app.utils.websocket import manager
from app.database import get_engine, Base, get_session_factory
from app.services.template_engine import seed_system_templates

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    engine = get_engine()
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database schema created successfully")
    except Exception as e:
        logger.error(f"Failed to create database schema: {e}")
        raise

    try:
        session_factory = get_session_factory()
        async with session_factory() as session:
            await seed_system_templates(session)
            await session.commit()
        logger.info("System templates seeded successfully")
    except Exception as e:
        logger.warning(f"Failed to seed system templates: {e}")

    yield

    # Shutdown
    try:
        await engine.dispose()
    except Exception as e:
        logger.warning(f"Error during engine disposal: {e}")


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
    logger.info(f"WebSocket connected: company={company_id}, connections={manager.active_connections_count}")

    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast_to_company(company_id, data, exclude=websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, company_id)
        logger.info(f"WebSocket disconnected: company={company_id}, connections={manager.active_connections_count}")
    except Exception as e:
        manager.disconnect(websocket, company_id)
        logger.warning(f"WebSocket error: company={company_id}, error={e}")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.APP_NAME}
