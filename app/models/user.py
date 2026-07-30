from datetime import UTC, datetime
from typing import Annotated

from beanie import Document, Indexed, PydanticObjectId
from pydantic import EmailStr, Field


class User(Document):
    """Like Django's AUTH_USER_MODEL, but nothing is built in —
    email uniqueness is a Mongo unique index (created by init_beanie),
    not an application-level check alone.
    """

    email: Annotated[EmailStr, Indexed(unique=True)]
    password_hash: str
    name: str
    # Favourites live on the user as an array of ids, not in a join
    # collection: the set is small, bounded and always read together with
    # the user. Mongo's $addToSet/$pull make toggling atomic — no
    # read-modify-write race, which a through-model would need a
    # transaction for.
    favorite_recipe_ids: list[PydanticObjectId] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "users"
