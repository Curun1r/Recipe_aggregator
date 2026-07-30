from datetime import UTC, datetime

from beanie import Document, Link
from pydantic import BaseModel, Field

from app.models.user import User


class Ingredient(BaseModel):
    """Embedded document: lives inside Recipe, not in its own collection.

    In Postgres this would be a separate table + FK; in MongoDB nesting
    is idiomatic when the child never exists without the parent.
    """

    name: str
    amount: float
    unit: str


class Step(BaseModel):
    """Embedded document, same reasoning as Ingredient."""

    order: int
    text: str


class Recipe(Document):
    """Beanie Document — an actual MongoDB collection, like a Django model."""

    title: str
    description: str
    ingredients: list[Ingredient]
    steps: list[Step]
    # Link stores a DBRef, not the embedded user — the closest thing Mongo
    # has to a FK. Unlike Django's ForeignKey it is NOT joined automatically:
    # either fetch_links=True, or (better for N+1) a DataLoader.
    author: Link[User]
    tags: list[str] = []
    # default_factory, not default=... — otherwise the timestamp would be
    # fixed at import time (same pitfall as mutable defaults in Django).
    # tz-aware: utcnow() is deprecated in 3.12 and returned naive datetimes.
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    class Settings:
        name = "recipes"
