import logging
import time
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_token_cache = {"access_token": None, "expires_at": 0}


def _get_access_token() -> str:
    """Obtain a Server-to-Server OAuth access token, cached until expiry."""
    now = time.time()
    if _token_cache["access_token"] and _token_cache["expires_at"] > now + 60:
        return _token_cache["access_token"]

    if not settings.zoom_account_id or not settings.zoom_client_id:
        raise RuntimeError("Zoom OAuth credentials not configured (ZOOM_ACCOUNT_ID, ZOOM_CLIENT_ID, ZOOM_CLIENT_SECRET)")

    response = httpx.post(
        "https://zoom.us/oauth/token",
        params={"grant_type": "account_credentials", "account_id": settings.zoom_account_id},
        auth=(settings.zoom_client_id, settings.zoom_client_secret),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()

    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 3600)

    logger.info("Zoom OAuth token obtained successfully")
    return _token_cache["access_token"]


def get_past_meeting_participants(meeting_id: str, max_retries: int = 3) -> list[dict]:
    """
    Fetch participants from a past meeting via the Zoom API.

    The Zoom API may return 404 for a few seconds after a meeting ends
    because past meeting data is not immediately available. We retry
    with a short delay to handle this.
    """
    token = _get_access_token()
    url = f"https://api.zoom.us/v2/past_meetings/{meeting_id}/participants"
    headers = {"Authorization": f"Bearer {token}"}

    all_participants = []
    next_page_token = ""

    for attempt in range(max_retries):
        try:
            params = {"page_size": 300}
            if next_page_token:
                params["next_page_token"] = next_page_token

            response = httpx.get(url, headers=headers, params=params, timeout=15)

            if response.status_code == 404 and attempt < max_retries - 1:
                wait = 5 * (attempt + 1)
                logger.info(f"Past meeting {meeting_id} not ready yet, retrying in {wait}s...")
                time.sleep(wait)
                continue

            response.raise_for_status()
            data = response.json()

            participants = data.get("participants", [])
            all_participants.extend(participants)

            next_page_token = data.get("next_page_token", "")
            if not next_page_token:
                break

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404 and attempt < max_retries - 1:
                wait = 5 * (attempt + 1)
                logger.info(f"Past meeting {meeting_id} not ready yet, retrying in {wait}s...")
                time.sleep(wait)
                continue
            logger.error(f"Zoom API error fetching participants: {e}")
            raise

    logger.info(f"Fetched {len(all_participants)} participant(s) for meeting {meeting_id}")
    return all_participants
