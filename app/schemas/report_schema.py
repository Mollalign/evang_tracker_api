from pydantic import BaseModel, Field
import datetime
from uuid import UUID
from typing import Optional

class ReportBase(BaseModel):
    outreach_name: str
    location: str
    date: datetime.date
    heard_count: int = Field(default=0, ge=0)
    interested_count: int = Field(default=0, ge=0)
    accepted_count: int = Field(default=0, ge=0)
    repented_count: int = Field(default=0, ge=0)
    notes: Optional[str] = None

class ReportCreate(ReportBase):
    pass

class ReportUpdate(BaseModel):
    outreach_name: Optional[str] = None
    location: Optional[str] = None
    date: Optional[datetime.date] = None
    heard_count: Optional[int] = Field(default=None, ge=0)
    interested_count: Optional[int] = Field(default=None, ge=0)
    accepted_count: Optional[int] = Field(default=None, ge=0)
    repented_count: Optional[int] = Field(default=None, ge=0)
    notes: Optional[str] = None

class ReportResponse(ReportBase):
    id: UUID
    evangelist_id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True