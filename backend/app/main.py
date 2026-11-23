from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.cloudinary_client import configure_cloudinary
from app.routers import albums, auth, families, invitations, media

app = FastAPI(title="Family Vault API", version="0.4.0")

configure_cloudinary()

app.include_router(auth.router)
app.include_router(families.router)
app.include_router(albums.router)
app.include_router(invitations.router)
app.include_router(media.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/db-check")
async def db_check() -> dict[str, str]:
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT version()"))
        version = result.scalar_one()
    return {"database": "connected", "version": version.split(",")[0]}
