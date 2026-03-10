import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.database import get_db
from app.models import Meeting, FeedbackRequest, FeedbackResponse
from app.routers.auth import get_current_admin

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/summary")
def dashboard_summary(db: Session = Depends(get_db), _admin: dict = Depends(get_current_admin)):
    total_meetings = db.query(func.count(Meeting.id)).scalar() or 0
    total_feedbacks = db.query(func.count(FeedbackResponse.id)).scalar() or 0
    avg_rating = db.query(func.avg(FeedbackResponse.rating)).scalar()
    overall_avg_rating = round(float(avg_rating), 2) if avg_rating else 0.0

    mm_rows = (
        db.query(
            FeedbackResponse.host_email,
            func.count(FeedbackResponse.id).label("total"),
            func.avg(FeedbackResponse.rating).label("avg_rating"),
            func.sum(case((FeedbackResponse.rating >= 4, 1), else_=0)).label("positive"),
        )
        .group_by(FeedbackResponse.host_email)
        .order_by(func.avg(FeedbackResponse.rating).desc())
        .all()
    )

    mm_stats = [
        {
            "mm_email": row.host_email,
            "total_feedbacks": row.total,
            "average_rating": round(float(row.avg_rating), 2),
            "positive_pct": round(int(row.positive) / row.total * 100, 1) if row.total else 0,
        }
        for row in mm_rows
    ]

    return {
        "overall_avg_rating": overall_avg_rating,
        "total_feedbacks": total_feedbacks,
        "total_meetings": total_meetings,
        "mm_stats": mm_stats,
    }


@router.get("/feedbacks")
def list_feedbacks(
    limit: int = 50,
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    rows = (
        db.query(FeedbackResponse)
        .order_by(FeedbackResponse.submitted_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "customer_email": r.customer_email,
            "rating": r.rating,
            "business_requirement": r.business_requirement,
            "confidence_level": r.confidence_level,
            "engineer_rating": r.engineer_rating,
            "improvements": r.improvements,
            "concern_resolved": r.concern_resolved,
            "comment": r.comments,
            "mm_email": r.host_email,
            "created_at": r.submitted_at.isoformat() if r.submitted_at else None,
        }
        for r in rows
    ]


@router.get("/trends")
def daily_trends(
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
    _admin: dict = Depends(get_current_admin),
):
    query = db.query(FeedbackResponse)

    if start_date:
        try:
            sd = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(FeedbackResponse.submitted_at >= sd)
        except ValueError:
            pass
    if end_date:
        try:
            ed = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(FeedbackResponse.submitted_at < ed)
        except ValueError:
            pass

    feedbacks = query.order_by(FeedbackResponse.submitted_at.asc()).all()

    if not feedbacks:
        return []

    weeks: dict[str, list] = {}
    for fb in feedbacks:
        if not fb.submitted_at:
            continue
        week_start = fb.submitted_at - timedelta(days=fb.submitted_at.weekday())
        week_key = week_start.strftime("%Y-%m-%d")
        weeks.setdefault(week_key, []).append(fb.rating)

    return [
        {
            "week": wk,
            "average_rating": round(sum(ratings) / len(ratings), 2),
            "total_feedbacks": len(ratings),
        }
        for wk, ratings in sorted(weeks.items())
    ]


@router.get("/leaderboard")
def leaderboard(db: Session = Depends(get_db), _admin: dict = Depends(get_current_admin)):
    mm_rows = (
        db.query(
            FeedbackResponse.host_email,
            func.count(FeedbackResponse.id).label("total"),
            func.avg(FeedbackResponse.rating).label("avg_rating"),
            func.sum(case((FeedbackResponse.rating >= 4, 1), else_=0)).label("positive"),
        )
        .group_by(FeedbackResponse.host_email)
        .order_by(func.avg(FeedbackResponse.rating).desc())
        .all()
    )

    return [
        {
            "mm_email": row.host_email,
            "total_feedbacks": row.total,
            "average_rating": round(float(row.avg_rating), 2),
            "positive_pct": round(int(row.positive) / row.total * 100, 1) if row.total else 0,
        }
        for row in mm_rows
    ]
