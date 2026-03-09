import logging
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import AdminUser

import hashlib
import hmac
import json
import base64

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()
settings = get_settings()


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def _create_token(data: dict, secret: str, expires_hours: int = 24) -> str:
    payload = {
        **data,
        "exp": (datetime.now(timezone.utc) + timedelta(hours=expires_hours)).isoformat(),
    }
    payload_bytes = json.dumps(payload, sort_keys=True).encode()
    signature = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
    token = base64.urlsafe_b64encode(payload_bytes).decode() + "." + signature
    return token


def _decode_token(token: str, secret: str) -> dict:
    try:
        parts = token.rsplit(".", 1)
        if len(parts) != 2:
            raise ValueError("Invalid token format")
        payload_b64, signature = parts
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        expected_sig = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            raise ValueError("Invalid signature")
        payload = json.loads(payload_bytes)
        exp = datetime.fromisoformat(payload["exp"])
        if exp < datetime.now(timezone.utc):
            raise ValueError("Token expired")
        return payload
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    return _decode_token(credentials.credentials, settings.admin_token_secret)


def seed_default_admin(db: Session):
    existing = db.query(AdminUser).filter(AdminUser.username == settings.admin_username).first()
    if not existing:
        admin = AdminUser(
            username=settings.admin_username,
            hashed_password=_hash_password(settings.admin_password),
        )
        db.add(admin)
        db.commit()
        logger.info(f"Default admin '{settings.admin_username}' created")
    else:
        logger.info("Default admin already exists")


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(AdminUser).filter(AdminUser.username == body.username).first()
    if not user or not _verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = _create_token({"sub": user.username}, settings.admin_token_secret)
    return TokenResponse(access_token=token)


@router.get("/me")
def me(admin: dict = Depends(get_current_admin)):
    return {"username": admin["sub"]}
