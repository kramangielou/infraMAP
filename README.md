# infraMAP — Infrastructure Monitoring GIS

A production-minded, prototype-cost-conscious web GIS for monitoring fictional infrastructure projects. The implementation follows the supplied build specification: React/Vite + TypeScript on Vercel, FastAPI on Render, Supabase PostgreSQL/PostGIS/Auth/Storage, MapLibre GL JS, and Recharts. The source explicitly requires a working application rather than a proposal and requires the monitoring evidence workflow to be tied to specific progress records.

> **DEMO DATA:** all seeded projects are fictional demonstration records and must not be represented as real government data.

## Repository layout

```text
infraMAP/
├── frontend/                 # React + Vite + TypeScript + MapLibre + Recharts
├── backend/                  # FastAPI + PostgreSQL/PostGIS + Supabase Storage integration
├── supabase/
│   ├── migrations/           # schema, constraints, RLS, Storage policies
│   └── seed/                 # fictional demo projects + progress history
├── docs/
├── .env.example
└── README.md
```

## Implemented MVP

- Supabase email/password authentication.
- `ADMIN` and `VIEWER` roles with server-side authorization and RLS.
- Dashboard KPIs, global filters, project map, recent monitoring activity, and charts.
- Project catalog with search, filters, server-side pagination, and sorting.
- Shareable project detail pages.
- PostGIS `POINT`, `LINESTRING`, and `POLYGON` in one `projects` entity.
- MapLibre status styling, legend, navigation, selection and fit-to-project.
- Admin project creation/editing with geometry drawing.
- Progress history retained instead of replacing prior progress.
- Planned-vs-actual schedule logic with `On Track / At Risk / Delayed / Insufficient Data`.
- MOV image upload attached to a **specific progress update**, with JPG/JPEG/PNG/WEBP validation, 10 MB default per-image limit, Supabase Storage, metadata in PostgreSQL, signed viewing URLs, gallery/lightbox, and admin-only delete.
- Basic backend and frontend tests.
- Vercel and Render configuration.

The source specification calls for Supabase Storage rather than PostgreSQL binary storage, a dedicated `project_progress_media` table, authenticated/authorized uploads, and viewer read-only access.

## Deployment: zero to a live infraMAP system

This section is the complete deployment walkthrough for the repository as supplied. It assumes the target architecture is:

```text
User browser
    |
    v
Vercel (React/Vite frontend)
    |
    | HTTPS API calls + Supabase Auth
    v
Render (FastAPI backend) ---------> Supabase Auth
    |                                  |
    |                                  v
    +-----------------------------> Supabase PostgreSQL/PostGIS
                                       |
                                       v
                                Supabase Storage
                                  (private MOV)
```

The procedure below keeps the Supabase service-role key on the backend only. Never place that key in Vercel, frontend source code, browser JavaScript, Git, or a public document.

### Phase 0 — Prepare your accounts and tools

Before starting, have:

1. A GitHub account and a repository containing this `infraMAP` source tree.
2. A Supabase account.
3. A Render account.
4. A Vercel account.
5. Git installed locally if you plan to push the repository from your computer.
6. Node.js 20+ for local frontend testing.
7. Python 3.12+ for local backend testing.

You can deploy from GitHub without running the application locally first, but local testing is strongly recommended before exposing the application publicly.

### Phase 1 — Put the project in GitHub

1. Create a new GitHub repository, for example `infraMAP`.
2. Do **not** commit `.env`, `.env.local`, passwords, database connection strings, JWT secrets, or Supabase service-role keys.
3. From the repository root, initialize Git if necessary:

```bash
git init
git add .
git commit -m "Initial infraMAP application"
git branch -M main
git remote add origin https://github.com/YOUR_ACCOUNT/YOUR_REPOSITORY.git
git push -u origin main
```

4. Confirm that GitHub contains the `frontend/`, `backend/`, and `supabase/` directories.
5. If a secret has accidentally been committed, rotate it before proceeding. Removing it from the latest file alone is not sufficient because Git history may still contain it.

