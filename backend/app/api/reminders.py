from uuid import UUID
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.reminder import (
    ReminderCreate, ReminderUpdate, ReminderResponse, ReminderListResponse,
)
from app.services.reminder_service import (
    get_reminders, get_reminder, create_reminder,
    update_reminder, delete_reminder,
)
from app.services.excel_service import export_reminders_to_excel, import_reminders_from_excel
from app.utils.security import get_current_user
from app.utils.websocket import manager, create_sync_message
from app.models.user import User
from fastapi import UploadFile, File

router = APIRouter(prefix="/reminders", tags=["reminders"])


@router.get("", response_model=ReminderListResponse)
async def list_reminders(
    company_id: UUID = Query(...),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = Query(None),
    completed: bool | None = Query(None),
    year: int | None = Query(None),
    month: int | None = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await get_reminders(
        db, user, company_id,
        page=page, page_size=page_size,
        category=category, completed=completed,
        year=year, month=month,
    )
    return ReminderListResponse(**result)


@router.get("/export/excel")
async def export_excel(
    company_id: UUID = Query(...),
    year: int | None = Query(None),
    category: str | None = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    output = await export_reminders_to_excel(db, company_id, user.id, year, category)

    filename = f"reminders_{year or 'all'}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.post("/import/excel")
async def import_excel(
    company_id: UUID = Query(...),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await import_reminders_from_excel(db, company_id, user.id, file)
    return result


@router.get("/{reminder_id}", response_model=ReminderResponse)
async def get_reminder_detail(
    reminder_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    reminder = await get_reminder(db, user, reminder_id)
    return ReminderResponse.model_validate(reminder)


@router.post("", response_model=ReminderResponse, status_code=201)
async def create_reminder_endpoint(
    company_id: UUID = Query(...),
    data: ReminderCreate = ...,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    reminder = await create_reminder(db, user, company_id, data)

    await manager.broadcast_to_company(
        company_id,
        create_sync_message("created", "reminder", str(reminder.id)),
    )

    return ReminderResponse.model_validate(reminder)


@router.put("/{reminder_id}", response_model=ReminderResponse)
async def update_reminder_endpoint(
    reminder_id: UUID,
    data: ReminderUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    reminder = await update_reminder(db, user, reminder_id, data)

    await manager.broadcast_to_company(
        reminder.company_id,
        create_sync_message("updated", "reminder", str(reminder.id)),
    )

    return ReminderResponse.model_validate(reminder)


@router.delete("/{reminder_id}", status_code=204)
async def delete_reminder_endpoint(
    reminder_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    reminder = await get_reminder(db, user, reminder_id)
    company_id = reminder.company_id
    await delete_reminder(db, user, reminder_id)

    await manager.broadcast_to_company(
        company_id,
        create_sync_message("deleted", "reminder", str(reminder_id)),
    )
