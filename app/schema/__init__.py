import strawberry

from app.schema.mutations import (
    AuthMutations,
    CommentMutations,
    FavoriteMutations,
    RecipeMutations,
)
from app.schema.queries import RecipeQueries


@strawberry.type
class Query(RecipeQueries):
    @strawberry.field
    def hello(self) -> str:
        return "world"


@strawberry.type
class Mutation(AuthMutations, RecipeMutations, CommentMutations, FavoriteMutations):
    """Root mutation, composed from per-domain mutation classes."""


schema = strawberry.Schema(query=Query, mutation=Mutation)
