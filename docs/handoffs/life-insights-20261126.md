# Runtime and campaign-life domain handoff

## Problem and scope
A stand with no mill-state observations exposed `known_runtime_hours: 0`; the UI rendered that lower bound as 0 h despite a long installation. Calendar installation age is not actual running life. No historical elapsed estimate is now substituted into measured runtime, targets or spare-life calculations.

## Contract
`RuntimeService.measure` retains internal numeric `known_hours` for safe accumulation and adds `has_coverage`, `coverage_status` (NONE/PARTIAL/COMPLETE), `observed_from`, and `covered_elapsed_hours`. API dashboard, stand history/detail, guide history, component and planning serializers expose absent observation coverage as null. A completely observed STOPPED interval still exposes actual zero. Partial observed zero remains distinguishable from no observation. Legacy initial lifetime remains uncertified.

Public `GET /api/v1/intelligence/life-insights` returns:
- `ongoing`, `longest_current_installation` (calendar age) and `longest_current_measured` (complete observed actual runtime only).
- `historical_stand_performance` and `weak_positions`, inferred snapshot elapsed-day cohorts.
- `measured_completed_stand_performance` and `measured_weak_positions`, separately measured-hour cohorts from completed registered stand installations.
- Counts, exclusions, independent-peer sample sizes, evidence sufficiency, truncation flags and methodology notes.

Stand peers are other stand IDs at the same line/position. Position peers are other lines at the same position number. The latter is screening under unverified equivalent duty, not confirmed identical operating conditions. Target and peer each require at least three completed campaigns before a ratio/ranking is supported. Ongoing campaigns are right-censored and excluded from all completed averages. New completed registered records are included dynamically instead of freezing analytics at spreadsheet import.

Snapshot duplicates use line/position/stand/installed-date identity across source files. Conflicting duplicate outcomes, open campaigns, non-finite or non-positive values, invalid/future dates and elapsed-day/date mismatches are excluded. Plant-day validation uses Asia/Kolkata.

## Validation
Full backend suite: 48 passed, 11 PostgreSQL-only skipped in the unit-test runtime. Nine new tests verify no-event unknown, complete zero, partial observed zero, stopped boundaries, distinct ongoing rankings, snapshot deduplication/conflicts/mismatches, India date, independent context cohorts and measured registered completed comparisons separated from inferred days. `git diff --check` and compileall passed.

## Practical limits
No invented historical runtime, automatic 24/7 baseline, fixed 12-hour deduction, remaining-life prediction, or causal reliability claim. Historical/registered windows bounded at 20,000 rows, ongoing/context windows at 1,000, ranking lists at 200 with explicit truncation flags. RuntimeService itself retains its existing all-event prefix index loading; it is not a database retention policy. Administrative runtime backfills/corrections recompute observations on subsequent reads. A three-sample threshold signals minimum evidence, not statistical significance or confidence intervals.
