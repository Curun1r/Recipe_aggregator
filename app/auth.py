import os
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from beanie import PydanticObjectId
from bson.errors import InvalidId
from flask import Request

from app.models.user import User

_ALGORITHM = "HS256"
_TOKEN_TTL = timedelta(hours=24)


def hash_password(password: str) -> str:
    # bcrypt directly (passlib is unmaintained and broken with bcrypt >= 5).
    # gensalt() embeds the salt into the hash — unlike Django's
    # PASSWORD_HASHERS there is no framework layer here.
    # bcrypt only reads the first 72 bytes; 5.x raises instead of truncating.
    return bcrypt.hashpw(password.encode()[:72], bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode()[:72], password_hash.encode())


def create_access_token(user_id: str) -> str:
    payload: dict[str, object] = {
        "sub": user_id,
        "exp": datetime.now(UTC) + _TOKEN_TTL,
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
    except (InvalidId, ValueError, TypeError):
        return None
    return await User.get(oid)
