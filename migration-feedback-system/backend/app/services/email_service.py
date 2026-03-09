import logging
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SENDGRID_API_URL = "https://api.sendgrid.com/v3/mail/send"


def _send_via_sendgrid(to: str, subject: str, html: str):
    """Send an email using the SendGrid v3 API."""
    if not settings.sendgrid_api_key:
        logger.warning("SENDGRID_API_KEY not configured — email skipped")
        return

    response = httpx.post(
        SENDGRID_API_URL,
        headers={
            "Authorization": f"Bearer {settings.sendgrid_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "personalizations": [{"to": [{"email": to}]}],
            "from": {"email": settings.sendgrid_from_email},
            "subject": subject,
            "content": [{"type": "text/html", "value": html}],
        },
        timeout=15,
    )
    response.raise_for_status()
    logger.info(f"SendGrid API response: status={response.status_code}")


def _build_feedback_html(customer_email: str, host_display_name: str, feedback_link: str) -> str:
    """Build the HTML email body with star rating links. host_display_name is shown (not email)."""
    display = (host_display_name or "our team").strip()
    stars_html = ""
    for i in range(5, 0, -1):
        star_link = f"{feedback_link}&rating={i}"
        color = "#f5a623" if i >= 3 else "#e0e0e0"
        stars_html += (
            f'<a href="{star_link}" '
            f'style="text-decoration:none;font-size:32px;margin:0 4px;color:{color};">'
            f"{'&#9733;' * i}{'&#9734;' * (5 - i)}"
            f"</a><br/>"
        )

    return f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f9; padding: 40px;">
      <div style="max-width: 560px; margin: auto; background: #fff; border-radius: 12px;
                  padding: 40px; box-shadow: 0 2px 12px rgba(0,0,0,0.08);">
        <h2 style="color: #1a1a2e; margin-bottom: 8px;">How was your experience?</h2>
        <p style="color: #555; line-height: 1.6;">
          Hi,<br/>
          You recently had a migration call with <strong>{display}</strong>.
          We'd love to hear your feedback — it only takes a few seconds.
        </p>

        <div style="text-align: center; margin: 32px 0;">
          <p style="font-size: 14px; color: #888; margin-bottom: 12px;">Click a rating below:</p>
          {stars_html}
        </div>

        <div style="text-align: center; margin-top: 24px;">
          <a href="{feedback_link}"
             style="display:inline-block; padding: 12px 32px; background: #2563eb; color: #fff;
                    border-radius: 8px; text-decoration: none; font-weight: 600;">
            Leave Detailed Feedback
          </a>
        </div>

        <p style="color: #999; font-size: 12px; margin-top: 32px; text-align: center;">
          CloudFuze Migration Team &bull; This link is unique to you.
        </p>
      </div>
    </body>
    </html>
    """


def send_feedback_email(customer_email: str, host_display_name: str, feedback_link: str):
    html = _build_feedback_html(customer_email, host_display_name, feedback_link)
    _send_via_sendgrid(
        to=customer_email,
        subject="How was your migration call? — Quick Feedback",
        html=html,
    )
    logger.info(f"Feedback email sent to {customer_email}")


def send_reminder_email(customer_email: str, feedback_link: str):
    html = f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f9; padding: 40px;">
      <div style="max-width: 560px; margin: auto; background: #fff; border-radius: 12px;
                  padding: 40px; box-shadow: 0 2px 12px rgba(0,0,0,0.08);">
        <h2 style="color: #1a1a2e;">Just a friendly reminder</h2>
        <p style="color: #555; line-height: 1.6;">
          We noticed you haven't shared your feedback yet. Your input helps us improve
          our migration service.
        </p>
        <div style="text-align: center; margin: 32px 0;">
          <a href="{feedback_link}"
             style="display:inline-block; padding: 12px 32px; background: #2563eb; color: #fff;
                    border-radius: 8px; text-decoration: none; font-weight: 600;">
            Share Feedback Now
          </a>
        </div>
        <p style="color: #999; font-size: 12px; margin-top: 32px; text-align: center;">
          CloudFuze Migration Team
        </p>
      </div>
    </body>
    </html>
    """
    _send_via_sendgrid(
        to=customer_email,
        subject="Reminder: We'd still love your feedback!",
        html=html,
    )
    logger.info(f"Reminder sent to {customer_email}")
