import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from app.database import Base


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    zoom_meeting_id = Column(String, index=True)
    host_email = Column(String, nullable=False)
    host_display_name = Column(String, nullable=True)
    participant_email = Column(String, nullable=False)
    topic = Column(String, nullable=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class FeedbackRequest(Base):
    __tablename__ = "feedback_requests"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, nullable=False)
    customer_email = Column(String, nullable=False)
    host_email = Column(String, nullable=False)
    host_display_name = Column(String, nullable=True)
    token = Column(String, unique=True, index=True, nullable=False)
    sent_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed = Column(Boolean, default=False)
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class FeedbackResponse(Base):
    __tablename__ = "feedback_responses"

    id = Column(Integer, primary_key=True, index=True)
    feedback_request_id = Column(Integer, nullable=False)
    customer_email = Column(String, nullable=False)
    host_email = Column(String, nullable=False)
    rating = Column(Integer, nullable=False)
    business_requirement = Column(String, nullable=True)
    confidence_level = Column(String, nullable=True)
    engineer_rating = Column(Integer, nullable=True)
    improvements = Column(Text, nullable=True)
    concern_resolved = Column(String, nullable=True)
    comments = Column(Text, nullable=True)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    display_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
