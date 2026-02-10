import math
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status
from app.models.reminder import Reminder
from app.models.company import CompanyMember
from app.models.user import User
from app.schemas.reminder import ReminderCreate, ReminderUpdate


async def _check_company_access(db: AsyncSession, user_id: UUID, company_id: UUID) -> None:
    result = await db.execute(
        select(CompanyMember).where(
            and_(
                CompanyMember.user_id == user_id,
                CompanyMember.company_id == company_id,
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this company",
        )


async def get_reminders(
    db: AsyncSession,
    user: User,
    company_id: UUID,
    page: int = 1,
    page_size: int = 20,
    category: str | None = None,
    completed: bool | None = None,
    year: int | None = None,
    month: int | None = None,
) -> dict:
    await _check_company_access(db, user.id, company_id)

    query = select(Reminder).where(Reminder.company_id == company_id)
    count_query = select(func.count(Reminder.id)).where(Reminder.company_id == company_id)

    if category:
        query = query.where(Reminder.category == category)
        count_query = count_query.where(Reminder.category == category)
    if completed is not None:
        query = query.where(Reminder.completed == completed)
        count_query = count_query.where(Reminder.completed == completed)
    if year:
        query = query.where(func.extract("year", Reminder.deadline) == year)
        count_query = count_query.where(func.extract("year", Reminder.deadline) == year)
    if month:
        query = query.where(func.extract("month", Reminder.deadline) == month)
        count_query = count_query.where(func.extract("month", Reminder.deadline) == month)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(Reminder.deadline).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 0,
    }


async def get_reminder(db: AsyncSession, user: User, reminder_id: UUID) -> Reminder:
    result = await db.execute(select(Reminder).where(Reminder.id == reminder_id))
    reminder = result.scalar_one_or_none()

    if not reminder:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reminder not found")

    await _check_company_access(db, user.id, reminder.company_id)
    return reminder


async def create_reminder(
    db: AsyncSession, user: User, company_id: UUID, data: ReminderCreate
) -> Reminder:
    await _check_company_access(db, user.id, company_id)

    reminder = Reminder(
        company_id=company_id,
        title=data.title,
        description=data.description,
        category=data.category,
        deadline=data.deadline,
        priority=data.priority,
        created_by=user.id,
    )
    db.add(reminder)
    await db.flush()
    return reminder


async def update_reminder(
    db: AsyncSession, user: User, reminder_id: UUID, data: ReminderUpdate
) -> Reminder:
    reminder = await get_reminder(db, user, reminder_id)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "completed" and value is True and not reminder.completed:
            setattr(reminder, "completed_at", datetime.utcnow())
        elif field == "completed" and value is False:
            setattr(reminder, "completed_at", None)
        setattr(reminder, field, value)

    reminder.updated_at = datetime.utcnow()
    await db.flush()
    return reminder


async def delete_reminder(db: AsyncSession, user: User, reminder_id: UUID) -> None:
    reminder = await get_reminder(db, user, reminder_id)
    await db.delete(reminder)
    await db.flush()


async def bulk_create_reminders(
    db: AsyncSession, user: User, company_id: UUID, reminders_data: list[dict]
) -> list[Reminder]:
    await _check_company_access(db, user.id, company_id)

    reminders = []
    for data in reminders_data:
        reminder = Reminder(
            company_id=company_id,
            created_by=user.id,
            **data,
        )
        db.add(reminder)
        reminders.append(reminder)

    await db.flush()
    return reminders
