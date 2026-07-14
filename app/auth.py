import os
from datetime import datetime, timedelta, timezone

import jwt
from beanie import PydanticObjectId
from flask import Request
from passlib.context import CryptContext

from app.models.user import User

# bcrypt handles salting internally — unlike Django's PASSWORD_HASHERS
# there is no framework layer, we call the hasher directly.
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

_ALGORITHM = "HS256"
_TOKEN_TTL = timedelta(hours=24)


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)


def create_access_token(user_id: str) -> str:
    payload: dict[str, object] = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + _TOKEN_TTL,
    }
    # Secret is read at call time (not import time) so tests can set it
    # via env without import-order issues.
    return jwt.encode(payload, os.environ["JWT_SECRET"], algorithm=_ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Returns user_id or None for anything invalid/expired —
    auth failures are a normal outcome, not an exception."""
    try:
        payload = jwt.decode(token, os.environ["JWT_SECRET"], algorithms=[_ALGORITHM])
    except jwt.InvalidTokenError:
        return None
    sub = payload.get("sub")
    return sub if isinstance(sub, str) else None


async def get_current_user(request: Request) -> User | None:
    """The DRF `request.user` equivalent, done by hand:
    Bearer token -> user_id -> User document (or None, never an error).
    """
    header: str = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None

    user_id = decode_access_token(header.removeprefix("Bearer "))
    if user_id is None:
        return None

    try:
        oid = PydanticObjectId(user_id)
    except (ValueError, TypeError):
        return None
    return await User.get(oid)
