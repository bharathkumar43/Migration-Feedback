import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Migration Feedback System"
    debug: bool = False

    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/migration_feedback"
    )

    zoom_webhook_secret: str = os.getenv("ZOOM_WEBHOOK_SECRET", "")
    zoom_verification_token: str = os.getenv("ZOOM_VERIFICATION_TOKEN", "")
    zoom_account_id: str = os.getenv("ZOOM_ACCOUNT_ID", "")
    zoom_client_id: str = os.getenv("ZOOM_CLIENT_ID", "")
    zoom_client_secret: str = os.getenv("ZOOM_CLIENT_SECRET", "")

    smtp_host: str = os.getenv("SMTP_HOST", "smtp.office365.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    smtp_from_email: str = os.getenv("SMTP_FROM_EMAIL", "")

    jira_base_url: str = os.getenv("JIRA_BASE_URL", "")
    jira_email: str = os.getenv("JIRA_EMAIL", "")
    jira_api_token: str = os.getenv("JIRA_API_TOKEN", "")
    jira_project_key: str = os.getenv("JIRA_PROJECT_KEY", "MIG")

    feedback_base_url: str = os.getenv("FEEDBACK_BASE_URL", "http://localhost:5173")
    feedback_token_secret: str = os.getenv("FEEDBACK_TOKEN_SECRET", "change-me-in-production")

    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "changeme")
    admin_token_secret: str = os.getenv("ADMIN_TOKEN_SECRET", "admin-secret-change-in-production")

    internal_domain: str = os.getenv("INTERNAL_DOMAIN", "cloudfuze.com")

    reminder_delay_hours: int = int(os.getenv("REMINDER_DELAY_HOURS", "24"))

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
