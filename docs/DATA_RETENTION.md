# Data Retention Policy

## Protected live data

The application has **no automatic deletion job**.

The following data must never be deleted by report cleanup:

- Current W1/W2/W3 running stand assignments.
- Active stand installations (`removed_at IS NULL`).
- Current stand location/status.
- Cumulative stand lifetime hours.
- Active entry-guide installations.
- Inventory current quantities.

## Reports

Monthly running-status Excel files are generated on demand from database history and streamed to the user. They are **not stored on the application server**, so report downloads do not consume persistent server storage.

## Historical records

Stand-change, stand-preparation, entry-guide and inventory transaction history is retained by default. Any future cleanup feature must be an explicit administrator action with a confirmation step and must exclude active records.

Because this application produces only a small number of plant transactions per day, retaining the database history is inexpensive and is preferred for maintenance traceability.
