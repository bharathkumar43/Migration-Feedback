from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.crud import get_overall_stats, get_mm_stats, get_weekly_trends, get_recent_feedbacks
from app.schemas import DashboardSummary
from app.routers.auth import require_admin

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(admin: str = Depends(require_admin), db: Session = Depends(get_db)):
    stats = get_overall_stats(db)
    mm = get_mm_stats(db)
    trends = get_weekly_trends(db)

    return DashboardSummary(
        overall_avg_rating=stats["overall_avg_rating"],
        total_feedbacks=stats["total_feedbacks"],
        total_meetings=stats["total_meetings"],
        mm_stats=mm,
        weekly_trends=trends,
    )


@router.get("/leaderboard")
def leaderboard(admin: str = Depends(require_admin), db: Session = Depends(get_db)):
    """Returns migration managers ranked by average rating (descending)."""
    mm = get_mm_stats(db)
    ranked = sorted(mm, key=lambda x: x["average_rating"], reverse=True)
    return ranked


@router.get("/trends")
def daily_trends(
    start_date: str = Query(default=None, description="YYYY-MM-DD"),
    end_date: str = Query(default=None, description="YYYY-MM-DD"),
    admin: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Returns daily trend data, optionally filtered by date range."""
    return get_weekly_trends(db, start_date=start_date, end_date=end_date)


@router.get("/feedbacks")
def recent_feedbacks(admin: str = Depends(require_admin), limit: int = Query(default=50, le=200), db: Session = Depends(get_db)):
    """Returns individual feedback records with customer email, rating, comment, and date."""
    return get_recent_feedbacks(db, limit=limit)
