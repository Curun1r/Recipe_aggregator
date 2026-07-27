import strawberry
from beanie import PydanticObjectId
from bson.errors import InvalidId

from app.models.recipe import Recipe
from app.schema.types.recipe import RecipeType


@strawberry.type
class RecipeQueries:
    @strawberry.field
    async def recipes(self) -> list[RecipeType]:
        # No fetch_links: authors are resolved lazily and batched by the
        # DataLoader, only if the query actually asks for them.
        documents = await Recipe.find_all().to_list()
        return [RecipeType.from_model(doc) for doc in documents]

    @strawberry.field
    async def recipe(self, id: strawberry.ID) -> RecipeType | None:
        try:
            oid = PydanticObjectId(id)
        except (InvalidId, ValueError, TypeError):
            # Malformed id is "not found", not a server error.
            return None

        document = await Recipe.get(oid)
        return RecipeType.from_model(document) if document is not None else None
