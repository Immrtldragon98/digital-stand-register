# Phase 2 - Stand Area Workflow

Implemented:
- Stand Area added to main navigation.
- Live 3-line position grid backed by `/dashboard/`.
- Stand click opens cumulative life, current campaign, leakage, vibration and installation history.
- Entry guide details and history are shown with stand details for positions 2, 4, 6, 8 and 10.
- Spare/preparation workflow: YET_TO_READY -> PENDING -> GAUGING -> HYDROTEST -> READY.
- One-step progression control for spare stands.
- Stand change form records replacement stand, operator, reason, condition and notes.
- Removed stand automatically returns to PENDING and its campaign hours are added to lifetime hours.
- Monthly running status Excel download uses one worksheet per line.
- Plant operations can be recorded by operator name without requiring a login session. Authentication can be added back later for admin control.

Data note:
The 22/08/2026 report contains duplicate/conflicting status entries (8A, 9A, 10A; and running 5D/10C also appearing in Pending). These are not auto-seeded until the correct status is confirmed.
