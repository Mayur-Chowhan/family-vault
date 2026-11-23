from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.deps import require_membership
from app.models import Album, FamilyMember
from app.schemas import AlbumCreate, AlbumResponse, AlbumUpdate

router = APIRouter(prefix="/api/v1/families/{family_id}/albums", tags=["albums"])


async def get_album_or_404(album_id: int, family_id: int, db: AsyncSession) -> Album:
    album = await db.get(Album, album_id)
    if album is None or album.family_id != family_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album not found")
    return album


@router.post("", response_model=AlbumResponse, status_code=status.HTTP_201_CREATED)
async def create_album(
    family_id: int,
    payload: AlbumCreate,
    membership: FamilyMember = Depends(require_membership),
    db: AsyncSession = Depends(get_db),
):
    album = Album(family_id=family_id, **payload.model_dump())
    db.add(album)
    await db.commit()
    await db.refresh(album)
    return album


@router.get("", response_model=list[AlbumResponse])
async def list_albums(
    family_id: int,
    membership: FamilyMember = Depends(require_membership),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Album).where(Album.family_id == family_id).order_by(Album.id)
    )
    return result.scalars().all()


@router.get("/{album_id}", response_model=AlbumResponse)
async def get_album(
    album_id: int,
    family_id: int,
    membership: FamilyMember = Depends(require_membership),
    db: AsyncSession = Depends(get_db),
):
    return await get_album_or_404(album_id, family_id, db)


@router.patch("/{album_id}", response_model=AlbumResponse)
async def update_album(
    album_id: int,
    family_id: int,
    payload: AlbumUpdate,
    membership: FamilyMember = Depends(require_membership),
    db: AsyncSession = Depends(get_db),
):
    album = await get_album_or_404(album_id, family_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(album, field, value)
    await db.commit()
    await db.refresh(album)
    return album


@router.delete("/{album_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_album(
    album_id: int,
    family_id: int,
    membership: FamilyMember = Depends(require_membership),
    db: AsyncSession = Depends(get_db),
):
    album = await get_album_or_404(album_id, family_id, db)
    await db.delete(album)
    await db.commit()
