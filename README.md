# recipe-aggregator

Pet project: a GraphQL API for aggregating recipes.

## Stack

Flask (app factory) · Strawberry GraphQL (code-first) · MongoDB + Beanie (PyMongo Async) · Docker · pytest

## Running

```bash
docker-compose up --build
```

GraphQL playground: http://localhost:5000/graphql

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
tests/
```
