# Release handover — 25 November 2026

Production main remains d34978df3f5a5e4cf1121503df553e3978baa87e. Review checkpoint b429c7c3d021d5519d8d8e85c1a71845f02da9fa is not release-approved.

The execution environment is currently unavailable. Use the review branch as authoritative; edits made after the checkpoint in prior transient workspaces may not exist here. Do not claim they are saved, tested or deployed without checking this branch.

Prior CI run45502305285: frontend passed, backend failed before tests at PostgreSQL container initialization. Corrected the health-command quoting in this checkpoint; require a new full CI run.

Remaining verified review items to inspect/fix: legacy lifetime0 must not certify known zero history; require saved component preparation or explicit reasoned skip before Gauging; explicit nonrunning dismantle/return that preserves identity and measured life without adding NEW stock; public component registry/admin mapping and selection UI; null-life labels across all screens; dynamic line denominator; admin-only corrections; AI PM imports must never silently change stands with assumed midnight timestamps; all-or-none confirmed imports and atomic receipts; actual PostgreSQL integration/concurrency tests.

Agent findings in conversation are evidence of earlier work, not proof of the durable branch state. Recover missing changes from the source and re-test. Obtain independent project-manager approval of exact final source before merging to main; then verify API/static/legacy frontend deployments read-only. Free hosting does not guarantee24/7 or perpetual-free provider operation. Do not invent runtime or initial component/stock data during commissioning.
