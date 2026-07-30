"""Idempotent demo data for local development.

Run against a running Mongo:

    JWT_SECRET=dev-secret MONGO_URI=mongodb://localhost:27017/recipe_aggregator \\
    python -m scripts.seed_db
"""

import asyncio
from dataclasses import dataclass, field
from typing import TypedDict

from beanie.operators import AddToSet

from app.auth import hash_password
from app.db import init_db
from app.models.comment import Comment
from app.models.recipe import Ingredient, Recipe, Step
from app.models.user import User


class DemoUser(TypedDict):
    email: str
    name: str
    password: str


class DemoRecipe(TypedDict):
    title: str
    description: str
    author_email: str
    tags: list[str]
    ingredients: list[tuple[str, float, str]]
    steps: list[str]


class DemoComment(TypedDict):
    recipe_title: str
    author_email: str
    text: str


# Demo passwords are intentionally plain and public — this data is for a
# local playground only, never seed a deployed database with it.
DEMO_USERS: list[DemoUser] = [
    {"email": "ann@example.com", "name": "Ann Baker", "password": "demo-pass-ann"},
    {"email": "bob@example.com", "name": "Bob Cook", "password": "demo-pass-bob"},
    {"email": "cleo@example.com", "name": "Cleo Chef", "password": "demo-pass-cleo"},
]

DEMO_RECIPES: list[DemoRecipe] = [
    {
        "title": "Focaccia",
        "description": "Airy Italian flatbread with olive oil and rosemary.",
        "author_email": "ann@example.com",
        "tags": ["bread", "italian", "vegetarian"],
        "ingredients": [
            ("Bread flour", 500.0, "g"),
            ("Water", 400.0, "ml"),
            ("Olive oil", 60.0, "ml"),
            ("Salt", 10.0, "g"),
            ("Fresh yeast", 7.0, "g"),
        ],
        "steps": [
            "Dissolve the yeast in lukewarm water, add flour and salt.",
            "Knead briefly, then rest the dough for 2 hours.",
            "Spread into an oiled tray, dimple with your fingers.",
            "Bake at 230°C for 20 minutes until golden.",
        ],
    },
    {
        "title": "Borscht",
        "description": "Beetroot soup simmered with beef and served with sour cream.",
        "author_email": "ann@example.com",
        "tags": ["soup", "ukrainian"],
        "ingredients": [
            ("Beef brisket", 600.0, "g"),
            ("Beetroot", 400.0, "g"),
            ("Cabbage", 300.0, "g"),
            ("Potatoes", 400.0, "g"),
            ("Tomato paste", 40.0, "g"),
        ],
        "steps": [
            "Simmer the brisket for 90 minutes, skimming the broth.",
            "Sauté grated beetroot with tomato paste and a splash of vinegar.",
            "Add potatoes and cabbage to the broth, cook until tender.",
            "Stir in the beetroot, rest off the heat for 15 minutes.",
        ],
    },
    {
        "title": "Shakshuka",
        "description": "Eggs poached in a spiced tomato and pepper sauce.",
        "author_email": "bob@example.com",
        "tags": ["breakfast", "vegetarian", "quick"],
        "ingredients": [
            ("Eggs", 4.0, "pcs"),
            ("Canned tomatoes", 400.0, "g"),
            ("Red pepper", 1.0, "pcs"),
            ("Cumin", 5.0, "g"),
            ("Feta", 80.0, "g"),
        ],
        "steps": [
            "Soften the pepper with cumin in olive oil.",
            "Add tomatoes and reduce for 10 minutes.",
            "Make wells, crack in the eggs, cover and cook 6 minutes.",
            "Scatter feta and serve with bread.",
        ],
    },
    {
        "title": "Ramen broth",
        "description": "Slow pork and chicken broth, the base for a proper bowl.",
        "author_email": "bob@example.com",
        "tags": ["japanese", "soup", "slow"],
        "ingredients": [
            ("Pork bones", 1000.0, "g"),
            ("Chicken carcass", 500.0, "g"),
            ("Ginger", 30.0, "g"),
            ("Spring onion", 2.0, "pcs"),
            ("Kombu", 10.0, "g"),
        ],
        "steps": [
            "Blanch the bones for 10 minutes and rinse them clean.",
            "Simmer with ginger and spring onion for 6 hours.",
            "Add kombu for the last 20 minutes only.",
            "Strain through a fine sieve, season with tare.",
        ],
    },
    {
        "title": "Apple galette",
        "description": "Rustic free-form tart — no tin, no blind baking.",
        "author_email": "cleo@example.com",
        "tags": ["dessert", "baking"],
        "ingredients": [
            ("Plain flour", 250.0, "g"),
            ("Cold butter", 150.0, "g"),
            ("Apples", 500.0, "g"),
            ("Sugar", 80.0, "g"),
        ],
        "steps": [
            "Rub butter into flour, add ice water, chill for an hour.",
            "Roll out, pile sliced apples in the middle, fold the edges.",
            "Bake at 200°C for 35 minutes.",
        ],
    },
]

