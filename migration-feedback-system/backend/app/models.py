import bcrypt
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Index
from sqlalchemy.sql import func
from app.database import Base


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(String(64), nullable=False, index=True)
    mm_email = Column(String(255), nullable=False)
    customer_domain = Column(String(255), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_meetings_mm_email", "mm_email"),
    )


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(String(64), nullable=False, index=True)
    customer_email = Column(String(255), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FeedbackRequest(Base):
    """Tracks sent feedback requests to manage reminders and prevent duplicates."""
    __tablename__ = "feedback_requests"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(String(64), nullable=False)
    customer_email = Column(String(255), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    reminder_sent = Column(Boolean, default=False)
    submitted = Column(Boolean, default=False)

    __table_args__ = (
        Index("ix_feedback_requests_meeting_customer", "meeting_id", "customer_email", unique=True),
    )


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def set_password(self, password: str):
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, password: str) -> bool:
        return bcrypt.checkpw(password.encode(), self.password_hash.encode())
