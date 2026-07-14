from flask import Flask
from strawberry.flask.views import GraphQLView

from app.schema import schema


def create_app() -> Flask:
    """App factory: the equivalent of what Django does for you via settings + wsgi.py."""
    app = Flask(__name__)

    app.add_url_rule(
        "/graphql",
        view_func=GraphQLView.as_view("graphql_view", schema=schema),
    )

    return app
