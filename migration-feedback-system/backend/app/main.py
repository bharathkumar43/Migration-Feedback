import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import get_settings
from app.database import engine, Base, SessionLocal
from app.routers import zoom_webhook, feedback, dashboard, auth
from app.routers.auth import seed_default_admin
from app.services.reminder_service import send_pending_reminders

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")

        db = SessionLocal()
        try:
            seed_default_admin(db)
        finally:
            db.close()

        scheduler.add_job(send_pending_reminders, "interval", hours=1, id="reminder_job")
        scheduler.start()
        logger.info("Reminder scheduler started")

        s = get_settings()
        logger.info(f"FEEDBACK_BASE_URL = {s.feedback_base_url}")
        logger.info(f"INTERNAL_DOMAIN = {s.internal_domain}")
        logger.info(f"Resend configured = {bool(s.resend_api_key)}")
        logger.info(f"Resend from = {s.resend_from_email}")
    except Exception as e:
        logger.exception("Startup failed: %s", e)
        raise

    yield

    scheduler.shutdown()
    logger.info("Scheduler shut down")


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(zoom_webhook.router, prefix="/webhooks", tags=["Zoom Webhooks"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": settings.app_name}
