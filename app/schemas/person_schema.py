from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional
from enum import Enum

class SpiritualStatus(str, Enum):
    interested = "interested"
    accepted = "accepted"
    repented = "repented"

class PersonBase(BaseModel):
    full_name: str
    phone_number: Optional[str] = None
    status: SpiritualStatus
    report_id: UUID

class PersonCreate(PersonBase):
    pass

class PersonUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    status: Optional[SpiritualStatus] = None
    report_id: Optional[UUID] = None

class PersonResponse(PersonBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
