import strawberry
from strawberry.types import Info

from app.models.recipe import Ingredient, Recipe, Step
from app.models.user import User
from app.schema.permissions import IsAuthenticated
from app.schema.types.recipe import RecipeType


@strawberry.input
class IngredientInput:
    name: str
    amount: float
    unit: str


@strawberry.input
class StepInput:
    order: int
    text: str


@strawberry.input
class CreateRecipeInput:
    title: str
    description: str
    ingredients: list[IngredientInput]
    steps: list[StepInput]
    tags: list[str] = strawberry.field(default_factory=list)


@strawberry.type
class RecipeMutations:
    @strawberry.mutation(permission_classes=[IsAuthenticated])
    async def create_recipe(self, input: CreateRecipeInput, info: Info) -> RecipeType:
        # Author comes from the token, never from input — otherwise any
        # client could publish recipes as somebody else.
        current_user: User = info.context["current_user"]

        recipe = Recipe(
            title=input.title,
            description=input.description,
            ingredients=[
                Ingredient(name=i.name, amount=i.amount, unit=i.unit)
                for i in input.ingredients
            ],
            steps=[Step(order=s.order, text=s.text) for s in input.steps],
            tags=list(input.tags),
            author=current_user,
        )
        await recipe.insert()

        return RecipeType.from_model(recipe)
