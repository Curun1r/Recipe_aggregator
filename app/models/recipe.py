from datetime import datetime

from beanie import Document
from pydantic import BaseModel, Field


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
    author_name: str
    tags: list[str] = []
    # default_factory, not default=datetime.utcnow() — otherwise the timestamp
    # would be fixed at import time (same pitfall as mutable defaults in Django).
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "recipes"
