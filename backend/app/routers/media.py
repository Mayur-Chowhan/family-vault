import asyncio

import cloudinary.uploader
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cloudinary_client import cloudinary_enabled, media_url
from app.config import settings
from app.database import get_db
from app.deps import require_membership
from app.models import Album, FamilyMember, Media
from app.schemas import MediaListResponse, MediaResponse

router = APIRouter(
    prefix="/api/v1/families/{family_id}/albums/{album_id}/media",
    tags=["media"],
)

ALLOWED_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/heic",
    "image/avif",
    "video/mp4",
    "video/quicktime",
    "video/webm",
}


async def get_album_or_404(
    album_id: int, family_id: int, db: AsyncSession
) -> Album:
    album = await db.get(Album, album_id)
    if album is None or album.family_id != family_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Album not found")
    return album


def to_response(media: Media) -> MediaResponse:
    thumb_transform = (
        "c_fill,w_400,h_300,q_auto,f_auto/" if media.resource_type == "image" else ""
    )
    fields = {
        c: getattr(media, c)
        for c in MediaResponse.model_fields
        if c not in {"url", "thumbnail_url", "download_url"}
    }
    return MediaResponse(
        **fields,
        url=media_url(media.cloudinary_public_id, media.resource_type),
        thumbnail_url=media_url(
            media.cloudinary_public_id, media.resource_type, thumb_transform
        ),
        download_url=media_url(
            media.cloudinary_public_id, media.resource_type, "fl_attachment/"
        ),
    )


@router.post("", response_model=MediaResponse, status_code=status.HTTP_201_CREATED)
async def upload_media(
    family_id: int,
    album_id: int,
    file: UploadFile = File(...),
    membership: FamilyMember = Depends(require_membership),
    db: AsyncSession = Depends(get_db),
):
    if not cloudinary_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Media storage is not configured",
        )
    await get_album_or_404(album_id, family_id, db)

    content_type = file.content_type or ""
    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {content_type}",
        )

    data = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.max_upload_mb}MB limit",
        )

    folder = f"family_{family_id}/album_{album_id}"
    result = await asyncio.to_thread(
        cloudinary.uploader.upload,
        data,
        folder=folder,
        resource_type="auto",
        use_filename=True,
        unique_filename=True,
    )

    media = Media(
        album_id=album_id,
        uploaded_by=membership.user_id,
        cloudinary_public_id=result["public_id"],
        resource_type=result.get("resource_type", "image"),
        format=result.get("format", ""),
        bytes=result.get("bytes", len(data)),
        width=result.get("width"),
        height=result.get("height"),
        duration=result.get("duration"),
        original_filename=file.filename or "unknown",
    )
    db.add(media)
    await db.commit()
    await db.refresh(media)
    return to_response(media)


@router.get("", response_model=MediaListResponse)
async def list_media(
    family_id: int,
    album_id: int,
    page: int = 1,
    page_size: int = 20,
    membership: FamilyMember = Depends(require_membership),
    db: AsyncSession = Depends(get_db),
):
    await get_album_or_404(album_id, family_id, db)
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)

    base = select(Media).where(Media.album_id == album_id)
    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()
    result = await db.execute(
        base.order_by(Media.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return MediaListResponse(
        items=[to_response(m) for m in result.scalars().all()],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete("/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_media(
    family_id: int,
    album_id: int,
    media_id: int,
    membership: FamilyMember = Depends(require_membership),
    db: AsyncSession = Depends(get_db),
):
    await get_album_or_404(album_id, family_id, db)
    media = await db.get(Media, media_id)
    if media is None or media.album_id != album_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found")

    if cloudinary_enabled():
        await asyncio.to_thread(
            cloudinary.uploader.destroy,
            media.cloudinary_public_id,
            resource_type=media.resource_type,
        )
    await db.delete(media)
    await db.commit()
