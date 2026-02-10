from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.reminders import router as reminders_router
from app.api.templates import router as templates_router
from app.api.companies import router as companies_router
from app.api.notifications import router as notifications_router

api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(reminders_router)
api_router.include_router(templates_router)
api_router.include_router(companies_router)
api_router.include_router(notifications_router)
