import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Meeting, FeedbackRequest, FeedbackResponse
from app.routers.auth import get_current_admin

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/stats")
def dashboard_stats(db: Session = Depends(get_db), _admin: dict = Depends(get_current_admin)):
    total_meetings = db.query(func.count(Meeting.id)).scalar() or 0
    total_feedback_sent = db.query(func.count(FeedbackRequest.id)).scalar() or 0
    total_responses = db.query(func.count(FeedbackResponse.id)).scalar() or 0
    avg_rating = db.query(func.avg(FeedbackResponse.rating)).scalar()

    response_rate = (total_responses / total_feedback_sent * 100) if total_feedback_sent > 0 else 0

    return {
        "total_meetings": total_meetings,
        "total_feedback_sent": total_feedback_sent,
        "total_responses": total_responses,
        "response_rate": round(response_rate, 1),
        "average_rating": round(float(avg_rating), 2) if avg_rating else None,
    }


@router.get("/responses")
def list_responses(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    responses = (
        db.query(FeedbackResponse)
        .order_by(FeedbackResponse.submitted_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "customer_email": r.customer_email,
            "host_email": r.host_email,
            "rating": r.rating,
            "comments": r.comments,
            "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
        }
        for r in responses
    ]


@router.get("/meetings")
def list_meetings(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    meetings = (
        db.query(Meeting)
        .order_by(Meeting.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        {
            "id": m.id,
            "zoom_meeting_id": m.zoom_meeting_id,
            "host_email": m.host_email,
            "host_display_name": m.host_display_name,
            "participant_email": m.participant_email,
            "topic": m.topic,
            "start_time": m.start_time.isoformat() if m.start_time else None,
            "end_time": m.end_time.isoformat() if m.end_time else None,
            "duration_minutes": m.duration_minutes,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in meetings
    ]


@router.get("/pending")
def list_pending(
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    pending = (
        db.query(FeedbackRequest)
        .filter(FeedbackRequest.completed == False)
        .order_by(FeedbackRequest.created_at.desc())
        .all()
    )
    return [
        {
            "id": p.id,
            "customer_email": p.customer_email,
            "host_email": p.host_email,
            "host_display_name": p.host_display_name,
            "sent_at": p.sent_at.isoformat() if p.sent_at else None,
            "reminder_sent": p.reminder_sent,
        }
        for p in pending
    ]