### Phase 2 — Create the Supabase project

1. Sign in to Supabase.
2. Create a new project.
3. Choose the organization and project name appropriate for your deployment.
4. Set a strong database password and store it in a password manager.
5. Wait until the project is provisioned.
6. Open the project's **SQL Editor**.
7. Keep the Supabase project dashboard open because you will need values from the project's API/settings pages later.

The application uses Supabase for PostgreSQL, PostGIS, Auth, and private Storage. The database schema and policies are supplied in `supabase/migrations/001_init.sql`.

### Phase 3 — Create the database schema, PostGIS objects, RLS, and Storage bucket

1. Open `supabase/migrations/001_init.sql` in the repository.
2. Copy the entire file into the Supabase SQL Editor.
3. Run it once.
4. Confirm the query finishes without an error.
5. Verify that the migration created the application tables, including:
   - `profiles`
   - `projects`
   - `project_progress`
   - `project_progress_media`
   - `audit_logs`
6. Verify that the private Storage bucket `project-mov` exists.
7. Verify that Row Level Security is enabled on the application tables.

The migration also creates the project geometry column and its validation for `Point`, `LineString`, and `Polygon`, plus Storage policies for project monitoring evidence.

> **Important:** Run the migration before inserting demo records or creating application users. The migration creates the Auth-user profile trigger used by the first-login flow.

### Phase 4 — Load the fictional demonstration data

The repository includes intentionally fictional demo data.

1. Open `supabase/seed/001_demo.sql`.
2. Copy its contents into a new Supabase SQL Editor query.
3. Run it after the migration succeeds.
4. Confirm that projects and progress records appear in the database.

The seeded records are demonstration data only. Do not present them as real government or infrastructure records.

### Phase 5 — Configure Supabase Authentication

1. In the Supabase dashboard, open **Authentication**.
2. Open the provider settings.
3. Enable the **Email** provider.
4. Decide whether email confirmation is required for your deployment. For a real deployment, use the confirmation/security settings appropriate to your organization's identity policy.
5. Configure the application URL/redirect settings for the final Vercel URL once that URL is known. During initial testing, you may also use the local frontend URL.

The application uses Supabase email/password authentication. The frontend receives only the public Supabase URL and anon key; privileged database/storage credentials stay on the backend.

### Phase 6 — Create the first ADMIN account securely

The repository deliberately does not contain a production administrator password.

1. In Supabase Authentication, create the first user using the normal Supabase user-creation flow.
2. Complete email confirmation if your Auth settings require it.
3. The database trigger creates a `VIEWER` profile for the new Auth user.
4. Open the Supabase SQL Editor.
5. Find the user's Auth UUID in the Authentication users list.
6. Change only that user's profile role to `ADMIN` with a SQL statement equivalent to:

```sql
update public.profiles
set role = 'ADMIN'
where id = 'YOUR_AUTH_USER_UUID';
```

7. Verify the role:

```sql
select id, email, role
from public.profiles
where id = 'YOUR_AUTH_USER_UUID';
```

8. Sign in to the application with that account after the frontend is deployed.

Do not put a password into `seed/001_demo.sql`, source code, README files, Render environment variables, or Vercel environment variables.

### Phase 7 — Collect the Supabase values required by the backend

You need four values for Render:

| Variable | What to use |
|---|---|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | The project's public anon/publishable key used for Auth token validation |
| `SUPABASE_SERVICE_ROLE_KEY` | The project's server-only service-role key |
| `DATABASE_URL` | The PostgreSQL connection string for the Supabase database |

Copy the URL and API keys from the Supabase project's API/settings area. Obtain the database connection string from the project's database connection settings.

For `DATABASE_URL`, use the connection format appropriate to the hosting environment and Supabase's current connection guidance. Do not paste the database password into GitHub or the README.

### Phase 8 — Test the backend locally before deploying it

From the repository root:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment:

**macOS/Linux:**

```bash
source .venv/bin/activate
```

**Windows PowerShell:**

