import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Date, Integer, Text, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base

class OutreachReport(Base):
    __tablename__ = "outreach_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    evangelist_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    outreach_name = Column(String, nullable=False) # (e.g., "Gospel Week", "Break Mission")
    location = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    heard_count = Column(Integer, default=0)
    interested_count = Column(Integer, default=0)
    accepted_count = Column(Integer, default=0)
    repented_count = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    evangelist = relationship("User", back_populates="outreach_reports")
    people = relationship("Person", back_populates="report")
