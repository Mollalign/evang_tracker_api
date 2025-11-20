import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Date, Integer, Text, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class Person(Base):
    __tablename__ = "people"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    report_id = Column(UUID(as_uuid=True), ForeignKey("outreach_reports.id"), nullable=False)
    full_name = Column(String, nullable=False)
    phone_number = Column(String)
    status = Column(Enum("interested", "accepted", "repented", name="spiritual_status"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    report = relationship("OutreachReport", back_populates="people")