import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models import Meeting, FeedbackRequest
from app.services.email_service import send_feedback_email

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


def _verify_zoom_signature(request_body: bytes, timestamp: str, signature: str) -> bool:
    if not settings.zoom_webhook_secret:
        return True
    message = f"v0:{timestamp}:{request_body.decode()}"
    expected = "v0=" + hmac.new(
        settings.zoom_webhook_secret.encode(), message.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def _is_external_participant(email: str) -> bool:
    if not email or not settings.internal_domain:
        return False
    return not email.lower().endswith(f"@{settings.internal_domain.lower()}")


def _generate_feedback_token() -> str:
    return secrets.token_urlsafe(32)


@router.post("")
async def zoom_webhook(request: Request):
    body = await request.body()
    payload = await request.json()

    event = payload.get("event", "")

    if event == "endpoint.url_validation":
        plain_token = payload.get("payload", {}).get("plainToken", "")
        hash_value = hmac.new(
            settings.zoom_webhook_secret.encode(),
            plain_token.encode(),
            hashlib.sha256,
        ).hexdigest()
        return {"plainToken": plain_token, "encryptedToken": hash_value}

    timestamp = request.headers.get("x-zm-request-timestamp", "")
    signature = request.headers.get("x-zm-signature", "")

    if settings.zoom_webhook_secret and not _verify_zoom_signature(body, timestamp, signature):
        raise HTTPException(status_code=401, detail="Invalid Zoom signature")

    if event == "meeting.ended":
        meeting_payload = payload.get("payload", {}).get("object", {})
        zoom_meeting_id = str(meeting_payload.get("id", ""))
        topic = meeting_payload.get("topic", "")
        host_email = meeting_payload.get("host_email", "")
        host_display_name = meeting_payload.get("host", {}).get("display_name", host_email)
        start_time_str = meeting_payload.get("start_time", "")
        end_time_str = meeting_payload.get("end_time", "")
        duration = meeting_payload.get("duration", 0)
        participants = meeting_payload.get("participants", [])

        if not participants:
            participants = payload.get("payload", {}).get("participants", [])

        db: Session = SessionLocal()
        try:
            for p in participants:
                p_email = p.get("email", "") or p.get("user_email", "")
                if not p_email or not _is_external_participant(p_email):
                    continue

                meeting = Meeting(
                    zoom_meeting_id=zoom_meeting_id,
                    host_email=host_email,
                    host_display_name=host_display_name,
                    participant_email=p_email,
                    topic=topic,
                    start_time=datetime.fromisoformat(start_time_str.replace("Z", "+00:00")) if start_time_str else None,
                    end_time=datetime.fromisoformat(end_time_str.replace("Z", "+00:00")) if end_time_str else None,
                    duration_minutes=duration,
                )
                db.add(meeting)
                db.flush()

                token = _generate_feedback_token()
                feedback_link = f"{settings.feedback_base_url}/feedback?token={token}"
                fb_request = FeedbackRequest(
                    meeting_id=meeting.id,
                    customer_email=p_email,
                    host_email=host_email,
                    host_display_name=host_display_name,
                    token=token,
                )
                db.add(fb_request)
                db.commit()

                try:
                    send_feedback_email(p_email, host_display_name, feedback_link)
                except Exception as e:
                    logger.error(f"Failed to send feedback email to {p_email}: {e}")

            logger.info(f"Processed meeting.ended for {zoom_meeting_id}")
        except Exception as e:
            db.rollback()
            logger.exception(f"Error processing webhook: {e}")
            raise HTTPException(status_code=500, detail="Internal error")
        finally:
            db.close()

    return {"status": "ok"}
