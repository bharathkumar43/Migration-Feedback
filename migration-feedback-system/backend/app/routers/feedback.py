import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import FeedbackRequest, FeedbackResponse

logger = logging.getLogger(__name__)
router = APIRouter()


class FeedbackSubmission(BaseModel):
    token: str
    rating: int
    business_requirement: str | None = None
    confidence_level: str | None = None
    engineer_rating: int | None = None
    improvements: str | None = None
    concern_resolved: str | None = None


class FeedbackInfo(BaseModel):
    host_display_name: str | None
    customer_email: str
    already_completed: bool


@router.get("/validate")
def validate_token(token: str, db: Session = Depends(get_db)):
    fb_req = db.query(FeedbackRequest).filter(FeedbackRequest.token == token).first()
    if not fb_req:
        raise HTTPException(status_code=404, detail="Invalid or expired feedback link")
    if fb_req.completed:
        raise HTTPException(status_code=409, detail="Feedback already submitted")
    return FeedbackInfo(
        host_display_name=fb_req.host_display_name,
        customer_email=fb_req.customer_email,
        already_completed=fb_req.completed,
    )


@router.post("/submit")
def submit_feedback(body: FeedbackSubmission, db: Session = Depends(get_db)):
    fb_req = db.query(FeedbackRequest).filter(FeedbackRequest.token == body.token).first()
    if not fb_req:
        raise HTTPException(status_code=404, detail="Invalid or expired feedback link")
    if fb_req.completed:
        raise HTTPException(status_code=409, detail="Feedback already submitted")
    if not 1 <= body.rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    response = FeedbackResponse(
        feedback_request_id=fb_req.id,
        customer_email=fb_req.customer_email,
        host_email=fb_req.host_email,
        rating=body.rating,
        business_requirement=body.business_requirement,
        confidence_level=body.confidence_level,
        engineer_rating=body.engineer_rating,
        improvements=body.improvements,
        concern_resolved=body.concern_resolved,
        submitted_at=datetime.now(timezone.utc),
    )
    db.add(response)

    fb_req.completed = True
    db.commit()

    logger.info(f"Feedback submitted by {fb_req.customer_email} — rating={body.rating}")
    return {"status": "ok", "message": "Thank you for your feedback!"}
