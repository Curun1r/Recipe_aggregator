import os
from collections.abc import AsyncIterator
from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.models.recipe import Ingredient, Recipe, Step
from app.models.user import User

TEST_DB_NAME = "recipe_aggregator_test"


@pytest_asyncio.fixture
async def test_db() -> AsyncIterator[None]:
    """Real Mongo connection, but always a separate test database —
    the same idea as Django's test runner creating test_<name>,
    only here we do it by hand.

    Requires a running Mongo: docker compose up -d mongo
    """
    uri: str = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    client: AsyncMongoClient = AsyncMongoClient(uri, tz_aware=True)

    # Force the test DB name regardless of what URI points to,
    # so tests can never touch the real database.
    await init_beanie(database=client[TEST_DB_NAME], document_models=[Recipe, User])

    yield

    await client.drop_database(TEST_DB_NAME)
    await client.close()


@pytest.mark.asyncio
async def test_recipe_insert_and_get(test_db: None) -> None:
    ingredient = Ingredient(name="Flour", amount=200.0, unit="g")
    step = Step(order=1, text="Mix the flour with water.")

    author = User(email="yehor@example.com", password_hash="x", name="Yehor")
    await author.insert()

    recipe = Recipe(
        title="Simple Bread",
        description="A minimal bread recipe.",
        ingredients=[ingredient],
        steps=[step],
        author=author,
    )
    await recipe.insert()

    # fetch_links=True resolves the DBRef — the explicit opt-in Django's
    # select_related makes optional but its ORM would do lazily anyway.
    fetched: Recipe | None = await Recipe.get(recipe.id, fetch_links=True)

    assert fetched is not None
    assert fetched.title == "Simple Bread"
    assert fetched.description == "A minimal bread recipe."
    assert fetched.ingredients == [ingredient]
    assert fetched.ingredients[0].amount == 200.0
    assert fetched.steps[0].order == 1
    assert fetched.steps[0].text == "Mix the flour with water."
    assert isinstance(fetched.author, User)
    assert fetched.author.id == author.id
    assert fetched.author.email == "yehor@example.com"
    assert fetched.tags == []
    assert isinstance(fetched.created_at, datetime)
    # Round-trip stays tz-aware — only true because the client is tz_aware=True.
    assert fetched.created_at.tzinfo is not None
    assert fetched.created_at.utcoffset() == timedelta(0)
