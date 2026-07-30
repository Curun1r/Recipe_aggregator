from typing import Annotated

import pydantic
import strawberry
from pymongo.errors import DuplicateKeyError

from app.auth import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schema.types.user import UserType


@strawberry.type
class AuthPayload:
    token: str
    user: UserType


@strawberry.type
class AuthError:
    message: str


# Expected failures (duplicate email, bad credentials) are part of the schema,
# not exceptions: the client gets a typed result instead of a 500.
# The GraphQL analogue of DRF's serializer.errors -> 400 response.
AuthResult = Annotated[AuthPayload | AuthError, strawberry.union("AuthResult")]


def _payload(user: User) -> AuthPayload:
    return AuthPayload(
        token=create_access_token(str(user.id)),
        user=UserType.from_model(user),
    )


@strawberry.type
class AuthMutations:
    @strawberry.mutation
    async def register(self, email: str, password: str, name: str) -> AuthResult:
        if await User.find_one(User.email == email) is not None:
            return AuthError(message="Email is already registered")

        try:
            user = User(email=email, password_hash=hash_password(password), name=name)
        except pydantic.ValidationError:
            return AuthError(message="Invalid email address")

        try:
            await user.insert()
        except DuplicateKeyError:
            # Race-safe guard: the unique index catches what find_one missed.
            return AuthError(message="Email is already registered")

        return _payload(user)

    @strawberry.mutation
    async def login(self, email: str, password: str) -> AuthResult:
        user = await User.find_one(User.email == email)
        # One message for both cases — don't reveal which emails exist.
        if user is None or not verify_password(password, user.password_hash):
            return AuthError(message="Invalid email or password")
        return _payload(user)
