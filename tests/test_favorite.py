import os
from typing import Any, AsyncIterator

import pytest
import pytest_asyncio
from beanie import PydanticObjectId, init_beanie
from pymongo import AsyncMongoClient

from app.models.comment import Comment
from app.models.recipe import Ingredient, Recipe, Step
from app.models.user import User
from app.schema import schema
from app.schema.dataloaders import create_comments_loader, create_dataloaders

os.environ.setdefault("JWT_SECRET", "test-secret")

TEST_DB_NAME = "recipe_aggregator_test"

TOGGLE_FAVORITE = """
mutation ToggleFavorite($recipeId: ID!) {
  toggleFavorite(recipeId: $recipeId) {
    __typename
    ... on FavoritePayload { isFavorited recipe { id title } }
    ... on FavoriteError { message }
  }
}
"""

MY_FAVORITES = """
query { myFavorites { id title } }
"""

ME = """
query { me { id email name } }
"""


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


def _context(current_user: User | None = None) -> dict[str, Any]:
    return {
        "current_user": current_user,
        "user_loader": create_dataloaders(),
        "comments_loader": create_comments_loader(),
    }


async def _make_user(email: str = "yehor@example.com", name: str = "Yehor") -> User:
    user = User(email=email, password_hash="x", name=name)
    await user.insert()
    return user


async def _make_recipe(author: User, title: str = "Simple Bread") -> Recipe:
    recipe = Recipe(
        title=title,
        description="A minimal bread recipe.",
        ingredients=[Ingredient(name="Flour", amount=200.0, unit="g")],
        steps=[Step(order=1, text="Mix.")],
        tags=[],
        author=author,
    )
    await recipe.insert()
    return recipe


@pytest.mark.asyncio
async def test_toggle_favorite_adds_then_removes(test_db: None) -> None:
    user = await _make_user()
    recipe = await _make_recipe(user)

    first = await schema.execute(
        TOGGLE_FAVORITE,
        variable_values={"recipeId": str(recipe.id)},
        context_value=_context(current_user=user),
    )
    assert first.errors is None
    assert first.data is not None
    assert first.data["toggleFavorite"]["__typename"] == "FavoritePayload"
    assert first.data["toggleFavorite"]["isFavorited"] is True
    assert first.data["toggleFavorite"]["recipe"]["id"] == str(recipe.id)

    # Re-read from Mongo: the change must be persisted, not just local.
    stored = await User.get(user.id)
    assert stored is not None
    assert stored.favorite_recipe_ids == [recipe.id]

    second = await schema.execute(
        TOGGLE_FAVORITE,
        variable_values={"recipeId": str(recipe.id)},
        context_value=_context(current_user=user),
    )
    assert second.errors is None
    assert second.data is not None
    assert second.data["toggleFavorite"]["isFavorited"] is False

    stored_again = await User.get(user.id)
    assert stored_again is not None
    assert stored_again.favorite_recipe_ids == []


@pytest.mark.asyncio
async def test_toggle_favorite_missing_recipe_is_modeled_error(test_db: None) -> None:
    user = await _make_user()

    result = await schema.execute(
        TOGGLE_FAVORITE,
        variable_values={"recipeId": str(PydanticObjectId())},
        context_value=_context(current_user=user),
    )

    assert result.errors is None
    assert result.data is not None
    assert result.data["toggleFavorite"]["__typename"] == "FavoriteError"
    assert result.data["toggleFavorite"]["message"] == "Recipe not found"


@pytest.mark.asyncio
async def test_toggle_favorite_malformed_id_is_modeled_error(test_db: None) -> None:
    """Regression: bson raises InvalidId (a BSONError, not a ValueError),
    so a malformed id used to escape the except clause as a 500."""
    user = await _make_user()

    result = await schema.execute(
        TOGGLE_FAVORITE,
        variable_values={"recipeId": "not-an-objectid"},
        context_value=_context(current_user=user),
    )

    assert result.errors is None
    assert result.data is not None
    assert result.data["toggleFavorite"]["__typename"] == "FavoriteError"


@pytest.mark.asyncio
async def test_toggle_favorite_without_token_is_permission_error(
    test_db: None,
) -> None:
    author = await _make_user()
    recipe = await _make_recipe(author)

    result = await schema.execute(
        TOGGLE_FAVORITE,
        variable_values={"recipeId": str(recipe.id)},
        context_value=_context(current_user=None),
    )

    assert result.errors is not None
    assert "Authentication required" in str(result.errors[0].message)


@pytest.mark.asyncio
async def test_my_favorites_are_isolated_per_user(test_db: None) -> None:
    ann = await _make_user(email="ann@example.com", name="Ann")
    bob = await _make_user(email="bob@example.com", name="Bob")

    bread = await _make_recipe(ann, title="Bread")
    soup = await _make_recipe(bob, title="Soup")
    await _make_recipe(ann, title="Salad")  # nobody's favourite

    for user, recipe in ((ann, bread), (bob, soup)):
        await schema.execute(
            TOGGLE_FAVORITE,
            variable_values={"recipeId": str(recipe.id)},
            context_value=_context(current_user=user),
        )

    ann_result = await schema.execute(MY_FAVORITES, context_value=_context(ann))
    bob_result = await schema.execute(MY_FAVORITES, context_value=_context(bob))

    assert ann_result.errors is None and bob_result.errors is None
    assert ann_result.data is not None and bob_result.data is not None
    # No leaking between users.
    assert [r["title"] for r in ann_result.data["myFavorites"]] == ["Bread"]
    assert [r["title"] for r in bob_result.data["myFavorites"]] == ["Soup"]


@pytest.mark.asyncio
async def test_me_returns_null_for_guest_and_user_when_authenticated(
    test_db: None,
) -> None:
    guest = await schema.execute(ME, context_value=_context(current_user=None))
    assert guest.errors is None
    assert guest.data == {"me": None}  # null, not an error

    user = await _make_user()
    authed = await schema.execute(ME, context_value=_context(current_user=user))
    assert authed.errors is None
    assert authed.data is not None
    assert authed.data["me"] == {
        "id": str(user.id),
        "email": "yehor@example.com",
        "name": "Yehor",
    }
