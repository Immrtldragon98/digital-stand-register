# Current plant dependability and value evidence

Production remains on free hosting by explicit user choice. API idle sleep remains a provider limitation; the static application shell, labelled saved dashboard and read reconnection do not constitute an always-on service. Do not claim a 24/7 availability guarantee or fake runtime records to fill gaps.

## Recovery evidence

On 26 November 2026, snapshot `snap-fancy-darkness-a1odkf1b` of the Neon production branch was restored as isolated branch `br-bold-salad-a11agew0`. All 30 public tables matched the source by row counts and content fingerprints. Production was not replaced. The deployed verification result is in `backend/ops/recovery.json`; it is a point-in-time check, not continuous backup monitoring.

Neon returned “backup schedule creation is not enabled for this project” when daily retained snapshots were requested. Scheduled backups are therefore NOT configured. Repeat the manual snapshot and isolated restore before production migrations. Provider snapshots share the provider failure domain and are not an independent off-provider backup. Off-provider encrypted backup storage and a recurring job remain unconfigured until a destination and credentials are available.

## Staging boundary

Staging uses a separate Neon branch and a fresh database named `dsr_staging`, not its inherited production database. `DSR_ENVIRONMENT=staging` refuses unsafe database names before migrations. Only synthetic DEMO fixtures are seeded; staging rejects all mutations and carries a persistent read-only banner. Use branch `staging` for staging deployment and promote the tested commit to `main` after CI and staging checks.

## Measurement definitions

* Preparation: operator explicitly selects Start preparation; the same server transaction that marks Ready closes the cycle. This is elapsed calendar time including pauses, not hands-on labour hours. Imported history does not create timed samples.
* Investigation: operator-reported engineering minutes, linked to an evidence description. It is not a browser dwell-time timer.
* Spare shortages: reported incidents and optional observed delay. Current stock below minimum is a separate snapshot exposure; zero logged incidents does not mean zero actual incidents.
* Record completeness: installation attribution and, for closed campaigns, removal actor and removal reason. This does not verify imported physical history.
* Runtime: recorded RUNNING/STOPPED intervals. An eight-hour confirmation target prompts each-shift checks; confirmations do not backfill prior runtime or infer downtime.
* Estimates: admin-entered historical average with sample count, completed period and source. Baseline minus observed current average is explicitly an estimate. Negative reduction is retained. No monetary savings are invented.

## Release and recovery procedure

1. Run unit, client, PostgreSQL migration/concurrency, normal/static build and proxy checks.
2. Snapshot the production branch before the migration; restore into a new branch with `finalize=false`, never over production.
3. Compare table counts and deterministic content fingerprints. Record the snapshot and verification time.
4. Deploy and verify the exact candidate on synthetic staging. Test mobile drill-down, navigation history, empty states and read-only rejection.
5. Promote the tested commit to production. Verify `/ready`, real dashboard data and the new measurement routes. Do not create fabricated plant transactions for smoke testing.
