# Course-platform

Submission for altschool enrollment capstone.

## setup (local)

```bash
python -m venv venv
venv\Scripts\activate      # windows
pip install -e ".[dev]"
```

## run migrations

```bash
alembic upgrade head
```

## run it

```bash
uvicorn app.main:app --reload
```

goes up on `http://localhost:8000`. docs at `/docs`.

## run tests

```bash
pytest tests/ -v
```

tests use in-memory sqlite so you dont need postgres running.

## docker

```bash
docker compose up --build
```

that spins up postgres + the api. hits `http://localhost:8000`.

make sure the `.env` file is there (theres one already).

## whats in it

- jwt auth (register / login)
- role based access (student vs admin)
- course crud (admin only for writes)
- enrollment with capacity checks, dupe prevention, inactive course blocking
- soft deletes on courses and users
- audit logs on every enrollment action
- pagination + title filtering on course list
- rate limiting on auth endpoints

## project structure

```
app/
  config.py
  main.py
  db/          - engine, session, base
  models/      - sqlalchemy models
  schemas/     - pydantic request/response models
  services/    - business  logic
  routers/     - api endpoints
  utils/       - jwt, hashing, dependencies, rate limiter
migrations/    - alembic
tests/         - pytest
```
