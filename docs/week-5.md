# Week 5 — Albums and gallery

## Status: complete

| Task | Implementation |
|------|----------------|
| Album creation & listing | `family-detail/` page — create form + list with visibility badges |
| Responsive media grid | CSS grid `auto-fill minmax(180px,1fr)` in `album-detail/` |
| Image preview / lightbox | Click thumbnail → overlay with full-res `url`, video support |
| Next/previous navigation | `‹` `›` buttons + `←`/`→` keys, `Esc`/backdrop close |
| Lazy loading | `loading="lazy"` on all grid thumbnails |
| Original-file download | `download_url` (`fl_attachment` transform) — button in grid caption + lightbox |
| Pagination | `GET .../media?page=&page_size=` (default 20, max 100); "Load more" button shows `(shown of total)` |

## API changes

- `GET /families/{fid}/albums/{aid}/media` now returns
  `{items, total, page, page_size}` instead of a bare list
- `MediaResponse` gained `download_url`

## Tests — 44 passing

Added: pagination (25 items → 20+5, no overlap), `download_url` presence,
updated list/delete tests for the envelope shape.
