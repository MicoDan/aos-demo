import uuid
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from taskcommon.events import Attachment, Priority

Status = Literal["pending", "in_progress", "completed"]


def _clean_list(v):
    """Trim, drop blanks, de-duplicate (keeps order)."""
    if v is None:
        return []
    out = []
    for x in v:
        if not isinstance(x, str):
            raise ValueError("entries must be strings")
        x = x.strip()
        if not x:
            continue
        if len(x) > 200:
            raise ValueError("each entry must be at most 200 characters")
        if x not in out:
            out.append(x)
    if len(out) > 50:
        raise ValueError("at most 50 entries")
    return out


class _ListFields(BaseModel):
    @field_validator("assignees", "labels", "supporting_institutions_within_gsas",
                     "supporting_institutions_outside_gsas", check_fields=False, mode="before")
    @classmethod
    def _lists(cls, v):
        return _clean_list(v) if v is None or isinstance(v, list) else v


class TaskCreate(_ListFields):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=5000)
    status: Status = "pending"
    due_date: Optional[date] = None
    project: Optional[str] = Field(default=None, max_length=200)
    attachments: list[Attachment] = Field(default_factory=list, max_length=20)
    parent_task: Optional[uuid.UUID] = None
    priority: Priority = "medium"
    assignees: list[str] = Field(default_factory=list)
    lead_institution: Optional[str] = Field(default=None, max_length=200)
    supporting_institutions_within_gsas: list[str] = Field(default_factory=list)
    supporting_institutions_outside_gsas: list[str] = Field(default_factory=list)
    date_issued: Optional[date] = None  # defaults to today (UTC) when omitted
    labels: list[str] = Field(default_factory=list)


class TaskUpdate(_ListFields):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=5000)
    status: Optional[Status] = None
    due_date: Optional[date] = None
    project: Optional[str] = Field(default=None, max_length=200)
    attachments: Optional[list[Attachment]] = Field(default=None, max_length=20)
    parent_task: Optional[uuid.UUID] = None
    priority: Optional[Priority] = None
    assignees: Optional[list[str]] = None
    lead_institution: Optional[str] = Field(default=None, max_length=200)
    supporting_institutions_within_gsas: Optional[list[str]] = None
    supporting_institutions_outside_gsas: Optional[list[str]] = None
    date_issued: Optional[date] = None
    labels: Optional[list[str]] = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    description: Optional[str]
    status: Status
    due_date: Optional[date]
    created_by: str
    created_at: datetime
    updated_at: datetime
    version: int
    project: Optional[str]
    attachments: list[Attachment]
    parent_task: Optional[uuid.UUID]
    priority: Priority
    assignees: list[str]
    lead_institution: Optional[str]
    supporting_institutions_within_gsas: list[str]
    supporting_institutions_outside_gsas: list[str]
    date_issued: date
    labels: list[str]


class TaskPage(BaseModel):
    items: list[TaskOut]
    total: int
    limit: int
    offset: int
    latest_updated_at: Optional[datetime] = None
