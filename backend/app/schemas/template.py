from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime, date


class TemplateItemResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    month: int | None
    day: int | None
    recurrence: str
    adjust_for_holiday: bool
    priority: int
    category: str

    model_config = {"from_attributes": True}


class TemplateResponse(BaseModel):
    id: UUID
    name: str
    description: str | None
    category: str
    is_system: bool
    items: list[TemplateItemResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class TemplateApplyRequest(BaseModel):
    template_id: UUID
    company_id: UUID
    year: int = Field(..., ge=2000, le=2100)


class GeneratedReminder(BaseModel):
    title: str
    category: str
    deadline: date
    original_deadline: date | None = None
    priority: int = 0
    description: str | None = None


class TemplateApplyResponse(BaseModel):
    template_name: str
    year: int
    generated_count: int
    reminders: list[GeneratedReminder]
