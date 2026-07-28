import asyncio
from typing import Any

from flask import Flask, Request, Response
from strawberry.flask.views import AsyncGraphQLView

from app.auth import get_current_user
from app.db import init_db
from app.schema import schema
from app.schema.dataloaders import create_comments_loader, create_dataloaders


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
            # Per-request loader: caching across requests would leak
            # one user's data into another's response.
            "user_loader": create_dataloaders(),
            "comments_loader": create_comments_loader(),
        }


def create_app(init_database: bool = True) -> Flask:
    """App factory: the equivalent of what Django does for you via settings + wsgi.py.

    init_database=False lets tests build the app without a live Mongo —
    the same reason Django's test runner swaps DATABASES for you.
    """
    app = Flask(__name__)

    if init_database:
        # NOT asyncio.run(init_db()) here: that binds AsyncMongoClient to a
        # temporary loop which is closed straight after, and every later
        # request then fails with "Cannot use AsyncMongoClient in different
        # event loop". Initialising on first request means the client is
        # created on the server's loop — the same one the views run on.
        db_ready = False
        db_lock: asyncio.Lock | None = None

        @app.before_request
        async def _init_db_once() -> None:
            nonlocal db_ready, db_lock
            if db_ready:
                return
            if db_lock is None:
                # Safe without a lock of its own: no await above it,
                # so this branch can't interleave.
                db_lock = asyncio.Lock()
            async with db_lock:
                if not db_ready:
                    await init_db()
                    db_ready = True

    app.add_url_rule(
        "/graphql",
        view_func=AuthGraphQLView.as_view("graphql_view", schema=schema),
    )

    return app
