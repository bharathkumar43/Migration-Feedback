from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# --- Meeting Schemas ---

class MeetingCreate(BaseModel):
    meeting_id: str
    mm_email: str
    customer_domain: str


class MeetingResponse(BaseModel):
    id: int
    meeting_id: str
    mm_email: str
    customer_domain: str
    timestamp: datetime

    class Config:
        from_attributes = True


# --- Feedback Schemas ---

class FeedbackSubmit(BaseModel):
    token: str
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    meeting_id: str
    customer_email: str
    rating: int
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# --- Dashboard Schemas ---

class MigrationManagerStats(BaseModel):
    mm_email: str
    average_rating: float
    total_feedbacks: int
    total_meetings: int


class WeeklyTrend(BaseModel):
    week: str
    average_rating: float
    total_feedbacks: int


class DashboardSummary(BaseModel):
    overall_avg_rating: float
    total_feedbacks: int
    total_meetings: int
    mm_stats: list[MigrationManagerStats]
    weekly_trends: list[WeeklyTrend]


# --- Zoom Webhook Schemas ---

class ZoomParticipant(BaseModel):
    user_name: Optional[str] = None
    email: Optional[str] = ""


class ZoomMeetingPayload(BaseModel):
    account_id: Optional[str] = None
    object: Optional[dict] = None


class ZoomWebhookEvent(BaseModel):
    event: str
    payload: Optional[ZoomMeetingPayload] = None
    event_ts: Optional[int] = None
