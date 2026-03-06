import logging
import httpx
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def create_jira_ticket(
    meeting_id: str,
    customer_email: str,
    rating: int,
    comment: str | None = None,
) -> dict | None:
    """Create a Jira issue when a customer leaves a low rating (<=2)."""
    if not settings.jira_base_url or not settings.jira_api_token:
        logger.warning("Jira not configured — ticket creation skipped")
        return None

    summary = f"Low migration feedback (rating {rating}/5) — Meeting {meeting_id}"
    description = (
        f"A customer provided a low satisfaction rating after a migration call.\n\n"
        f"*Meeting ID:* {meeting_id}\n"
        f"*Customer Email:* {customer_email}\n"
        f"*Rating:* {rating}/5\n"
        f"*Comment:* {comment or 'No comment provided'}\n\n"
        f"Please follow up with the customer and the assigned migration manager."
    )

    payload = {
        "fields": {
            "project": {"key": settings.jira_project_key},
            "summary": summary,
            "description": description,
            "issuetype": {"name": "Task"},
            "priority": {"name": "High"},
        }
    }

    url = f"{settings.jira_base_url.rstrip('/')}/rest/api/2/issue"

    try:
        response = httpx.post(
            url,
            json=payload,
            auth=(settings.jira_email, settings.jira_api_token),
            headers={"Content-Type": "application/json"},
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()
        logger.info(f"Jira ticket created: {data.get('key')}")
        return data
    except httpx.HTTPError as e:
        logger.error(f"Jira API error: {e}")
        raise
