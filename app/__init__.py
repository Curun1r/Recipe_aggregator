import asyncio
from typing import Any

from flask import Flask, Request, Response
from strawberry.flask.views import AsyncGraphQLView

from app.auth import get_current_user
from app.db import init_db
from app.schema import schema


class AuthGraphQLView(AsyncGraphQLView):
    """Puts the authenticated user into the GraphQL context —
    the hand-rolled equivalent of DRF's authentication middleware
    populating request.user. Resolvers read info.context["current_user"].
    """

    async def get_context(self, request: Request, response: Response) -> dict[str, Any]:
        return {
            "request": request,
            "response": response,
            "current_user": await get_current_user(request),
        }


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
        view_func=AuthGraphQLView.as_view("graphql_view", schema=schema),
    )

    return app
