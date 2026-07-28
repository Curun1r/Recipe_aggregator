from flask import render_template

from app.models.recipe import Recipe


async def index() -> str:
    """Read-only demo page.

    No DataLoader and no GraphQL layer here on purpose: this page always
    needs every author, so fetch_links=True ($lookup) resolves them in one
    round trip. DataLoaders exist to batch what GraphQL asks for *lazily* —
    pulling them in here would be cargo-culting.
    """
    recipes: list[Recipe] = await Recipe.find_all(fetch_links=True).to_list()
    return render_template("index.html", recipes=recipes)
