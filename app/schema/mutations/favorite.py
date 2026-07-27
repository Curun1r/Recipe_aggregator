from typing import Annotated, Union

import strawberry
from beanie import PydanticObjectId
from beanie.operators import AddToSet, Pull
from bson.errors import InvalidId
from strawberry.types import Info

from app.models.recipe import Recipe
from app.models.user import User
from app.schema.permissions import IsAuthenticated
from app.schema.types.recipe import RecipeType


@strawberry.type
class FavoritePayload:
    is_favorited: bool
    recipe: RecipeType


@strawberry.type
class FavoriteError:
    message: str


FavoriteResult = Annotated[
    Union[FavoritePayload, FavoriteError], strawberry.union("FavoriteResult")
]


@strawberry.type
class FavoriteMutations:
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def toggle_favorite(
        self, recipe_id: strawberry.ID, info: Info
    ) -> FavoriteResult:
        try:
            oid = PydanticObjectId(recipe_id)
        # InvalidId is a BSONError, NOT a ValueError — catching only
        # ValueError lets a malformed id escape as a 500.
        except (InvalidId, ValueError, TypeError):
            return FavoriteError(message="Recipe not found")

        recipe = await Recipe.get(oid)
        if recipe is None:
            return FavoriteError(message="Recipe not found")

        current_user: User = info.context["current_user"]
        is_favorited = oid not in current_user.favorite_recipe_ids

        # $addToSet / $pull are atomic server-side operators: two concurrent
        # toggles can't clobber each other the way loading the list,
        # editing it in Python and saving the whole document would.
        # $addToSet is also idempotent — no duplicates even on a retry.
        operator = (
            AddToSet({User.favorite_recipe_ids: oid})
            if is_favorited
            else Pull({User.favorite_recipe_ids: oid})
        )
        await current_user.update(operator)

        return FavoritePayload(
            is_favorited=is_favorited, recipe=RecipeType.from_model(recipe)
        )
