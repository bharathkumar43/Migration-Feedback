import logging
from datetime import datetime, timedelta, timezone

from app.config import get_settings
from app.database import SessionLocal
from app.models import FeedbackRequest
from app.services.email_service import send_reminder_email

logger = logging.getLogger(__name__)
settings = get_settings()


def send_pending_reminders():
    cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.reminder_delay_hours)
    db = SessionLocal()
    try:
        pending = (
            db.query(FeedbackRequest)
            .filter(
                FeedbackRequest.completed == False,
                FeedbackRequest.reminder_sent == False,
                FeedbackRequest.created_at <= cutoff,
            )
            .all()
        )

        for fb_req in pending:
            feedback_link = (
                settings.feedback_form_url.strip()
                if settings.feedback_form_url.strip()
                else f"{settings.feedback_base_url}/feedback?token={fb_req.token}"
            )
            try:
                send_reminder_email(fb_req.customer_email, feedback_link)
                fb_req.reminder_sent = True
                fb_req.reminder_sent_at = datetime.now(timezone.utc)
                db.commit()
                logger.info(f"Reminder sent to {fb_req.customer_email}")
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to send reminder to {fb_req.customer_email}: {e}")

        logger.info(f"Reminder job complete — processed {len(pending)} pending requests")
    except Exception as e:
        logger.exception(f"Reminder job failed: {e}")
    finally:
        db.close()