```powershell
.venv\\Scripts\\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Copy the backend environment template:

```bash
cp .env.example .env
```

On Windows, copy the file using File Explorer or PowerShell if `cp` is unavailable.

Fill `.env` with the Supabase values. For local testing, use:

```env
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY=YOUR_SUPABASE_SERVICE_ROLE_KEY
DATABASE_URL=YOUR_SUPABASE_POSTGRES_CONNECTION_STRING
CORS_ORIGINS=http://localhost:5173
MOV_BUCKET=project-mov
MAX_MOV_MB=10
```

Start FastAPI:

```bash
uvicorn app.main:app --reload --port 8000
```

In a browser, verify:

```text
http://localhost:8000/health
http://localhost:8000/docs
```

The health endpoint should return a successful response. The OpenAPI page should load.

### Phase 9 — Test the frontend locally

Open another terminal:

```bash
cd frontend
npm install
cp .env.example .env.local
```

Set `.env.local` to:

```env
VITE_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
VITE_API_URL=http://localhost:8000
VITE_MAP_STYLE_URL=https://demotiles.maplibre.org/style.json
```

Start Vite:

```bash
npm run dev
```

Open:

```text
http://localhost:5173
```

Test at least:

1. Login with the ADMIN account.
2. Dashboard loads.
3. Project catalog loads.
4. Project detail opens.
5. Map displays project geometry.
6. Admin can create/edit a project.
7. Admin can add progress.
8. Admin can attach multiple JPG/JPEG/PNG/WEBP evidence images to that specific progress record.
9. Viewer accounts can read but cannot perform admin writes.

### Phase 10 — Deploy the FastAPI backend to Render

The repository includes `backend/render.yaml` and `backend/Dockerfile`.

1. Sign in to Render.
2. Create a new **Web Service**.
3. Connect the GitHub repository containing infraMAP.
4. Set the service root/build configuration so Render uses the `backend` application. The supplied Render configuration uses the backend Dockerfile.
5. If Render offers to use the repository's `render.yaml`, use that configuration or reproduce its settings in the service UI.
6. Confirm the service is a Docker-based web service.
7. Configure the environment variables below as **secret/server-side variables**:

```env
SUPABASE_URL=https://YOUR_PROJECT.supabase.co
SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY=YOUR_SUPABASE_SERVICE_ROLE_KEY
DATABASE_URL=YOUR_SUPABASE_POSTGRES_CONNECTION_STRING
CORS_ORIGINS=http://localhost:5173
MOV_BUCKET=project-mov
MAX_MOV_MB=10
```

8. Do not add `SUPABASE_SERVICE_ROLE_KEY` to Vercel or any frontend variable beginning with `VITE_`.
9. Deploy the service.
10. Wait for the Render build and deployment to finish.
11. Open the Render service URL followed by `/health`.
12. Confirm the endpoint responds successfully.
13. Record the HTTPS Render URL. It will be the production value of `VITE_API_URL` in Vercel.

#### Render CORS configuration

After the Vercel deployment URL is known, return to Render and change:

```env
CORS_ORIGINS=https://YOUR_VERCEL_DOMAIN
```

If you need more than one allowed frontend origin, configure the value according to the backend's accepted CORS format rather than using a wildcard unnecessarily.

For initial local + production testing, the backend can be configured with the required comma-separated origins if supported by the deployed configuration, for example:

```env
CORS_ORIGINS=http://localhost:5173,https://YOUR_VERCEL_DOMAIN
```

Use HTTPS for the public frontend.

### Phase 11 — Deploy the React frontend to Vercel

1. Sign in to Vercel.
2. Select **Add New Project**.
3. Import the same GitHub repository.
4. Set the frontend root directory to:

```text
frontend
```

5. Allow Vercel to detect Vite.
6. The expected build command is:

```bash
npm run build
```

7. Configure these Vercel environment variables:

```env
VITE_SUPABASE_URL=https://YOUR_PROJECT.supabase.co
VITE_SUPABASE_ANON_KEY=YOUR_SUPABASE_ANON_KEY
VITE_API_URL=https://YOUR_RENDER_SERVICE.onrender.com
VITE_MAP_STYLE_URL=https://demotiles.maplibre.org/style.json
```

8. Deploy the project.
9. Open the generated Vercel URL.
10. Confirm the login screen loads.

The repository includes `frontend/vercel.json` with an SPA rewrite so routes such as `/projects/{id}` resolve to the React application instead of returning a static 404.

### Phase 12 — Connect the production frontend to Supabase Auth

After Vercel provides the production URL:

1. Copy the exact HTTPS Vercel URL.
2. Return to Supabase Authentication settings.
3. Add the Vercel URL to the allowed site/redirect configuration required by your Auth setup.
4. Save the changes.
5. If you use a custom production domain, configure that domain in Supabase instead of relying only on the temporary Vercel domain.

Then test login again from the Vercel site.

### Phase 13 — Lock down Render CORS for the production frontend

1. Return to Render.
2. Open the backend service environment variables.
3. Set `CORS_ORIGINS` to the exact production Vercel origin, for example:

```env
CORS_ORIGINS=https://inframap.example.com
```

4. Redeploy/restart the Render service if Render does not automatically restart after the environment change.
5. Test the frontend again.

Do not use `*` as the permanent production CORS policy when the application has a known frontend origin.

### Phase 14 — Configure the production map style

The default prototype setting is:

```env
VITE_MAP_STYLE_URL=https://demotiles.maplibre.org/style.json
```

This is suitable for demonstrating MapLibre behavior, but it should not be treated as an unlimited production map service.

For production:

1. Choose a map style/tile provider whose licensing and usage limits fit your organization.
2. Or self-host an appropriate open map style/tile stack.
3. Set `VITE_MAP_STYLE_URL` in Vercel to that style URL.
4. Redeploy the frontend.
5. Verify that the dashboard, catalog, and project maps still load.

The application does not require a paid GIS SDK. The style/tile provider is a separate operational consideration.

### Phase 15 — Create a normal VIEWER account

To test the read-only role separately from ADMIN:

1. Create another user through Supabase Auth.
2. Let the database trigger create its `VIEWER` profile.
3. Verify the role:

```sql
select id, email, role
from public.profiles
where email = 'VIEWER_EMAIL';
```

4. Do not change this user's role to `ADMIN`.
5. Sign into the deployed Vercel application as the viewer.
6. Confirm the viewer can inspect projects and monitoring evidence but cannot use admin write operations.

The backend performs the actual admin authorization check; hiding an admin button in the frontend is not treated as sufficient security.

### Phase 16 — Perform the production smoke test

Run the following sequence against the live Vercel application.

#### Authentication

- [ ] Login succeeds with an ADMIN account.
- [ ] Login succeeds with a VIEWER account.
- [ ] An unauthenticated visitor cannot access protected application data.

#### Dashboard

- [ ] KPI cards load.
- [ ] Global filters work.
- [ ] Map loads.
- [ ] Map status styling/legend is visible.
- [ ] Recent monitoring activity loads.
- [ ] Charts load.

#### Project catalog

- [ ] Search works.
- [ ] Filters work.
- [ ] Pagination works.
- [ ] Sorting works.
- [ ] Opening a project takes the user to its detail page.

#### Project detail

- [ ] Project information loads.
- [ ] Geometry displays correctly.
- [ ] Progress history is retained.
- [ ] Planned-vs-actual status is visible.
- [ ] Monitoring evidence appears under the progress record to which it belongs.

#### Admin project management

- [ ] ADMIN can create a project.
- [ ] ADMIN can edit a project.
- [ ] ADMIN can archive/delete a project through the supplied soft-delete behavior.
- [ ] ADMIN can draw/select Point geometry.
- [ ] ADMIN can draw/select LineString geometry.
- [ ] ADMIN can draw/select Polygon geometry.

#### Progress + MOV evidence

1. Open a project as ADMIN.
2. Add a new completion percentage.
3. Enter the progress date.
4. Add remarks.
5. Select several valid JPG/JPEG/PNG/WEBP images.
6. Preview the selected images.
7. Remove one preview and confirm the remaining images are correct.
8. Upload/save the progress record.
9. Confirm the new progress record appears in the timeline.
10. Confirm each evidence image is attached to that specific progress record.
11. Open the evidence gallery/lightbox.
12. Confirm images load through signed URLs.
13. As VIEWER, confirm the evidence can be viewed.
14. As VIEWER, confirm there is no upload/delete capability.
15. As ADMIN, confirm an evidence item can be deleted.

### Phase 17 — Verify the private Storage boundary

In Supabase Storage, the `project-mov` bucket should remain private.

The intended flow is:

```text
ADMIN browser
   |
   | authenticated API request
   v
