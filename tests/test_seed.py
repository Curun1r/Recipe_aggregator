import os
from typing import AsyncIterator

import pytest
import pytest_asyncio
from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.models.comment import Comment
from app.models.recipe import Recipe
from app.models.user import User
from scripts.seed_db import (
    DEMO_COMMENTS,
    DEMO_FAVORITES,
    DEMO_RECIPES,
    DEMO_USERS,
    seed,
)

os.environ.setdefault("JWT_SECRET", "test-secret")

TEST_DB_NAME = "recipe_aggregator_test"


@pytest_asyncio.fixture
async def test_db() -> AsyncIterator[None]:
    uri: str = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
    client: AsyncMongoClient = AsyncMongoClient(uri, tz_aware=True)
    await init_beanie(
        database=client[TEST_DB_NAME], document_models=[Recipe, User, Comment]
    )
    yield
    await client.drop_database(TEST_DB_NAME)
    await client.close()


async def _counts() -> tuple[int, int, int]:
    return (
        await User.find_all().count(),
        await Recipe.find_all().count(),
        await Comment.find_all().count(),
    )


@pytest.mark.asyncio
async def test_seed_creates_demo_content(test_db: None) -> None:
    # connect=False: the fixture already initialised Beanie on this loop.
    stats = await seed(connect=False)

    assert await _counts() == (
        len(DEMO_USERS),
        len(DEMO_RECIPES),
        len(DEMO_COMMENTS),
    )
    assert stats.created["users"] == len(DEMO_USERS)
    assert stats.created["recipes"] == len(DEMO_RECIPES)
    assert stats.created["comments"] == len(DEMO_COMMENTS)
    assert stats.created["favorites"] == len(DEMO_FAVORITES)

    # Spot-check the links actually resolve, not just that rows exist.
    focaccia = await Recipe.find_one(Recipe.title == "Focaccia", fetch_links=True)
    assert focaccia is not None
    assert focaccia.author.email == "ann@example.com"
    assert len(focaccia.ingredients) == 5
    assert [step.order for step in focaccia.steps] == [1, 2, 3, 4]

    bob = await User.find_one(User.email == "bob@example.com")
    assert bob is not None
    assert focaccia.id in bob.favorite_recipe_ids


@pytest.mark.asyncio
async def test_seed_is_idempotent(test_db: None) -> None:
    await seed(connect=False)
    counts_after_first = await _counts()

    second = await seed(connect=False)
    counts_after_second = await _counts()

    # Nothing duplicated on a re-run.
    assert counts_after_second == counts_after_first
    assert second.created == {
        "users": 0,
        "recipes": 0,
        "comments": 0,
        "favorites": 0,
    }
    assert second.skipped["users"] == len(DEMO_USERS)
    assert second.skipped["recipes"] == len(DEMO_RECIPES)
    assert second.skipped["comments"] == len(DEMO_COMMENTS)
    assert second.skipped["favorites"] == len(DEMO_FAVORITES)

    # Favourites are a set, not an append-only list.
    bob = await User.find_one(User.email == "bob@example.com")
    assert bob is not None
    assert len(bob.favorite_recipe_ids) == len(set(bob.favorite_recipe_ids))
