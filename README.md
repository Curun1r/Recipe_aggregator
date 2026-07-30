# recipe-aggregator

Pet project: a GraphQL API for aggregating recipes.

## Stack

Flask (app factory) · Strawberry GraphQL (code-first) · MongoDB + Beanie (PyMongo Async) · Docker · pytest

## Running

```bash
docker compose up --build
```

Recipes page: http://localhost:8000/ · GraphQL playground: http://localhost:8000/graphql

Port 8000, not 5000 — on macOS the AirPlay Receiver occupies 5000 and
answers every request with 403.

Locally, without Docker — **use hypercorn, not `flask run`**:

```bash
docker compose up -d mongo
JWT_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))") \
MONGO_URI=mongodb://localhost:27017/recipe_aggregator \
hypercorn app.wsgi:asgi_app --bind 0.0.0.0:8000
```

`flask run` serves WSGI, which hands every request a fresh event loop;
`AsyncMongoClient` is bound to the loop it was created on and raises
`Cannot use AsyncMongoClient in different event loop` on the second request.
Serving the app as ASGI (`app/wsgi.py`) keeps everything on one loop.

Smoke query:

```graphql
{ hello }
```

## Tests

Model tests need a live Mongo (a separate `recipe_aggregator_test` database
is created and dropped automatically):

```bash
docker compose up -d mongo
pip install -r requirements.txt
MONGO_URI=mongodb://localhost:27017/recipe_aggregator_test pytest
```

## Structure

```
app/
  __init__.py   # create_app() factory
  schema/       # Strawberry schema
  db.py         # PyMongo Async client + init_beanie
  wsgi.py       # ASGI entrypoint (WsgiToAsgi) — see "Running"
tests/
```
