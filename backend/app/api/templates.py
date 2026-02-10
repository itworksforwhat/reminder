from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.schemas.template import (
    TemplateResponse, TemplateApplyRequest, TemplateApplyResponse, GeneratedReminder,
)
from app.schemas.reminder import ReminderResponse
from app.models.template import Template
from app.services.template_engine import apply_template, SYSTEM_TEMPLATES, generate_reminders_from_template
from app.utils.security import get_current_user
from app.utils.websocket import manager, create_sync_message
from app.models.user import User

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=list[TemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Template).order_by(Template.name))
    templates = result.scalars().all()
    return [TemplateResponse.model_validate(t) for t in templates]


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Template).where(Template.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return TemplateResponse.model_validate(template)


@router.post("/preview", response_model=TemplateApplyResponse)
async def preview_template(
    request: TemplateApplyRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """템플릿 적용 미리보기 (실제 저장하지 않음)."""
    result = await db.execute(select(Template).where(Template.id == request.template_id))
    template = result.scalar_one_or_none()
    if not template:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    template_data = {
        "name": template.name,
        "items": [
            {
                "title": item.title,
                "description": item.description,
                "month": item.month,
                "day": item.day,
                "recurrence": item.recurrence,
                "adjust_for_holiday": item.adjust_for_holiday,
                "priority": item.priority,
                "category": item.category,
                "extra_config": item.extra_config,
            }
            for item in template.items
        ],
    }

    reminder_dicts = generate_reminders_from_template(template_data, request.year)

    return TemplateApplyResponse(
        template_name=template.name,
        year=request.year,
        generated_count=len(reminder_dicts),
        reminders=[GeneratedReminder(**rd) for rd in reminder_dicts],
    )


@router.post("/apply", response_model=list[ReminderResponse])
async def apply_template_endpoint(
    request: TemplateApplyRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """템플릿을 적용하여 실제 리마인더를 생성합니다."""
    reminders = await apply_template(
        db, request.template_id, request.company_id, user.id, request.year,
    )

    await manager.broadcast_to_company(
        request.company_id,
        create_sync_message("bulk_created", "reminder"),
    )

    return [ReminderResponse.model_validate(r) for r in reminders]
