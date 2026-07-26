import strawberry

from app.models.user import User


@strawberry.type
class UserType:
    """GraphQL projection of User — password_hash is deliberately absent."""

    id: strawberry.ID
    email: str
    name: str

    @classmethod
    def from_model(cls, user: User) -> "UserType":
        return cls(id=strawberry.ID(str(user.id)), email=user.email, name=user.name)
