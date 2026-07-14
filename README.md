# recipe-aggregator

Pet project: a GraphQL API for aggregating recipes.

## Stack

Flask (app factory) · Strawberry GraphQL (code-first) · MongoDB + Beanie/Motor · Docker · pytest

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

```bash
pip install -r requirements.txt
pytest
```

## Structure

```
app/
  __init__.py   # create_app() factory
  schema/       # Strawberry schema
  db.py         # Motor client + init_beanie
tests/
```
