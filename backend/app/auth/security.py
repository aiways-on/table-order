"""Security primitives: password hashing, JWT, session tokens.  [SEC-12][SEC-08]"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

_settings = get_settings()
_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=_settings.bcrypt_rounds)

_JWT_ALG = "HS256"
_JWT_ISS = "table-order"


# --- Passwords [SEC-12] --------------------------------------------------

def hash_password(password: str) -> str:
    return _pwd.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _pwd.verify(password, password_hash)
    except (ValueError, TypeError):
        return False


# --- JWT [SEC-08] --------------------------------------------------------

def create_admin_token(store_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": store_id,
        "role": "admin",
        "iss": _JWT_ISS,
        "iat": now,
        "exp": now + timedelta(hours=_settings.jwt_expire_hours),
    }
    return jwt.encode(payload, _settings.jwt_secret, algorithm=_JWT_ALG)


def decode_admin_token(token: str) -> dict[str, Any] | None:
    """Return claims if the token is valid (signature/exp/iss), else None."""
    try:
        return jwt.decode(
            token,
            _settings.jwt_secret,
            algorithms=[_JWT_ALG],
            issuer=_JWT_ISS,
            options={"require": ["exp", "iss", "sub"]},
        )
    except jwt.InvalidTokenError:
        return None


# --- Session tokens [SEC-12] --------------------------------------------

def generate_session_token() -> str:
    return secrets.token_urlsafe(32)
