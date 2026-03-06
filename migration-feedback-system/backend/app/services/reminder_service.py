import logging
from app.config import get_settings
from app.database import SessionLocal
from app.crud import get_pending_reminders, mark_reminder_sent
from app.services.email_service import send_reminder_email

logger = logging.getLogger(__name__)
settings = get_settings()


def send_pending_reminders():
    """Scheduled job: send reminder emails for unanswered feedback requests."""
    db = SessionLocal()
    try:
        pending = get_pending_reminders(db, hours=settings.reminder_delay_hours)
        logger.info(f"Found {len(pending)} pending reminder(s)")

        for req in pending:
            feedback_link = f"{settings.feedback_base_url}/feedback?token={req.token}"
            try:
                send_reminder_email(req.customer_email, feedback_link)
                mark_reminder_sent(db, req.id)
                logger.info(f"Reminder sent to {req.customer_email}")
            except Exception as e:
                logger.error(f"Failed to send reminder to {req.customer_email}: {e}")
    finally:
        db.close()
