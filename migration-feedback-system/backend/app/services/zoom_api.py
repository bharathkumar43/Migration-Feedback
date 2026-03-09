import logging
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

ZOOM_OAUTH_URL = "https://zoom.us/oauth/token"
ZOOM_API_BASE = "https://api.zoom.us/v2"


def _get_access_token() -> str | None:
    if not settings.zoom_account_id or not settings.zoom_client_id or not settings.zoom_client_secret:
        logger.warning("Zoom OAuth credentials not configured")
        return None

    response = httpx.post(
        ZOOM_OAUTH_URL,
        params={"grant_type": "account_credentials", "account_id": settings.zoom_account_id},
        auth=(settings.zoom_client_id, settings.zoom_client_secret),
        timeout=15,
    )
    response.raise_for_status()
    token = response.json().get("access_token")
    logger.info("Zoom OAuth token obtained")
    return token


def get_past_meeting_participants(meeting_id: str) -> list[dict]:
    token = _get_access_token()
    if not token:
        return []

    participants = []
    next_page_token = ""

    while True:
        url = f"{ZOOM_API_BASE}/past_meetings/{meeting_id}/participants"
        params = {"page_size": 300}
        if next_page_token:
            params["next_page_token"] = next_page_token

        response = httpx.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=15,
        )

        if response.status_code == 404:
            logger.warning(f"Past meeting {meeting_id} not found in Zoom API (may not be ready yet)")
            return []

        response.raise_for_status()
        data = response.json()

        for p in data.get("participants", []):
            participants.append(p)

        next_page_token = data.get("next_page_token", "")
        if not next_page_token:
            break

    logger.info(f"Fetched {len(participants)} participants for meeting {meeting_id}")
    return participants
