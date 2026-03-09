import hashlib
import hmac
import logging
import secrets
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Request, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.models import Meeting, FeedbackRequest
from app.services.email_service import send_feedback_email
from app.services.zoom_api import get_past_meeting_participants

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
        logger.debug(f"Skipping participant (no email or no internal_domain): email={email!r}")
        return False
    is_external = not email.lower().endswith(f"@{settings.internal_domain.lower()}")
    logger.info(f"Participant {email} — external={is_external} (internal_domain={settings.internal_domain})")
    return is_external


def _generate_feedback_token() -> str:
    return secrets.token_urlsafe(32)


def _extract_unique_emails(participants: list[dict]) -> list[dict]:
    """Deduplicate participants by email."""
    seen = set()
    unique = []
    for p in participants:
        email = (p.get("user_email") or p.get("email") or "").strip().lower()
        if email and email not in seen:
            seen.add(email)
            unique.append({"email": email, "name": p.get("name", "")})
    return unique


@router.post("/zoom")
async def zoom_webhook(request: Request):
    body = await request.body()
    payload = await request.json()

    event = payload.get("event", "")
    logger.info(f"Zoom webhook received: event={event}")

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

        logger.info(
            f"Meeting ended: id={zoom_meeting_id}, topic={topic!r}, "
            f"host={host_email}, host_name={host_display_name}"
        )

        # Zoom meeting.ended does NOT include participants.
        # Wait briefly then fetch via the Past Meeting Participants API.
        time.sleep(3)
        api_participants = get_past_meeting_participants(zoom_meeting_id)
        unique_participants = _extract_unique_emails(api_participants)

        logger.info(f"Found {len(unique_participants)} unique participants for meeting {zoom_meeting_id}")

        if not unique_participants:
            logger.warning(f"No participants found for meeting {zoom_meeting_id} — no emails will be sent")
            return {"status": "ok", "detail": "no participants found"}

        db: Session = SessionLocal()
        try:
            for p in unique_participants:
                p_email = p["email"]

                if not _is_external_participant(p_email):
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

                logger.info(f"Created feedback request for {p_email}, link={feedback_link}")

                try:
                    send_feedback_email(p_email, host_display_name, feedback_link)
                    logger.info(f"Feedback email sent successfully to {p_email}")
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
