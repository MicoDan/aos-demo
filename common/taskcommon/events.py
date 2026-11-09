"""Event schema shared by the outbox writer (Smart Admin) and the replica consumer (My Assist).

Events carry a full task snapshot so My Assist never needs to query Smart Admin.
"""
import uuid
from datetime import date, datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator

EVENT_TYPES = ("task.created", "task.updated", "task.deleted", "task.completed")
EventType = Literal["task.created", "task.updated", "task.deleted", "task.completed"]
Status = Literal["pending", "in_progress", "completed"]
Priority = Literal["low", "medium", "high", "critical"]


class Attachment(BaseModel):
    """Stored inline on the task (no separate table). A reference, not file storage."""
    name: str = Field(min_length=1, max_length=255)
    url: Optional[str] = Field(default=None, max_length=2000)
    content_type: Optional[str] = Field(default=None, max_length=100)
    size: Optional[int] = Field(default=None, ge=0)


class TaskSnapshot(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str] = None
    status: Status
    due_date: Optional[date] = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    # --- fields below default so events published before they existed still replay
    project: Optional[str] = None
    attachments: list[Attachment] = Field(default_factory=list)
    parent_task: Optional[uuid.UUID] = None
    priority: Priority = "medium"
    assignees: list[str] = Field(default_factory=list)
    lead_institution: Optional[str] = None
    supporting_institutions_within_gsas: list[str] = Field(default_factory=list)
    supporting_institutions_outside_gsas: list[str] = Field(default_factory=list)
    date_issued: Optional[date] = None
    labels: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _default_issue_date(self):
        if self.date_issued is None:  # legacy events: issued when created (UTC)
            self.date_issued = self.created_at.astimezone(timezone.utc).date()
        return self


class TaskEvent(BaseModel):
    event_id: uuid.UUID
    event_type: EventType
    task_id: uuid.UUID
    user_id: str
    version: int = Field(ge=1)
    occurred_at: datetime
    task: TaskSnapshot
    changes: dict[str, Any] = Field(default_factory=dict)


def new_event(event_type: str, snapshot: dict, version: int, user_id: str,
              changes: Optional[dict] = None) -> TaskEvent:
    return TaskEvent(
        event_id=uuid.uuid4(),
        event_type=event_type,
        task_id=snapshot["id"],
        user_id=user_id,
        version=version,
        occurred_at=datetime.now(timezone.utc),
        task=snapshot,
        changes=changes or {},
    )
