# Day 1 — Foundations and environment (Week 1)

## Environment audit

| Tool           | Status                                   |
|----------------|------------------------------------------|
| Node.js        | v20.20.2                                 |
| npm            | 10.8.2                                   |
| Angular CLI    | 20.1.5                                   |
| Python         | 3.13.3                                   |
| pip            | 25.0                                     |
| Git            | 2.48.1                                   |
| Docker         | NOT installed (not needed for MVP local) |
| PostgreSQL     | 17.7, running on localhost:5432          |
| Disk space     | 343G free                                |

## What was set up

- Monorepo: `frontend/`, `backend/`, `docs/`, `infra/`, root `.gitignore`, `README.md`
- Backend: Python venv, FastAPI, SQLAlchemy 2.x (async), Alembic (async env),
  psycopg 3 driver, pydantic-settings, Pillow, pytest
- `app/main.py`: `/health` and `/db-check` endpoints, CORS configured for Angular dev server
- `app/config.py` + `app/database.py`: settings from `.env`, async engine, `Base` for models
- Alembic configured for async migrations using `DATABASE_URL` from settings
- Frontend: Angular 20 workspace with routing (Tailwind/Material to be added when needed)

## Database

- PostgreSQL 17.7 local, database `family_vault`, role `family_vault_user` (owner)
- `DATABASE_URL` configured in `backend/.env` (gitignored)
- Verified: `GET /db-check` returns PostgreSQL version through FastAPI
- Alembic ready for first migration once models exist (Week 2)
