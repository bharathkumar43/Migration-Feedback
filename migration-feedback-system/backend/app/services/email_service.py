import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _build_feedback_html(customer_email: str, mm_email: str, feedback_link: str) -> str:
    """Build the HTML email body with star rating links."""
    stars_html = ""
    for i in range(1, 6):
        star_link = f"{feedback_link}&rating={i}"
        stars_html += (
            f'<a href="{star_link}" '
            f'style="text-decoration:none;font-size:32px;margin:0 4px;color:{"#f5a623" if i <= 3 else "#e0e0e0"};">'
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
          You recently had a migration call with <strong>{mm_email}</strong>.
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


def send_feedback_email(customer_email: str, mm_email: str, feedback_link: str):
    if not settings.smtp_username:
        logger.warning("SMTP not configured — email skipped")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "How was your migration call? — Quick Feedback"
    msg["From"] = settings.smtp_from_email or settings.smtp_username
    msg["To"] = customer_email

    html = _build_feedback_html(customer_email, mm_email, feedback_link)
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.sendmail(msg["From"], [customer_email], msg.as_string())

    logger.info(f"Email sent to {customer_email}")


def send_reminder_email(customer_email: str, feedback_link: str):
    if not settings.smtp_username:
        logger.warning("SMTP not configured — reminder skipped")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Reminder: We'd still love your feedback!"
    msg["From"] = settings.smtp_from_email or settings.smtp_username
    msg["To"] = customer_email

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
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.sendmail(msg["From"], [customer_email], msg.as_string())

    logger.info(f"Reminder sent to {customer_email}")