FastAPI
   |
   +--> validate Supabase Auth user
   +--> verify ADMIN role
   +--> validate image MIME/extension/size
   +--> store object in private project-mov bucket
   +--> store metadata in project_progress_media
   |
   v
short-lived signed URL
   |
   v
authenticated project viewer
```

Do not make the evidence bucket public simply to make the gallery easier to implement. The application is designed around private evidence with signed viewing URLs.

### Phase 18 — Final production configuration checklist

Before treating the system as live, verify:

- [ ] Supabase project is the intended production project.
- [ ] Database migration ran successfully.
- [ ] Demo seed data has been reviewed; remove it if this is not a demo environment.
- [ ] PostGIS geometry constraints are present.
- [ ] RLS is enabled.
- [ ] Storage bucket `project-mov` is private.
- [ ] Storage policies allow only the intended authenticated operations.
- [ ] First ADMIN account was created without storing its password in source.
- [ ] At least one VIEWER account has been tested.
- [ ] `SUPABASE_SERVICE_ROLE_KEY` exists only in Render/backend secrets.
- [ ] No Supabase service-role key appears in Vercel variables.
- [ ] `CORS_ORIGINS` contains the intended production frontend origin.
- [ ] Supabase Auth redirect/site settings contain the intended production frontend URL.
- [ ] Render `/health` succeeds.
- [ ] Vercel application loads over HTTPS.
- [ ] Login works from the production URL.
- [ ] Dashboard, map, catalog, and detail pages work.
- [ ] Point/LineString/Polygon behavior works.
- [ ] Progress history works.
- [ ] MOV upload, preview, gallery, signed viewing, and admin deletion work.
- [ ] Viewer is read-only.
- [ ] The production map style/tile provider's license and request limits have been reviewed.
- [ ] Image storage growth is monitored and unnecessary evidence is removed.
- [ ] Backups/retention and operational ownership have been established for the production Supabase project.

### Phase 19 — Updating the live application later

For a normal code-only release:

1. Make the change locally.
2. Run backend tests and frontend tests.
3. Commit the change to Git.
4. Push to the branch connected to Render/Vercel.
5. Render rebuilds/redeploys the backend.
6. Vercel rebuilds/redeploys the frontend.
7. Run the production smoke test for the changed feature.

For database changes:

1. Create a new numbered SQL migration rather than editing an already-applied migration in place.
2. Test the migration against a non-production database when possible.
3. Back up/confirm recovery procedures before applying a production schema change.
4. Apply the migration.
5. Deploy the matching backend/frontend code.
6. Verify RLS and Storage policies again if the schema/security boundary changed.

Do not casually replace an already-applied migration file and assume the production database will update automatically.

### Phase 20 — Troubleshooting guide

#### The Vercel site loads but API requests fail

Check, in order:

1. `VITE_API_URL` points to the HTTPS Render URL, not `localhost`.
2. Render `/health` works directly.
3. Render `CORS_ORIGINS` exactly matches the Vercel origin.
4. The Render service has the correct Supabase variables.
5. Browser developer tools show whether the failure is CORS, authentication, or a server error.

#### Login succeeds but the dashboard does not load

Check:

1. Supabase URL and anon key in Vercel.
2. Supabase Auth redirect/site settings.
3. Render API URL in `VITE_API_URL`.
4. Render logs for authentication/database errors.
5. The user's `profiles` row and role.

#### ADMIN sees the app but cannot create/edit projects

Check:

1. The Auth user UUID matches the `profiles.id` value.
2. `profiles.role` is exactly `ADMIN`.
3. The Supabase database migration was applied.
4. Render has the correct `SUPABASE_SERVICE_ROLE_KEY` and `DATABASE_URL`.
5. Render logs for the failed request.

#### MOV upload fails

Check:

1. `project-mov` exists and is private.
2. `MOV_BUCKET=project-mov` in Render.
3. `MAX_MOV_MB` is appropriate.
4. The file is JPG/JPEG/PNG/WEBP.
5. The file is within the configured size limit.
6. Render can connect to Supabase Storage using the configured service-role key.
7. The progress record was created before the media objects were uploaded.

#### The map is blank

Check:

1. `VITE_MAP_STYLE_URL` is reachable.
2. The style provider permits requests from the deployed site.
3. The browser console for MapLibre/style errors.
4. Project geometry exists and uses SRID 4326.
5. The selected project has valid Point, LineString, or Polygon GeoJSON.

#### A project URL returns a 404 after refreshing

Confirm that the Vercel deployment is using the supplied `frontend/vercel.json` SPA rewrite. The React Router routes need the hosting platform to return `index.html` for client-side routes.

### Local development

The following shorter setup is retained for developers who only need to run the application locally.

1. Create a Supabase project and apply the migration/seed.
2. Configure the backend `.env` from `backend/.env.example`.
3. Start FastAPI on port 8000.
4. Configure the frontend `.env.local` from `frontend/.env.example`.
5. Start Vite on port 5173.
6. Open `http://localhost:5173`.

