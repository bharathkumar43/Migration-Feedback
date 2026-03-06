from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from app.models import Meeting, Feedback, FeedbackRequest, AdminUser
from app.schemas import MeetingCreate


def create_meeting(db: Session, meeting: MeetingCreate) -> Meeting | None:
    existing = db.query(Meeting).filter(Meeting.meeting_id == meeting.meeting_id).first()
    if existing:
        return existing
    db_meeting = Meeting(
        meeting_id=meeting.meeting_id,
        mm_email=meeting.mm_email,
        customer_domain=meeting.customer_domain,
    )
    db.add(db_meeting)
    db.commit()
    db.refresh(db_meeting)
    return db_meeting


def get_meeting_by_id(db: Session, meeting_id: str) -> Meeting | None:
    return db.query(Meeting).filter(Meeting.meeting_id == meeting_id).first()


def create_feedback(db: Session, meeting_id: str, customer_email: str, rating: int, comment: str | None) -> Feedback:
    fb = Feedback(
        meeting_id=meeting_id,
        customer_email=customer_email,
        rating=rating,
        comment=comment,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb


def get_feedback_by_meeting(db: Session, meeting_id: str) -> list[Feedback]:
    return db.query(Feedback).filter(Feedback.meeting_id == meeting_id).all()


def feedback_already_submitted(db: Session, meeting_id: str, customer_email: str) -> bool:
    return (
        db.query(Feedback)
        .filter(Feedback.meeting_id == meeting_id, Feedback.customer_email == customer_email)
        .first()
        is not None
    )


# --- Feedback Request Tracking ---

def feedback_request_exists(db: Session, meeting_id: str, customer_email: str) -> bool:
    return (
        db.query(FeedbackRequest)
        .filter(FeedbackRequest.meeting_id == meeting_id, FeedbackRequest.customer_email == customer_email)
        .first()
        is not None
    )


def create_feedback_request(db: Session, meeting_id: str, customer_email: str, token: str) -> FeedbackRequest | None:
    if feedback_request_exists(db, meeting_id, customer_email):
        return None
    req = FeedbackRequest(
        meeting_id=meeting_id,
        customer_email=customer_email,
        token=token,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return req


def get_feedback_request_by_token(db: Session, token: str) -> FeedbackRequest | None:
    return db.query(FeedbackRequest).filter(FeedbackRequest.token == token).first()


def mark_feedback_submitted(db: Session, token: str):
    req = get_feedback_request_by_token(db, token)
    if req:
        req.submitted = True
        db.commit()


def get_pending_reminders(db: Session, hours: int = 24) -> list[FeedbackRequest]:
    """Get feedback requests older than `hours` that haven't been submitted or reminded."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return (
        db.query(FeedbackRequest)
        .filter(
            FeedbackRequest.submitted == False,
            FeedbackRequest.reminder_sent == False,
            FeedbackRequest.sent_at <= cutoff,
        )
        .all()
    )


def mark_reminder_sent(db: Session, request_id: int):
    req = db.query(FeedbackRequest).filter(FeedbackRequest.id == request_id).first()
    if req:
        req.reminder_sent = True
        db.commit()


# --- Dashboard Analytics ---

def get_overall_stats(db: Session) -> dict:
    avg_rating = db.query(func.avg(Feedback.rating)).scalar() or 0
    total_feedbacks = db.query(func.count(Feedback.id)).scalar() or 0
    total_meetings = db.query(func.count(Meeting.id)).scalar() or 0
    return {
        "overall_avg_rating": round(float(avg_rating), 2),
        "total_feedbacks": total_feedbacks,
        "total_meetings": total_meetings,
    }


def get_mm_stats(db: Session) -> list[dict]:
    results = (
        db.query(
            Meeting.mm_email,
            func.avg(Feedback.rating).label("average_rating"),
            func.count(Feedback.id).label("total_feedbacks"),
        )
        .join(Feedback, Meeting.meeting_id == Feedback.meeting_id)
        .group_by(Meeting.mm_email)
        .all()
    )

    mm_meeting_counts = (
        db.query(Meeting.mm_email, func.count(Meeting.id).label("total_meetings"))
        .group_by(Meeting.mm_email)
        .all()
    )
    meeting_map = {r.mm_email: r.total_meetings for r in mm_meeting_counts}

    return [
        {
            "mm_email": r.mm_email,
            "average_rating": round(float(r.average_rating), 2),
            "total_feedbacks": r.total_feedbacks,
            "total_meetings": meeting_map.get(r.mm_email, 0),
        }
        for r in results
    ]


def get_weekly_trends(db: Session, days: int = 30, start_date: str | None = None, end_date: str | None = None) -> list[dict]:
    query = db.query(
        func.date_trunc("day", Feedback.created_at).label("day"),
        func.avg(Feedback.rating).label("average_rating"),
        func.count(Feedback.id).label("total_feedbacks"),
    )

    if start_date and end_date:
        query = query.filter(
            Feedback.created_at >= datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc),
            Feedback.created_at < datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1),
        )
    else:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        query = query.filter(Feedback.created_at >= cutoff)

    results = (
        query
        .group_by(func.date_trunc("day", Feedback.created_at))
        .order_by(func.date_trunc("day", Feedback.created_at))
        .all()
    )
    return [
        {
            "week": r.day.strftime("%Y-%m-%d"),
            "average_rating": round(float(r.average_rating), 2),
            "total_feedbacks": r.total_feedbacks,
        }
        for r in results
    ]


def get_recent_feedbacks(db: Session, limit: int = 50) -> list[dict]:
    results = (
        db.query(Feedback, Meeting.mm_email)
        .outerjoin(Meeting, Feedback.meeting_id == Meeting.meeting_id)
        .order_by(Feedback.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": fb.id,
            "meeting_id": fb.meeting_id,
            "customer_email": fb.customer_email,
            "rating": fb.rating,
            "comment": fb.comment,
            "created_at": fb.created_at.isoformat() if fb.created_at else None,
            "mm_email": mm_email,
        }
        for fb, mm_email in results
    ]


# --- Admin Users ---

def get_admin_by_username(db: Session, username: str) -> AdminUser | None:
    return db.query(AdminUser).filter(AdminUser.username == username).first()


def create_admin_user(db: Session, username: str, display_name: str, password: str) -> AdminUser:
    user = AdminUser(username=username, display_name=display_name)
    user.set_password(password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
