from sqlalchemy import Column, String, DateTime
from datetime import datetime, timedelta, timezone
from app.core.database import Base
from uuid import uuid4

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    email = Column(String, primary_key=True)
    token = Column(String, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True))

    @staticmethod
    def generate(email: str):
        token = str(uuid4())
        return PasswordResetToken(
            email=email,
            token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
        )

