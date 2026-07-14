import asyncio

from flask import Flask
from strawberry.flask.views import AsyncGraphQLView

from app.db import init_db
from app.schema import schema


def create_app(init_database: bool = True) -> Flask:
    """App factory: the equivalent of what Django does for you via settings + wsgi.py.

    init_database=False lets tests build the app without a live Mongo —
    the same reason Django's test runner swaps DATABASES for you.
    """
    app = Flask(__name__)

    # Django runs migrations/connects lazily; here we register Beanie models
    # explicitly at startup. asyncio.run() is fine because create_app()
    # is called once, in sync context, before the server starts serving.
    if init_database:
        asyncio.run(init_db())

    app.add_url_rule(
        "/graphql",
        view_func=AsyncGraphQLView.as_view("graphql_view", schema=schema),
    )

    return app
