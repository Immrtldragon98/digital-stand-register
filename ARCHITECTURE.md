# Digital Stand Register — Clean Architecture

## Frontend
- `frontend/app/` — Next.js routes/screens
- `frontend/components/` — reusable UI grouped by feature
- `frontend/hooks/` — frontend hooks
- `frontend/lib/` — API client and utilities
- `frontend/store/` — client state

## Backend
- `backend/app/api/routes/` — HTTP endpoints only
- `backend/app/services/` — business rules/workflows
- `backend/app/repositories/` — database queries
- `backend/app/models/` — SQLAlchemy persistence models
- `backend/app/schemas/` — API request/response schemas
- `backend/app/auth/` — authentication/security
- `backend/app/config/` — application settings
- `backend/app/database/` — DB session/base
- `backend/alembic/` — schema migrations

## Main domain flow
`Route -> Service -> Repository -> Model/Database`

Frontend pages should call backend APIs through `frontend/lib/api.ts` rather than embedding database/business logic.

## Domain modules retained
- Dashboard / live line status
- Stand assets and stand life
- Stand changes / operations
- Entry guide tracking
- Activity audit trail
- Reports / Excel export

### Inventory audit model
`inventory_items` stores the current balance and active/archive state. `inventory_transactions` is append-only history for every stock movement. Quantity edits must go through `/inventory/{id}/quantity` or `/inventory/{id}/set-quantity`; normal item edits do not directly change stock.

## Initial data integrity

`backend/app/seed/snapshot_20260822.py` is the single source of truth for the first plant snapshot. `backend/scripts/seed_20260822.py` performs an idempotent import after migrations. It does not fabricate missing asset codes. Automated tests verify three complete running lines, no running/spare overlap, duplicate Ready priority, and the four-asset gap in the supplied report.
