from datetime import datetime

import strawberry
from beanie import Link, PydanticObjectId
from strawberry.types import Info

from app.models.comment import Comment
from app.models.user import User
from app.schema.types.user import UserType


@strawberry.type
class CommentType:
    id: strawberry.ID
    text: str
    created_at: datetime

    _author_id: strawberry.Private[PydanticObjectId]

    @strawberry.field
    async def author(self, info: Info) -> UserType | None:
        """Reuses the same per-request user_loader as RecipeType.author,
        so authors shared between a recipe and its comments are fetched once.
        """
        loader = info.context["user_loader"]
        user: User | None = await loader.load(self._author_id)
        return UserType.from_model(user) if user is not None else None

    @classmethod
    def from_model(cls, comment: Comment) -> "CommentType":
        author = comment.author
        author_id = author.ref.id if isinstance(author, Link) else author.id

        return cls(
            id=strawberry.ID(str(comment.id)),
            text=comment.text,
            created_at=comment.created_at,
            _author_id=author_id,
        )
