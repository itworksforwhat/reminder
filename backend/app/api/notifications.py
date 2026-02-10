from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.utils.security import get_current_user
from app.services.notification_service import (
    get_notification_summary, get_today_reminders,
    get_overdue_reminders, get_upcoming_deadlines,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/summary")
async def notification_summary(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """현재 사용자의 알림 요약 (오늘 마감, 지연, 7일 이내)을 반환합니다."""
    return await get_notification_summary(db, user.id)


@router.get("/today")
async def today_notifications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """오늘 마감인 리마인더 목록을 반환합니다."""
    return await get_today_reminders(db, user.id)


@router.get("/overdue")
async def overdue_notifications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """마감일이 지난 미완료 리마인더 목록을 반환합니다."""
    return await get_overdue_reminders(db, user.id)


@router.get("/upcoming")
async def upcoming_notifications(
    days: int = Query(7, ge=1, le=30),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """향후 N일 이내 마감되는 리마인더 목록을 반환합니다."""
    return await get_upcoming_deadlines(db, user.id, days_ahead=days)
