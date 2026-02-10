"""알림 서비스.

D-Day 기반 알림 생성, 이메일 알림 큐, 푸시 알림 등을 처리합니다.
실제 이메일/푸시 전송은 외부 서비스(SendGrid, FCM 등)와 연동합니다.
"""
from datetime import date, datetime, timedelta
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.models.reminder import Reminder
from app.models.company import CompanyMember
from app.models.user import User


async def get_upcoming_deadlines(
    db: AsyncSession,
    user_id: UUID,
    days_ahead: int = 7,
) -> list[dict]:
    """향후 N일 이내 마감되는 미완료 리마인더를 조회합니다."""
    today = date.today()
    end_date = today + timedelta(days=days_ahead)

    # 사용자가 속한 모든 회사 ID 조회
    member_result = await db.execute(
        select(CompanyMember.company_id).where(CompanyMember.user_id == user_id)
    )
    company_ids = [row[0] for row in member_result.all()]

    if not company_ids:
        return []

    result = await db.execute(
        select(Reminder).where(
            and_(
                Reminder.company_id.in_(company_ids),
                Reminder.completed == False,
                Reminder.deadline >= today,
                Reminder.deadline <= end_date,
            )
        ).order_by(Reminder.deadline)
    )
    reminders = result.scalars().all()

    notifications = []
    for r in reminders:
        days_left = (r.deadline - today).days
        notifications.append({
            "reminder_id": str(r.id),
            "title": r.title,
            "category": r.category,
            "deadline": r.deadline.isoformat(),
            "days_left": days_left,
            "d_day_label": _d_day_label(days_left),
            "priority": r.priority,
            "company_id": str(r.company_id),
        })

    return notifications


async def get_overdue_reminders(
    db: AsyncSession,
    user_id: UUID,
) -> list[dict]:
    """마감일이 지난 미완료 리마인더를 조회합니다."""
    today = date.today()

    member_result = await db.execute(
        select(CompanyMember.company_id).where(CompanyMember.user_id == user_id)
    )
    company_ids = [row[0] for row in member_result.all()]

    if not company_ids:
        return []

    result = await db.execute(
        select(Reminder).where(
            and_(
                Reminder.company_id.in_(company_ids),
                Reminder.completed == False,
                Reminder.deadline < today,
            )
        ).order_by(Reminder.deadline)
    )
    reminders = result.scalars().all()

    return [
        {
            "reminder_id": str(r.id),
            "title": r.title,
            "category": r.category,
            "deadline": r.deadline.isoformat(),
            "days_overdue": (today - r.deadline).days,
            "d_day_label": f"D+{(today - r.deadline).days}",
            "priority": r.priority,
            "company_id": str(r.company_id),
        }
        for r in reminders
    ]


async def get_today_reminders(
    db: AsyncSession,
    user_id: UUID,
) -> list[dict]:
    """오늘 마감인 미완료 리마인더를 조회합니다."""
    today = date.today()

    member_result = await db.execute(
        select(CompanyMember.company_id).where(CompanyMember.user_id == user_id)
    )
    company_ids = [row[0] for row in member_result.all()]

    if not company_ids:
        return []

    result = await db.execute(
        select(Reminder).where(
            and_(
                Reminder.company_id.in_(company_ids),
                Reminder.completed == False,
                Reminder.deadline == today,
            )
        ).order_by(Reminder.priority.desc())
    )
    reminders = result.scalars().all()

    return [
        {
            "reminder_id": str(r.id),
            "title": r.title,
            "category": r.category,
            "deadline": r.deadline.isoformat(),
            "d_day_label": "D-Day",
            "priority": r.priority,
            "company_id": str(r.company_id),
        }
        for r in reminders
    ]


async def get_notification_summary(
    db: AsyncSession,
    user_id: UUID,
) -> dict:
    """알림 요약 정보를 반환합니다."""
    today_items = await get_today_reminders(db, user_id)
    overdue_items = await get_overdue_reminders(db, user_id)
    upcoming_items = await get_upcoming_deadlines(db, user_id, days_ahead=7)

    return {
        "today": {
            "count": len(today_items),
            "items": today_items,
        },
        "overdue": {
            "count": len(overdue_items),
            "items": overdue_items,
        },
        "upcoming_7days": {
            "count": len(upcoming_items),
            "items": upcoming_items,
        },
        "total_pending": len(today_items) + len(overdue_items) + len(upcoming_items),
        "generated_at": datetime.utcnow().isoformat(),
    }


def _d_day_label(days_left: int) -> str:
    if days_left == 0:
        return "D-Day"
    elif days_left > 0:
        return f"D-{days_left}"
    else:
        return f"D+{abs(days_left)}"
