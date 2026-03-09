from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Migration Feedback System"
    debug: bool = False

    database_url: str = "postgresql://postgres:postgres@localhost:5432/migration_feedback"

    zoom_webhook_secret: str = ""
    zoom_verification_token: str = ""
    zoom_account_id: str = ""
    zoom_client_id: str = ""
    zoom_client_secret: str = ""

    smtp_host: str = "smtp.office365.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""

    sendgrid_api_key: str = ""
    sendgrid_from_email: str = ""

    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_project_key: str = "MIG"

    feedback_base_url: str = "http://localhost:5173"
    feedback_token_secret: str = "change-me-in-production"

    admin_username: str = "admin"
    admin_password: str = "changeme"
    admin_token_secret: str = "admin-secret-change-in-production"

    internal_domain: str = "cloudfuze.com"

    reminder_delay_hours: int = 24

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
