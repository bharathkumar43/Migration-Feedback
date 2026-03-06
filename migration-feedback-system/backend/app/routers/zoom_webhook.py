import hashlib
import hmac
import json
import logging
from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.orm import Session

import secrets
from app.config import get_settings
from app.database import get_db
from app.crud import create_meeting, create_feedback_request
from app.utils.domain_parser import extract_domain, is_internal_email
from app.services.email_service import send_feedback_email
from app.services.zoom_service import get_past_meeting_participants
from app.schemas import MeetingCreate

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


def verify_zoom_signature(request_body: bytes, timestamp: str, signature: str) -> bool:
    """Validate the Zoom webhook event signature using HMAC-SHA256."""
    if not settings.zoom_webhook_secret:
        logger.warning("ZOOM_WEBHOOK_SECRET not configured — skipping signature validation")
        return True

    message = f"v0:{timestamp}:{request_body.decode('utf-8')}"
    expected = "v0=" + hmac.HMAC(
        settings.zoom_webhook_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


@router.post("/zoom")
async def zoom_webhook(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    payload = json.loads(body)

    # --- Zoom URL Validation (CRC challenge-response) ---
    if payload.get("event") == "endpoint.url_validation":
        plain_token = payload["payload"]["plainToken"]
        hash_digest = hmac.HMAC(
            settings.zoom_webhook_secret.encode("utf-8"),
            plain_token.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return {"plainToken": plain_token, "encryptedToken": hash_digest}

    # --- Signature verification ---
    timestamp = request.headers.get("x-zm-request-timestamp", "")
    signature = request.headers.get("x-zm-signature", "")
    if not verify_zoom_signature(body, timestamp, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    event_type = payload.get("event", "")
    logger.info(f"Received Zoom event: {event_type}")

    if event_type != "meeting.ended":
        return {"status": "ignored", "event": event_type}

    meeting_obj = payload.get("payload", {}).get("object", {})
    meeting_id = str(meeting_obj.get("id", ""))
    host_email = meeting_obj.get("host_email", "")
    meeting_uuid = meeting_obj.get("uuid", "")

    if not meeting_id:
        raise HTTPException(status_code=400, detail="Missing meeting ID")

    # Fetch full participant list from the Zoom API (webhook payload lacks emails)
    try:
        api_participants = get_past_meeting_participants(meeting_id)
    except Exception as e:
        logger.error(f"Failed to fetch participants from Zoom API for meeting {meeting_id}: {e}")
        api_participants = []

    # Fall back to webhook payload participants if the API returned nothing
    if not api_participants:
        webhook_participants = meeting_obj.get("participants", [])
        api_participants = [
            {"user_email": p.get("email", "") or p.get("user_email", "")}
            for p in webhook_participants
        ]

    external_participants = []
    mm_email = host_email
    seen_emails = set()

    for p in api_participants:
        email = (p.get("user_email") or p.get("email") or "").strip().lower()
        if not email or email in seen_emails:
            continue
        seen_emails.add(email)

        if is_internal_email(email, settings.internal_domain):
            mm_email = email
        else:
            external_participants.append(email)

    if not external_participants:
        logger.info(f"Meeting {meeting_id}: No external participants found")
        return {"status": "no_external_participants"}

    customer_domain = extract_domain(external_participants[0])
    meeting_record = MeetingCreate(
        meeting_id=meeting_id,
        mm_email=mm_email,
        customer_domain=customer_domain,
    )
    create_meeting(db, meeting_record)

    emails_sent = 0
    for email in external_participants:
        token = secrets.token_urlsafe(32)
        req = create_feedback_request(db, meeting_id, email, token)

        if req is None:
            logger.info(f"Feedback request already exists for {email} on meeting {meeting_id}, skipping")
            continue

        feedback_link = f"{settings.feedback_base_url}/feedback?token={token}"
        try:
            send_feedback_email(email, mm_email, feedback_link)
            logger.info(f"Feedback email sent to {email}")
            emails_sent += 1
        except Exception as e:
            logger.error(f"Failed to send email to {email}: {e}")

    return {
        "status": "processed",
        "meeting_id": meeting_id,
        "emails_sent": emails_sent,
    }
