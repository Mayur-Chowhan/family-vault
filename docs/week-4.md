# Week 4 — Cloud media uploads (Cloudinary variant)

> Deviation from plan: instead of Cloudflare R2 + presigned URLs, this project
> uses **Cloudinary** for media storage. Rationale: simpler upload flow,
> automatic thumbnails/variants, no Pillow pipeline, free tier covers family use.
> The `media` table still stores object keys (`cloudinary_public_id`) so a
> storage swap later stays possible.

## Database (migration `a0114db8b845`)

`media` table: id, album_id (FK cascade), uploaded_by (FK users),
cloudinary_public_id (unique), resource_type (image/video/raw), format,
bytes, width, height, duration, original_filename, created_at.

## Backend

- `app/cloudinary_client.py` — SDK config from `CLOUDINARY_URL`
  (`cloudinary://KEY:SECRET@NAME`) or `CLOUDINARY_CLOUD_NAME`;
  `media_url()` builds delivery URLs with optional transforms
- `app/routers/media.py` — nested under albums:
  - `POST .../media` — multipart upload; validates MIME type
    (jpeg/png/webp/gif/heic/avif/mp4/mov/webm) and size (`MAX_UPLOAD_MB`,
    default 50); uploads via `cloudinary.uploader.upload` to folder
    `family_{fid}/album_{aid}`; stores metadata; returns `url` +
    `thumbnail_url` (400×300 `c_fill,q_auto,f_auto` for images)
  - `GET .../media` — list (newest first)
  - `DELETE .../media/{id}` — destroys Cloudinary asset + DB row
  - Requires family membership (reuses `require_membership`)
  - Returns **503** if Cloudinary isn't configured

### Upload flow (backend-mediated)

Angular → FastAPI (multipart) → Cloudinary → metadata in Postgres.
The plan's "browser uploads directly to storage" is relaxed for MVP
simplicity; a signed direct-to-Cloudinary upload session can be added later
without changing the schema.

## Frontend

- `home/` — family names now link to family detail
- `family-detail/` (`/families/:familyId`) — family name, album list,
  create-album form, visibility badges
- `album-detail/` (`/families/:familyId/albums/:albumId`) — media grid
  (lazy-loaded Cloudinary thumbnails), multi-file upload with progress %,
  per-item delete

## Setup

```bash
# backend/.env
CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME
MAX_UPLOAD_MB=50
```

## Tests — 42 passing

`test_media.py` mocks `cloudinary.uploader.upload/destroy` and
`cloudinary.config` — covers upload, MIME rejection (415), list, delete,
membership enforcement (403), and 503 when unconfigured.

## Notes / TODO later

- Direct browser→Cloudinary signed uploads (skip API proxying)
- EXIF/GPS stripping on shared derivatives
- Video thumbnails/transcoding settings in Cloudinary dashboard
- Upload queue with retry/cancel (Week 7)