The frontend only receives the Supabase URL/anon key. The Supabase service-role key remains backend-only, as required by the specification.

## API

| Method | Route | Access |
|---|---|---|
| GET | `/health` | public |
| GET | `/me` | authenticated |
| GET | `/projects` | authenticated |
| GET | `/projects/{id}` | authenticated |
| POST | `/projects` | admin |
| PUT | `/projects/{id}` | admin |
| DELETE | `/projects/{id}` | admin; soft archive |
| GET | `/projects/{id}/progress` | authenticated |
| POST | `/projects/{id}/progress` | admin; multipart MOV |
| DELETE | `/progress-media/{id}` | admin |
| GET | `/dashboard/summary` | authenticated |
| GET | `/dashboard/projects-by-year` | authenticated |
| GET | `/dashboard/projects-by-status` | authenticated |
| GET | `/dashboard/projects-by-sector` | authenticated |
| GET | `/dashboard/recent-updates` | authenticated |

Filtering supports year, status, project type, location, implementing agency, and search. Catalog requests also support `page`, `page_size`, `sort_by`, and `sort_dir`.

## Geometry model

All project geometry lives in one PostGIS column using SRID 4326. The API accepts GeoJSON geometry and validates `Point`, `LineString`, and `Polygon`; the frontend draws these with MapLibre without introducing a paid GIS API. This matches the source requirement to use one project entity rather than separate point/line/polygon tables.

