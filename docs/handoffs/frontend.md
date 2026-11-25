# Frontend engineering handover — remote verification release

## Changes
- Public Component Assets page at /components provides identified-part life/availability; admins register real physical identities and map component types to verified new-part preparation stock. Registration and dismantling never invent/increase new stock.
- Operators can dismantle an explicitly selected nonrunning stand with a reason. The backend controls readiness reset/atomic history.
- Component preparation selects actual available identities, derives new/reused counts, requires an explicit reason for tracking skips, and never accepts pooled guessed carried life.
- Gauging confirmation uses a persistent backend command receipt; manual retry checks its saved outcome before attempting the status request again. No write silently replays offline.
- Acknowledged stage keys are forgotten so a later preparation cycle with identical operator/remarks receives a new command.
- Unknown/partial actual life remains unknown/partial in stand-area, entry-guide, stand history and component displays. Null cannot be interpreted as zero for life-percentage health.
- Stock catalog/edit/balance-correction controls require admin; operators retain logging new completed life. Guide actions require an authenticated operator. Existing custom stand-change time is already admin-only.
- Existing dashboard already derives running denominator from all returned positions; no change needed. Existing RuntimePanel public viewer/operator current state/admin corrections and line creation retained.
- Existing PM/report preview confirmations already use stable idempotency keys and distinguish reviewed history/imports.

## Verification
The execution environment is unavailable, so no local frontend build is claimed. GitHub CI on this new release branch must run client tests, production build, same-origin proxy checks and static export. Added semantic tests for unknown runtime labels and stage-key acknowledgement. Do not deploy until the parent integrates sibling domain/AI changes and checks final exact source.

## Limitations
Offline support remains cached public shell/snapshot, without autonomous stock/stand changes. Component registry returns up to2,000 records; label discloses limit. Historical runtime and initial component identity/stock need real commissioning data; no old workbook quantity is fabricated into individual identities.
