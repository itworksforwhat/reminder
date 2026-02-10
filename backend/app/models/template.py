import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, Boolean, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    items = relationship("TemplateItem", back_populates="template", lazy="selectin", order_by="TemplateItem.month, TemplateItem.day")


class TemplateItem(Base):
    __tablename__ = "template_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    template_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("templates.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    month: Mapped[int | None] = mapped_column(Integer, nullable=True)
    day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recurrence: Mapped[str] = mapped_column(String(20), default="once")
    adjust_for_holiday: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    extra_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    template = relationship("Template", back_populates="items")
