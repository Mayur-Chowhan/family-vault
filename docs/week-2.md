# Week 2 — FastAPI and database fundamentals

## What was built

### Models (`app/models.py`)
- `Family` — id, name, created_at, updated_at; has many `albums` (cascade delete)
- `Album` — id, family_id (FK → families, CASCADE), name, visibility
  (`private`/`family`/`public`), timestamps

### Schemas (`app/schemas.py`)
- Pydantic `Create`/`Update`/`Response` models per entity
- `from_attributes=True` for ORM → response conversion
- Field validation: name length, visibility pattern

### Routers (`app/routers/`)
- `families.py` — `POST/GET/PATCH/DELETE /api/v1/families[/{id}]`
- `albums.py` — nested under families:
  `/api/v1/families/{family_id}/albums[/{album_id}]`
- Albums verify the parent family exists; album lookups are scoped to the family

### Migration
- Alembic (async env) autogenerates from `Base.metadata`
- First revision: `e3cc50263eec_create_families_and_albums_tables.py`
- Applied to `family_vault` — `families` and `albums` tables exist

### Tests (`tests/`, 17 passing)
- pytest + pytest-asyncio + httpx `ASGITransport`
- SQLite in-memory DB via `aiosqlite`, `get_db` overridden in `conftest.py`
- Covers: health, family CRUD + 404 + validation, album CRUD, visibility
  validation, wrong-family 404, cascade delete

## Commands

```bash
cd backend
source .venv/bin/activate

alembic revision --autogenerate -m "message"   # after model changes
alembic upgrade head                            # apply migrations
alembic current                                 # show applied revision

pytest -q                # run tests
uvicorn app.main:app --reload --port 8000
```

## Gotchas learned

- Alembic `env.py` with async engines: `run_sync` needs a **sync** function;
  wrap connect in `asyncio.run`.
- If `do_run_migrations` is `async def`, `run_sync` silently never awaits it —
  `revision --autogenerate` then produces an **empty** migration. Fix the
  function, delete the empty revision, `DELETE FROM alembic_version`, regenerate.
- `configparser` interpolation rejects `%` in URLs — escape `%` → `%%`
  when calling `set_main_option` (password `Mayur@123` → `Mayur%40123`).
- PostgreSQL 15+: `family_vault_user` needs schema `public` CREATE privilege —
  fixed by `ALTER DATABASE family_vault OWNER TO family_vault_user;`
  (run as postgres superuser).
