# Digital Stand Register

Production-oriented stand-area management application for three finishing-mill lines, spare stand preparation, stand-life tracking, entry guides, inventory, transaction history, and monthly Excel running-status export.

## Core plant rules

- 3 running lines: W1, W2, W3; 10 positions each.
- A running stand exists only in one line position and cannot appear in Ready/Pending/WIP lists.
- Spare workflow: `Pending -> Gauging -> Hydrotest -> Ready -> Installed`.
- A removed running stand automatically returns to `Pending`.
- Stand life is tracked in running hours from installation/removal timestamps.
- Entry guides are applicable only at positions 2, 4, 6, 8, and 10.
- No automatic deletion of running state or lifecycle history.
- Monthly Excel files are generated on demand and are not stored by the server.

## Quick start with Docker

1. Copy `.env.example` to `.env` and change the password and secret.
2. Build and start:

```bash
docker compose up --build -d
```

3. Open:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

Database migrations run automatically every time the backend container starts.

## Load the 22/08/2026 baseline once

After the first startup:

```bash
docker compose exec backend python scripts/seed_20260822.py
```

The seed is idempotent for commissioning and applies the priority rule `Running > Ready > INP > Pending`. It does not invent the four stand codes that were absent from the supplied report.

## Important production environment variables

- `DATABASE_URL` — set automatically by Docker Compose; set explicitly on cloud platforms.
- `SECRET_KEY` — use a long random value.
- `CORS_ORIGINS` — comma-separated allowed frontend origins.
- `NEXT_PUBLIC_API_URL` — browser-visible backend URL ending in `/api/v1`; this is baked into the frontend build.

## Retention

There is no automatic cleanup. Running stands, active installations, stand life, stand-change history, preparation history, entry-guide history, and inventory history remain in the database. Exported Excel reports are generated only when requested, so they do not consume server storage.

## Validation commands

Backend:

```bash
cd backend
python -m compileall -q app scripts tests
pytest -q
```

Frontend:

```bash
cd frontend
npm ci
npm run build
```

## Render deployment

`render.yaml` plans two free web services in Singapore. PostgreSQL runs in the
dedicated Neon Free project `digital-stand-register` (`withered-lake-09762482`).
Supply its connection string as the API service's secret `DATABASE_URL` during
Blueprint setup; never commit credentials. Free-tier resource limits apply.
No existing resources are adopted. The database starts empty; this does not migrate
an existing plant database or automatically seed an old commissioning snapshot.

Browser API requests use `/api/v1` on the frontend origin. Next.js forwards them
to `DSR_API_ORIGIN`, populated from the API service URL. Local development defaults
to `http://localhost:8000`. An explicitly configured `NEXT_PUBLIC_API_URL` still
supports separate frontend and backend origins.

The API runs Alembic migrations before startup. Render generates its signing key.
After deployment, verify `/health`, the frontend `/operations` and `/intelligence`
pages, and read API responses before commissioning plant data. Create the first
admin through the existing first-setup flow before sharing the new instance.

## Spare average life and current stock

The Spares page opens to average life and current stock. Average life uses completed
component-life records: `sum(life_hours × quantity) / sum(quantity)`. Each grouped
entry must describe spares with the same measured completed life. Active stand age,
carried reused life, procurement targets and consumption totals are not life samples.
The UI shows sample count; an older manually supplied average is labelled as manual
and used only when no completed samples exist. Life above the expected target is
not capped at 100%.

Stock is nullable: unknown is separate from a verified zero balance. Set an opening
balance before issuing or receiving quantity adjustments. Every subsequent adjustment
records its before/after quantities, operator and reason. Life records never alter
stock. The workbook supplies catalog names only; receipts are not an opening balance.
