# Campus Navigation Backend

FastAPI backend for indoor navigation in a university building.

## Stack

- FastAPI
- PostgreSQL + PostGIS + pgRouting
- SQLAlchemy 2.0
- Alembic
- Poetry
- Docker Compose

## Setup

1. Copy env file:
   - `cp .env.example .env`
2. Install dependencies:
   - `poetry install`

## Run Locally

- Start database:
  - `docker compose up -d`
- Apply migrations:
  - `poetry run alembic upgrade head`
- Start API:
  - `poetry run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`
- Open docs:
  - `http://localhost:8000/docs`

## Run With Docker

1. Copy env file:
   - `cp .env.example .env`
2. Start database only:
   - `docker compose up --build`
3. Start database and API:
   - `docker compose --profile app up --build`

## Database Migrations

- Apply migrations:
  - `poetry run alembic upgrade head`

## Code Quality

- Run mypy:
  - `poetry run mypy app`
- Check formatting with black:
  - `poetry run black --check app`
- Format code with black:
  - `poetry run black app`

## Main endpoint

- `POST /api/v1/navigation/route`