The default style is isolated in `VITE_MAP_STYLE_URL`. Replace it with a provider you are licensed to use or a self-hosted/open style. A public demo style is useful for local prototyping but should not be treated as an unlimited production tile service.

## Schedule monitoring rules

Implemented in both the frontend utility and backend service:

- **Insufficient Data:** start or target end is missing.
- **Delayed:** target end has passed and progress is below 100%.
- **At Risk:** actual progress is more than 15 percentage points behind expected linear progress.
- **On Track:** otherwise.

Expected progress is a transparent linear trajectory from `start_date` to `target_end_date`, clamped to 0–100. The 15-point threshold is configurable in the calculation function. The source requires the underlying calculation to be documented rather than hiding a simplistic status decision.

## MOV / project monitoring evidence

The admin progress workflow is:

1. Enter new completion percentage, date, and remarks.
2. Select multiple images.
3. Preview/remove images before submit.
4. Save the progress history record.
5. Upload accepted images to `project-mov/{project_id}/{progress_id}/{uuid}.ext`.
6. Store image metadata in `project_progress_media`.
7. Refresh the monitoring timeline.

Supported image types are JPEG, PNG, and WEBP; the default per-image limit is 10 MB. The backend checks both MIME type and extension and never uses user filenames as unrestricted storage paths. The source explicitly requires partial-upload failures to be communicated instead of silently claiming success.

