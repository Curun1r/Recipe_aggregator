from beanie import PydanticObjectId
from beanie.operators import In
from strawberry.dataloader import DataLoader

from app.models.comment import Comment
from app.models.user import User

UserLoader = DataLoader[PydanticObjectId, User | None]
CommentsByRecipeLoader = DataLoader[PydanticObjectId, list[Comment]]


async def load_users(keys: list[PydanticObjectId]) -> list[User | None]:
    """Batch function: one query for N ids, instead of N queries.

    The DataLoader contract requires the result list to line up with `keys`
    positionally — Mongo returns documents in arbitrary order, so we index
    them by id and rebuild the list. Missing ids must yield None, not be
    skipped, or every later key would shift by one.
    """
    users = await User.find(In(User.id, keys)).to_list()
    by_id: dict[PydanticObjectId, User] = {user.id: user for user in users}
    return [by_id.get(key) for key in keys]


async def load_comments_by_recipe(
    keys: list[PydanticObjectId],
) -> list[list[Comment]]:
    """One-to-many batch: one indexed query for N recipes.

    Unlike load_users this returns a list *per key*, so a recipe with no
    comments must map to [] — dropping it would shift every later key
    onto the wrong recipe's comments.
    """
    comments = await Comment.find(In(Comment.recipe_id, keys)).to_list()

    grouped: dict[PydanticObjectId, list[Comment]] = {key: [] for key in keys}
    for comment in comments:
        grouped[comment.recipe_id].append(comment)
    return [grouped[key] for key in keys]


def create_dataloaders() -> UserLoader:
    """A fresh loader per HTTP request.

    DataLoader caches by key for its whole lifetime, so a module-level
    instance would serve one request's stale user data to another —
    and never notice updates. Cheap to create; scope it to the request.
    """
    return DataLoader(load_fn=load_users)


def create_comments_loader() -> CommentsByRecipeLoader:
    """Same per-request rule as create_dataloaders()."""
    return DataLoader(load_fn=load_comments_by_recipe)
