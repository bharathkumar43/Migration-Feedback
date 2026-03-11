import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Columns to add to feedback_responses if missing (name, sql type)
FEEDBACK_RESPONSE_EXTRA_COLUMNS = [
    ("business_requirement", "VARCHAR"),
    ("confidence_level", "VARCHAR"),
    ("engineer_rating", "INTEGER"),
    ("improvements", "TEXT"),
    ("concern_resolved", "VARCHAR"),
    ("comments", "TEXT"),
]


def ensure_feedback_responses_columns():
    """Add missing columns to feedback_responses (e.g. after deploy with older schema)."""
    with engine.connect() as conn:
        for col_name, col_type in FEEDBACK_RESPONSE_EXTRA_COLUMNS:
            try:
                conn.execute(
                    text(
                        "ALTER TABLE feedback_responses ADD COLUMN IF NOT EXISTS "
                        + col_name
                        + " "
                        + col_type
                    )
                )
            except Exception as e:
                logger.warning("Migration add column %s: %s", col_name, e)
        conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
