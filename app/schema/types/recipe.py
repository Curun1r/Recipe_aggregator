from datetime import datetime

import strawberry
from beanie import Link, PydanticObjectId
from strawberry.types import Info

from app.models.recipe import Ingredient, Recipe, Step
from app.models.user import User
from app.schema.types.user import UserType


@strawberry.type
class IngredientType:
    name: str
    amount: float
    unit: str

    @classmethod
    def from_model(cls, ingredient: Ingredient) -> "IngredientType":
        return cls(
            name=ingredient.name, amount=ingredient.amount, unit=ingredient.unit
        )


@strawberry.type
class StepType:
    order: int
    text: str

    @classmethod
    def from_model(cls, step: Step) -> "StepType":
        return cls(order=step.order, text=step.text)


@strawberry.type
class RecipeType:
    id: strawberry.ID
    title: str
    description: str
    ingredients: list[IngredientType]
    steps: list[StepType]
    tags: list[str]
    created_at: datetime

    # Private: carried through for the author resolver, never exposed in SDL.
    _author_id: strawberry.Private[PydanticObjectId]

    @strawberry.field
    async def author(self, info: Info) -> UserType | None:
        """Resolved through the DataLoader, so a list of N recipes costs
        one users query instead of N (the GraphQL N+1 problem — the same
        thing select_related solves in Django, but per-field and batched).
        """
        loader = info.context["user_loader"]
        user: User | None = await loader.load(self._author_id)
        return UserType.from_model(user) if user is not None else None

    @classmethod
    def from_model(cls, recipe: Recipe) -> "RecipeType":
        author = recipe.author
        # Link when unfetched, User when fetch_links=True was used —
        # we only need the id either way.
        author_id = author.ref.id if isinstance(author, Link) else author.id

        return cls(
            id=strawberry.ID(str(recipe.id)),
            title=recipe.title,
            description=recipe.description,
            ingredients=[IngredientType.from_model(i) for i in recipe.ingredients],
            steps=[StepType.from_model(s) for s in recipe.steps],
            tags=list(recipe.tags),
            created_at=recipe.created_at,
            _author_id=author_id,
        )
