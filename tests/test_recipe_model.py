import os
from datetime import datetime
from typing import AsyncIterator

import pytest
import pytest_asyncio
from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.models.recipe import Ingredient, Recipe, Step

TEST_DB_NAME = "recipe_aggregator_test"


@pytest_asyncio.fixture
async def test_db() -> AsyncIterator[None]:
    """Real Mongo connection, but always a separate test database —
    the same idea as Django's test runner creating test_<name>,
    only here we do it by hand.

    Requires a running Mongo: docker compose up -d mongo
    """
    uri: str = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    client: AsyncMongoClient = AsyncMongoClient(uri)

    # Force the test DB name regardless of what URI points to,
    # so tests can never touch the real database.
    await init_beanie(database=client[TEST_DB_NAME], document_models=[Recipe])

    yield

    await client.drop_database(TEST_DB_NAME)
    await client.close()


@pytest.mark.asyncio
async def test_recipe_insert_and_get(test_db: None) -> None:
    ingredient = Ingredient(name="Flour", amount=200.0, unit="g")
    step = Step(order=1, text="Mix the flour with water.")

    recipe = Recipe(
        title="Simple Bread",
        description="A minimal bread recipe.",
        ingredients=[ingredient],
        steps=[step],
        author_name="Yehor",
    )
    await recipe.insert()

    fetched: Recipe | None = await Recipe.get(recipe.id)

    assert fetched is not None
    assert fetched.title == "Simple Bread"
    assert fetched.description == "A minimal bread recipe."
    assert fetched.ingredients == [ingredient]
    assert fetched.ingredients[0].amount == 200.0
    assert fetched.steps[0].order == 1
    assert fetched.steps[0].text == "Mix the flour with water."
    assert fetched.author_name == "Yehor"
    assert fetched.tags == []
    assert isinstance(fetched.created_at, datetime)
