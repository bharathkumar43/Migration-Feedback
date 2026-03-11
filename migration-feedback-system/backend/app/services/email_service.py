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


def _logo_url() -> str:
    """Base URL for logo image (same origin as feedback form). Place logo at frontend/public/logo.png or set EMAIL_LOGO_URL."""
    base = (settings.feedback_base_url or "").rstrip("/")
    return f"{base}/logo.png"


def _build_feedback_html(customer_email: str, host_display_name: str, feedback_link: str) -> str:
    """Build the HTML email body matching the exact Migration Feedback Form (PDF): logo, * Required, title, intro, all 6 questions, then CTA link."""
    logo = _logo_url()
    return f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background: #fff; padding: 32px; margin: 0; color: #333;">
      <div style="max-width: 680px; margin: auto;">
        <p style="font-size: 13px; color: #333; margin: 0 0 8px 0;">* Required</p>
        <div style="margin-bottom: 16px;">
          <img src="{logo}" alt="CloudFuze" style="max-width: 200px; height: auto; display: block;" />
        </div>
        <h1 style="font-size: 24px; font-weight: 700; margin: 0 0 16px 0; color: #000;">Migration Feedback Form</h1>
        <p style="font-size: 14px; line-height: 1.7; margin: 0 0 24px 0; color: #333;">
          Thank you for participating in today's CloudFuze migration session.<br/>
          Your feedback helps us enhance our service and better support your migration needs.<br/>
          All information shared will remain confidential.
        </p>
        <table style="width: 100%; border-collapse: collapse; font-size: 14px; color: #333; margin-bottom: 24px;">
          <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;">1. How would you rate your overall experience? *</td></tr>
          <tr><td style="padding: 4px 0 12px 0; color: #666;">Extremely dissatisfied &nbsp;&mdash;&nbsp; Extremely satisfied</td></tr>
          <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;">2. Did we understand your business requirement properly? *</td></tr>
          <tr><td style="padding: 4px 0 12px 0; color: #666;">Yes &nbsp;&bull;&nbsp; No &nbsp;&bull;&nbsp; Partially</td></tr>
          <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;">3. After today's call, how confident do you feel about the progress of your migration project? *</td></tr>
          <tr><td style="padding: 4px 0 12px 0; color: #666;">Not Confident &nbsp;&bull;&nbsp; Slightly Confident &nbsp;&bull;&nbsp; Moderately Confident &nbsp;&bull;&nbsp; Confident &nbsp;&bull;&nbsp; Very Confident</td></tr>
          <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;">4. How would you rate the clarity and professionalism of our migration engineer during the call? *</td></tr>
          <tr><td style="padding: 4px 0 12px 0; color: #666;">Enter your answer</td></tr>
          <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;">5. Is there anything we could improve or any additional support you require? *</td></tr>
          <tr><td style="padding: 4px 0 12px 0; color: #666;">Enter your answer</td></tr>
          <tr><td style="padding: 8px 0; border-bottom: 1px solid #eee;">6. Was your concern or query addressed effectively during the call?</td></tr>
          <tr><td style="padding: 4px 0 12px 0; color: #666;">Yes, fully resolved &nbsp;&bull;&nbsp; Partially resolved &nbsp;&bull;&nbsp; Not resolved</td></tr>
        </table>
        <p style="font-size: 15px; color: #333; margin-bottom: 16px;">Please click the link below to open the form and submit your feedback.</p>
        <p style="margin-bottom: 24px;">
          <a href="{feedback_link}" style="font-size: 15px; color: #1155cc; text-decoration: underline;">Open Migration Feedback Form</a>
        </p>
        <p style="color: #666; font-size: 12px; margin: 0;">CloudFuze Migration Team &bull; This link is unique to you.</p>
      </div>
    </body>
    </html>
    """


def send_feedback_email(customer_email: str, host_display_name: str, feedback_link: str):
    html = _build_feedback_html(customer_email, host_display_name, feedback_link)
    _send_via_sendgrid(
        to=customer_email,
        subject="Migration Feedback Form — CloudFuze",
        html=html,
    )
    logger.info(f"Feedback email sent to {customer_email}")


def send_reminder_email(customer_email: str, feedback_link: str):
    """Reminder email — same template as Migration Feedback Form (PDF): logo, intro, CTA."""
    logo = _logo_url()
    html = f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background: #fff; padding: 32px; margin: 0; color: #333;">
      <div style="max-width: 680px; margin: auto;">
        <p style="font-size: 13px; color: #333; margin: 0 0 8px 0;">* Required</p>
        <div style="margin-bottom: 16px;">
          <img src="{logo}" alt="CloudFuze" style="max-width: 200px; height: auto; display: block;" />
        </div>
        <h1 style="font-size: 24px; font-weight: 700; margin: 0 0 16px 0; color: #000;">Migration Feedback Form</h1>
        <p style="font-size: 14px; line-height: 1.7; margin: 0 0 24px 0; color: #333;">
          Thank you for participating in today's CloudFuze migration session.<br/>
          Your feedback helps us enhance our service and better support your migration needs.<br/>
          All information shared will remain confidential.
        </p>
        <p style="font-size: 15px; color: #333; margin-bottom: 16px;">We noticed you haven't completed the feedback form yet. Please click the link below to open it.</p>
        <p style="margin-bottom: 24px;">
          <a href="{feedback_link}" style="font-size: 15px; color: #1155cc; text-decoration: underline;">Open Migration Feedback Form</a>
        </p>
        <p style="color: #666; font-size: 12px; margin: 0;">CloudFuze Migration Team</p>
      </div>
    </body>
    </html>
    """
    _send_via_sendgrid(
        to=customer_email,
        subject="Reminder — Migration Feedback Form",
        html=html,
    )
    logger.info(f"Reminder sent to {customer_email}")
