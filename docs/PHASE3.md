# Phase 3 — Persistent Operations & Data Integrity

This phase makes the stand-area workflow safe for persistent database use.

## Rules enforced

- A physical stand can be installed in only one running position at a time.
- A running position can contain only one active stand.
- A running stand cannot appear in Ready/Pending/Gauging/Hydrotest.
- Removed stands automatically return to **PENDING**.
- Replacement stands must be **READY** before installation.
- Preparation workflow advances one step at a time:
  `YET_TO_READY -> PENDING -> GAUGING -> HYDROTEST -> READY`.
- A stand can be reset to **PENDING** from a later preparation stage if rework is needed.
- Stand life is accumulated in hours on removal; the current campaign is calculated live from the installation timestamp.
- Duplicate line positions are blocked at database level.
- Active installation uniqueness is also enforced at PostgreSQL database level to protect against simultaneous users.

## Entry guides

Entry-guide tracking remains restricted to positions 2, 4, 6, 8 and 10. Active-guide uniqueness is protected in the same way as stands.

## Migration

Run:

```bash
cd backend
alembic upgrade head
```

before using the updated application with an existing database.

## Inventory traceability extension
- Inventory quantity changes are transactional and require operator + reason.
- Every transaction stores before/change/after quantity and timestamp.
- Direct set-quantity corrections are tracked separately as CORRECTION.
- Inventory items are archived instead of physically deleted, preserving transaction history.
- Archived items are hidden from the default active inventory list.


## Persistent preparation history
- Every preparation transition is stored in `stand_preparation_events`.
- Required traceability: previous status, new status, operator, remarks, timestamp.
- Running stands cannot enter preparation workflow.
- Only one-step progression is allowed: Yet to Ready → Pending → Gauging → Hydrotest → Ready.
- Gauging/Hydrotest/Ready can reset to Pending for rework.
- Only READY stands can be installed into W1/W2/W3.
