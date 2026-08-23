# Digital Stand Register

Production-oriented stand-area management application for three finishing-mill lines, spare stand preparation, stand-life tracking, entry guides, inventory, transaction history, and monthly Excel running-status export.

## Core plant rules

- 3 running lines: W1, W2, W3; 10 positions each.
- A running stand exists only in one line position and cannot appear in Ready/Pending/WIP lists.
- Spare workflow: `Yet to Ready -> Pending -> Gauging -> Hydrotest -> Ready -> Installed`.
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
