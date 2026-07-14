import strawberry

from app.schema.mutations import AuthMutations


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "world"


@strawberry.type
class Mutation(AuthMutations):
    """Root mutation, composed from per-domain mutation classes."""


schema = strawberry.Schema(query=Query, mutation=Mutation)
