import os

from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.models.recipe import Recipe
from app.models.user import User


async def init_db(mongo_uri: str | None = None) -> None:
    """Initialize the MongoDB connection.

    Roughly Django's DATABASES setting and migrations combined:
    Beanie has no migrations — init_beanie registers document models
    and creates indexes at startup.
    """
    uri: str = mongo_uri or os.environ["MONGO_URI"]
    client: AsyncMongoClient = AsyncMongoClient(uri)

    await init_beanie(
        database=client.get_default_database(),
        document_models=[Recipe, User],
    )
