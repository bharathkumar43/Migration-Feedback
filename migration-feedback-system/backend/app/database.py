import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

IS_RENDER = os.getenv("RENDER") == "true"

if not IS_RENDER:
    # Load .env only when running locally so DATABASE_URL is available
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

# On Render, DATABASE_URL must be set in Web Service → Environment (or via linked PostgreSQL)
# Locally, fall back to default if not in .env
DATABASE_URL = os.getenv("DATABASE_URL")
_render_needs_url = IS_RENDER and (not DATABASE_URL or "localhost" in (DATABASE_URL or "") or "127.0.0.1" in (DATABASE_URL or ""))
if not DATABASE_URL or _render_needs_url:
    if IS_RENDER:
        print(
            "ERROR: DATABASE_URL is not set or points to localhost. On Render, add DATABASE_URL in your "
            "Web Service → Environment (use the Internal Database URL from your Render PostgreSQL), "
            "or link a PostgreSQL database so Render sets it automatically.",
            file=sys.stderr,
        )
        sys.exit(1)
    DATABASE_URL = DATABASE_URL or "postgresql://postgres:postgres@localhost:5432/migration_feedback"

# Render may provide "postgres://"; SQLAlchemy requires "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
