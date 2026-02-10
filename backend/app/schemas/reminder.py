from pydantic import BaseModel
from uuid import UUID
from datetime import date, datetime
from typing import Optional


class ReminderCreate(BaseModel):
    title: str
    description: str | None = None
    category: str
    deadline: date
    priority: int = 0


class ReminderUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    deadline: date | None = None
    completed: bool | None = None
    priority: int | None = None


class ReminderResponse(BaseModel):
    id: UUID
    company_id: UUID
    title: str
    description: str | None
    category: str
    deadline: date
    original_deadline: date | None
    completed: bool
    completed_at: datetime | None
    priority: int
    template_id: UUID | None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReminderListResponse(BaseModel):
    items: list[ReminderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