DEMO_COMMENTS: list[DemoComment] = [
    {
        "recipe_title": "Focaccia",
        "author_email": "bob@example.com",
        "text": "Left it to rise overnight instead — even better crumb.",
    },
    {
        "recipe_title": "Focaccia",
        "author_email": "cleo@example.com",
        "text": "Halved the salt and it was still plenty savoury.",
    },
    {
        "recipe_title": "Shakshuka",
        "author_email": "ann@example.com",
        "text": "Perfect weekend breakfast, took me 20 minutes.",
    },
    {
        "recipe_title": "Apple galette",
        "author_email": "bob@example.com",
        "text": "Used pears, worked just as well.",
    },
]

# (who favourites, which recipe) — deliberately somebody else's recipe.
DEMO_FAVORITES: list[tuple[str, str]] = [
    ("bob@example.com", "Focaccia"),
    ("ann@example.com", "Ramen broth"),
]


@dataclass
class SeedStats:
    """Created vs skipped, per collection — printed at the end."""

    created: dict[str, int] = field(
        default_factory=lambda: {
            "users": 0,
            "recipes": 0,
            "comments": 0,
            "favorites": 0,
        }
    )
    skipped: dict[str, int] = field(
        default_factory=lambda: {
            "users": 0,
            "recipes": 0,
            "comments": 0,
            "favorites": 0,
        }
    )

    def record(self, kind: str, *, was_created: bool) -> None:
        (self.created if was_created else self.skipped)[kind] += 1

    def render(self) -> str:
        lines = ["Seed summary:"]
        for kind in self.created:
            lines.append(
                f"  {kind:<10} created: {self.created[kind]:>2}"
                f"   skipped (already existed): {self.skipped[kind]:>2}"
            )
        return "\n".join(lines)


async def _seed_users(stats: SeedStats) -> dict[str, User]:
    users: dict[str, User] = {}

    for demo in DEMO_USERS:
        existing = await User.find_one(User.email == demo["email"])
        if existing is not None:
            users[demo["email"]] = existing
            stats.record("users", was_created=False)
            continue

        user = User(
            email=demo["email"],
            name=demo["name"],
            password_hash=hash_password(demo["password"]),
        )
        await user.insert()
        users[demo["email"]] = user
        stats.record("users", was_created=True)

    return users


async def _seed_recipes(users: dict[str, User], stats: SeedStats) -> dict[str, Recipe]:
    recipes: dict[str, Recipe] = {}

    for demo in DEMO_RECIPES:
        author = users[demo["author_email"]]
        # Title alone isn't unique enough — two users may post "Borscht".
        # Beanie translates author.id into the DBRef's author.$id.
        existing = await Recipe.find_one(
            Recipe.title == demo["title"], Recipe.author.id == author.id
        )
        if existing is not None:
            recipes[demo["title"]] = existing
            stats.record("recipes", was_created=False)
            continue

        recipe = Recipe(
            title=demo["title"],
            description=demo["description"],
            ingredients=[
                Ingredient(name=name, amount=amount, unit=unit)
                for name, amount, unit in demo["ingredients"]
            ],
            steps=[
                Step(order=order, text=text)
                for order, text in enumerate(demo["steps"], start=1)
            ],
            tags=list(demo["tags"]),
            author=author,
        )
        await recipe.insert()
        recipes[demo["title"]] = recipe
        stats.record("recipes", was_created=True)

    return recipes


async def _seed_comments(
    users: dict[str, User], recipes: dict[str, Recipe], stats: SeedStats
) -> None:
    for demo in DEMO_COMMENTS:
        recipe = recipes[demo["recipe_title"]]
        author = users[demo["author_email"]]

        existing = await Comment.find_one(
            Comment.recipe_id == recipe.id,
            Comment.author.id == author.id,
            Comment.text == demo["text"],
        )
        if existing is not None:
            stats.record("comments", was_created=False)
            continue

        await Comment(recipe_id=recipe.id, author=author, text=demo["text"]).insert()
        stats.record("comments", was_created=True)


async def _seed_favorites(
    users: dict[str, User], recipes: dict[str, Recipe], stats: SeedStats
) -> None:
    for user_email, recipe_title in DEMO_FAVORITES:
        user = users[user_email]
        recipe = recipes[recipe_title]

        if recipe.id in user.favorite_recipe_ids:
            stats.record("favorites", was_created=False)
            continue

        # $addToSet, same as the toggleFavorite mutation: idempotent even
        # if two seeds race each other.
        await user.update(AddToSet({User.favorite_recipe_ids: recipe.id}))
        stats.record("favorites", was_created=True)


async def seed(*, connect: bool = True) -> SeedStats:
    """Populate the database with demo content. Safe to run repeatedly.

    Demo accounts (password in brackets), for logging in via the API:
      ann@example.com  (demo-pass-ann)
      bob@example.com  (demo-pass-bob)
      cleo@example.com (demo-pass-cleo)

    connect=False assumes Beanie is already initialised — that is how the
    tests reuse this, mirroring create_app(init_database=False).
    """
    if connect:
        await init_db()

    stats = SeedStats()
    users = await _seed_users(stats)
    recipes = await _seed_recipes(users, stats)
    await _seed_comments(users, recipes, stats)
    await _seed_favorites(users, recipes, stats)

    print(stats.render())
    return stats


if __name__ == "__main__":
    asyncio.run(seed())
