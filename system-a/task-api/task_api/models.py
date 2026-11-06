import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "tasks"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    created_by: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=1)
    project: Mapped[Optional[str]] = mapped_column(Text)
    attachments: Mapped[list] = mapped_column(JSONB, default=list)
    parent_task: Mapped[Optional[uuid.UUID]]
    priority: Mapped[str] = mapped_column(Text, default="medium")
    assignees: Mapped[list] = mapped_column(JSONB, default=list)
    lead_institution: Mapped[Optional[str]] = mapped_column(Text)
    supporting_institutions_within_gsas: Mapped[list] = mapped_column(JSONB, default=list)
    supporting_institutions_outside_gsas: Mapped[list] = mapped_column(JSONB, default=list)
    date_issued: Mapped[date] = mapped_column(Date)
    labels: Mapped[list] = mapped_column(JSONB, default=list)


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    aggregate_id: Mapped[uuid.UUID]
    event_type: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
