# Acceptance matrix

| Area | Implemented |
|---|---|
| Auth | Supabase Auth, profile roles, protected routes |
| Authorization | FastAPI admin dependency + Supabase RLS |
| Dashboard | KPIs, filters, map, recent updates, charts |
| Catalog | Search, filters, pagination, sorting, map split view |
| Detail | Information, map, progress history, schedule indicators, MOV gallery/lightbox |
| Admin create/edit | Project fields + Point/LineString/Polygon geometry editor |
| Progress | History preserved; current completion refreshed |
| MOV | Multiple photos, validation, compression, captions, dates, Storage, metadata, signed URLs |
| Viewer MOV access | Read-only |
| Admin MOV management | Upload and delete |
| GIS | PostGIS + GeoJSON + MapLibre |
| Security | No service-role key in frontend; server role checks; RLS |
| Deployment | Vercel config + Render Docker config + env examples |
| Tests | Backend schedule/geometry/health; frontend schedule |

## Remaining production hardening opportunities

- Add automated browser/E2E tests against a disposable Supabase project.
- Add full audit-log writes for every admin mutation if operational audit requirements expand.
- Add true client-side EXIF parsing only if needed; manual date remains supported.
- Replace the demo basemap with a provider/self-hosted style whose production terms and quotas are understood.
- Add virus/malware scanning only if the deployment threat model requires it; the MVP intentionally permits image formats only.
