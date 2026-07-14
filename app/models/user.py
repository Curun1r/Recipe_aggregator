from datetime import datetime, timezone
from typing import Annotated

from beanie import Document, Indexed
from pydantic import EmailStr, Field


class User(Document):
    """Like Django's AUTH_USER_MODEL, but nothing is built in —
    email uniqueness is a Mongo unique index (created by init_beanie),
    not an application-level check alone.
    """

    email: Annotated[EmailStr, Indexed(unique=True)]
    password_hash: str
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