Images are private in Supabase Storage and displayed through short-lived signed URLs. Viewers can read evidence but cannot upload, delete, or modify it. Admin deletion removes the metadata record and attempts to remove the Storage object. The source specifies these role rules.

## Testing

Backend:

```bash
cd backend
pytest
```

Frontend:

```bash
cd frontend
npm install
npm test
```

Tests cover schedule rules, geometry validation, and the health endpoint; the UI also keeps role protection in the router while the actual write authorization is enforced by the FastAPI dependency and Supabase RLS.

## Vercel

Set the frontend root directory to `frontend`. Vercel detects Vite automatically. Configure:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_API_URL`
- `VITE_MAP_STYLE_URL`

`frontend/vercel.json` rewrites SPA routes such as `/projects/{id}` to `index.html`.

## Render

The backend includes `backend/Dockerfile` and `backend/render.yaml`. Create a Render web service from the repository and provide the backend environment variables. The service listens on `$PORT` and exposes `/health`.

Render free-tier services can sleep and may have cold starts/usage limits. Supabase Storage and database usage are also subject to the selected Supabase plan's quotas. Public map tiles have their own provider terms/limits. No third-party service should be assumed to remain free forever.

## Cost / free-tier considerations

The prototype intentionally avoids paid map APIs, Google Maps, paid GIS SDKs, Redis, workers, paid analytics, and separate image hosting. The source requires cost to be a primary architectural constraint.

Potential future cost/limits:

- Supabase database/storage/auth quotas.
- Render service quotas and sleeping behavior.
- Vercel build/deployment limits.
- Map tile provider terms and request limits.
- Storage growth from MOV photos.

For the prototype, resize/compress images client-side before upload when practical, limit image size, and delete incorrect/duplicate evidence. The source explicitly prioritizes storage-cost control.

## Deployment checklist

- [ ] GitHub repository created
- [ ] Supabase project created
- [ ] PostGIS enabled
- [ ] Migration executed
- [ ] RLS enabled
- [ ] Demo data inserted
- [ ] Auth configured
- [ ] Admin account created securely
- [ ] Viewer account created
- [ ] Render backend deployed
- [ ] `/health` works
- [ ] Vercel frontend deployed
- [ ] Environment variables configured
- [ ] Login works
- [ ] Dashboard/map/catalog/detail pages work
- [ ] Admin project editing works
- [ ] Viewer is read-only
- [ ] Point/line/polygon geometry works
- [ ] Progress history works
- [ ] MOV upload/preview/gallery/lightbox works
- [ ] MOV Storage policies prevent unauthorized uploads
- [ ] Planned-vs-actual monitoring works

These items align with the source's final acceptance criteria and its updated MOV acceptance criteria.

## Design notes / deliberate prototype trade-offs

- FastAPI uses the Supabase Auth `/auth/v1/user` endpoint to validate the presented bearer token, then loads the role from PostgreSQL. This avoids duplicating JWT verification configuration in the prototype while keeping authorization server-side.
- Backend DB access uses a small connection pool and the service-role database credentials remain server-only. Direct browser access is not used for project writes.
- Supabase RLS remains enabled for direct authenticated access and storage policies; FastAPI performs an independent role check before writes.
- MapLibre uses layers rather than one React marker per project for better scaling.
- 3D is intentionally omitted from the MVP; the source explicitly makes 2D mandatory and 3D optional.

## License

Choose and add the license appropriate for your repository before public release.
