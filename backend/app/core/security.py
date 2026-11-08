from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.entities import User

bearer = HTTPBearer(auto_error=False)
PBKDF2_ITERATIONS = 310_000


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${_b64encode(salt)}${_b64encode(derived)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), _b64decode(salt), int(iterations))
        return hmac.compare_digest(_b64encode(derived), expected)
    except (ValueError, TypeError):
        return False


def create_access_token(user: User, expires_seconds: int = 8 * 60 * 60) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": str(user.id), "role": user.role, "email": user.email, "exp": int(time.time()) + expires_seconds}
    signing_input = f"{_b64encode(json.dumps(header, separators=(',', ':')).encode())}.{_b64encode(json.dumps(payload, separators=(',', ':')).encode())}"
    signature = hmac.new(settings.secret_key.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64encode(signature)}"


def decode_access_token(token: str) -> dict | None:
    try:
        if len(token) > 4096:
            return None
        header, payload, signature = token.split(".", 2)
        header_data = json.loads(_b64decode(header))
        if header_data.get("alg") != "HS256" or header_data.get("typ") != "JWT":
            return None
        signing_input = f"{header}.{payload}"
        expected = hmac.new(settings.secret_key.encode(), signing_input.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64encode(expected), signature):
            return None
        data = json.loads(_b64decode(payload))
        if int(data.get("exp", 0)) <= int(time.time()):
            return None
        return data
    except (ValueError, TypeError, json.JSONDecodeError, KeyError):
        return None


def auth_guard(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)):
    if not settings.auth_enabled:
        return None
    if credentials is None:
        raise HTTPException(401, "Authentication is required.", headers={"WWW-Authenticate": "Bearer"})
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(401, "Your session is invalid or expired. Sign in again.", headers={"WWW-Authenticate": "Bearer"})
    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(401, "This account is unavailable.")
    return user


def require_admin(credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)):
    user = auth_guard(credentials, db)
    if settings.auth_enabled and (not user or user.role != "admin"):
        raise HTTPException(403, "Administrator access is required.")
    return user


def require_roles(*allowed_roles: str):
    def dependency(user: User | None = Depends(auth_guard)):
        if settings.auth_enabled and (not user or user.role not in allowed_roles):
            raise HTTPException(403, "Your workspace role does not allow this action.")
        return user
    return dependency
