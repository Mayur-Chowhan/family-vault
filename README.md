# Family Vault

Secure family photo and media storage platform. See `Family_Vault_Project_Plan.pdf` for the full roadmap.

## Repository structure

```
family-vault/
├── frontend/   # Angular application (Angular CLI 20, TypeScript)
├── backend/    # FastAPI application (Python 3.13, SQLAlchemy async, Alembic, PostgreSQL)
├── docs/       # Architecture, API and setup notes
├── infra/      # Deployment and infrastructure configuration
└── .gitignore
```

## Prerequisites

- Node.js 20+ and npm
- Python 3.13+
- PostgreSQL (local or hosted)
- Angular CLI (`npm install -g @angular/cli`)

## Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit DATABASE_URL
```

Create the database (once you have Postgres credentials):

```bash
createdb family_vault   # or: CREATE DATABASE family_vault;
```

Run the API:

```bash
uvicorn app.main:app --reload --port 8000
```

Endpoints (all `/api/v1`, auth required unless noted):

- `POST /auth/register`, `POST /auth/login`, `GET /auth/me`
- `/families` — family CRUD (creator = owner; update/delete = owner/admin)
- `/families/{id}/members` — list/remove members
- `/families/{id}/invitations` — create/list invites (owner/admin)
- `/invitations/mine`, `/invitations/{token}/accept`
- `/families/{id}/albums` — album CRUD (family members)
- `/families/{id}/albums/{id}/media` — upload/list/delete media (Cloudinary)

Tests:

```bash
pip install -r requirements-dev.txt
pytest -q
```

Migrations (Alembic, async):

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

## Frontend setup

```bash
cd frontend
npm install
ng serve   # http://localhost:4200
```

## Environment variables

Backend `.env`:

| Variable        | Default                                              | Purpose                    |
|-----------------|------------------------------------------------------|----------------------------|
| `DATABASE_URL`  | `postgresql+psycopg://localhost:5432/family_vault`   | Async SQLAlchemy URL       |
| `CORS_ORIGINS`  | `http://localhost:4200`                              | Allowed frontend origins   |
| `SECRET_KEY`    | dev default (change for production)                  | JWT signing key            |
| `CLOUDINARY_URL`| empty                                                | `cloudinary://KEY:SECRET@NAME` for media uploads |
