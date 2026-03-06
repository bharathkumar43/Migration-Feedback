import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.crud import (
    get_feedback_request_by_token,
    feedback_already_submitted,
    create_feedback,
    mark_feedback_submitted,
)
from app.schemas import FeedbackSubmit, FeedbackResponse
from app.services.jira_service import create_jira_ticket

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/validate")
def validate_token(token: str, db: Session = Depends(get_db)):
    """Validate a feedback token and return meeting context."""
    req = get_feedback_request_by_token(db, token)
    if not req:
        raise HTTPException(status_code=404, detail="Invalid or expired feedback link")
    if req.submitted:
        raise HTTPException(status_code=409, detail="Feedback already submitted")
    return {
        "valid": True,
        "meeting_id": req.meeting_id,
        "customer_email": req.customer_email,
    }


@router.post("/submit", response_model=FeedbackResponse)
def submit_feedback(payload: FeedbackSubmit, db: Session = Depends(get_db)):
    req = get_feedback_request_by_token(db, payload.token)
    if not req:
        raise HTTPException(status_code=404, detail="Invalid or expired feedback link")

    if req.submitted or feedback_already_submitted(db, req.meeting_id, req.customer_email):
        raise HTTPException(status_code=409, detail="Feedback already submitted for this meeting")

    fb = create_feedback(
        db,
        meeting_id=req.meeting_id,
        customer_email=req.customer_email,
        rating=payload.rating,
        comment=payload.comment,
    )
    mark_feedback_submitted(db, payload.token)

    # Auto-create Jira ticket for low ratings
    if payload.rating <= 2:
        try:
            create_jira_ticket(
                meeting_id=req.meeting_id,
                customer_email=req.customer_email,
                rating=payload.rating,
                comment=payload.comment,
            )
            logger.info(f"Jira ticket created for low rating on meeting {req.meeting_id}")
        except Exception as e:
            logger.error(f"Failed to create Jira ticket: {e}")

    return fb
