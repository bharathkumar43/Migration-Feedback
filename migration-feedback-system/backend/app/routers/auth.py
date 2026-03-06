import hashlib
import hmac
import time
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.crud import get_admin_by_username, create_admin_user

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()
security = HTTPBearer()

TOKEN_EXPIRY_SECONDS = 24 * 60 * 60  # 24 hours


class LoginRequest(BaseModel):
    username: str
    password: str


class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    display_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=6)


def _generate_token(username: str, display_name: str) -> str:
    expires = int(time.time()) + TOKEN_EXPIRY_SECONDS
    payload = f"{username}:{expires}"
    signature = hmac.HMAC(
        settings.admin_token_secret.encode(),
        payload.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{payload}:{signature}"


def _verify_token(token: str) -> str | None:
    """Returns the username if valid, None otherwise."""
    parts = token.split(":")
    if len(parts) != 3:
        return None
    username, expires_str, signature = parts
    try:
        expires = int(expires_str)
    except ValueError:
        return None
    if time.time() > expires:
        return None
    expected = hmac.HMAC(
        settings.admin_token_secret.encode(),
        f"{username}:{expires_str}".encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return None
    return username


def require_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """FastAPI dependency that protects endpoints behind admin auth."""
    username = _verify_token(credentials.credentials)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return username


def seed_default_admin(db: Session):
    """Create the default admin account if no admin users exist yet."""
    from app.models import AdminUser
    count = db.query(AdminUser).count()
    if count == 0:
        create_admin_user(db, "admin", "Admin", "admin123")
        logger.info("Default admin account created (username: admin)")


@router.post("/login")
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = get_admin_by_username(db, body.username)
    if not user or not user.verify_password(body.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = _generate_token(user.username, user.display_name)
    logger.info(f"Admin login: {user.username}")
    return {"token": token, "username": user.username, "display_name": user.display_name}


@router.post("/signup")
def signup(body: SignupRequest, db: Session = Depends(get_db)):
    if get_admin_by_username(db, body.username):
        raise HTTPException(status_code=409, detail="Username already taken")

    user = create_admin_user(db, body.username, body.display_name, body.password)
    token = _generate_token(user.username, user.display_name)
    logger.info(f"Admin signup: {user.username}")
    return {"token": token, "username": user.username, "display_name": user.display_name}
