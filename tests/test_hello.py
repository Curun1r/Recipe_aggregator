from flask import Flask
from flask.testing import FlaskClient
import pytest

from app import create_app


@pytest.fixture
def client() -> FlaskClient:
    # Smoke test of the GraphQL view only — no live Mongo needed.
    app: Flask = create_app(init_database=False)
    return app.test_client()


def test_hello(client: FlaskClient) -> None:
    response = client.post("/graphql", json={"query": "{ hello }"})

    assert response.status_code == 200
    assert response.get_json() == {"data": {"hello": "world"}}
