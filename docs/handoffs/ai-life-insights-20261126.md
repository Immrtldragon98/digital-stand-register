# AI life insights handoff — 26 November 2026

## Scope and behavior

The stand assistant previously routed a few frontend regexes to canned text and
could not answer longest-current-installation or comparative completed life.
This branch adds a public read-only `POST /api/v1/intelligence/ask` with a bounded
`{question}` input. The response is `{answer,intent,evidence,limitations,provider,
as_of}`; `provider` is honestly `deterministic`, requiring no API key or paid model.

Supported intents: oldest/current longest installation; longest measured runtime
among fully covered campaigns (with global uncertainty if other campaigns are
unknown); completed stand performance; weaker position screening; recorded-reason
investigation; historical spare usage. Natural wording includes “more time”,
“longer”, “better life”, “weak/weaks”, and WHY plus a line/position. Future W4+
and recorded nonnumeric line names are supported. “Longest life” without ongoing
wording means completed comparison, not current age.

## Evidence boundaries

- Uses the domain agent's shared `LifeInsightService`,
  `dedupe_completed_campaigns`, and `completed_comparisons` helpers.
- Complete measured registered campaigns are preferred when adequately supported;
  inferred snapshot elapsed days remain a separately labelled fallback.
- Ongoing, inconsistent, future, duplicate/conflicting imported campaigns do not
  enter completed averages. The shared helper determines exclusions consistently.
- Target/peer cohorts each need at least three completed campaigns. Stand peers
  are other stand codes on the same line and position. Position peers are other
  lines at the same numbered position, a screening assumption, not proven duty
  equivalence. The target cohort is excluded from its peer baseline.
- Insufficient samples show available average/median/sample counts instead of
  unsupported “better” or “weak” verdicts. No prediction of remaining life.
- WHY retrieves scoped recorded reasons and recent linked campaign events;
  these are not represented as verified root causes. Missing process observations
  is explicitly disclosed. No component-failure cause is invented.
- Investigation `downtime_minutes` now sums only STOPPAGE events, excluding other
  observation durations. These remain entered durations, not runtime integration.

## Validation

12 focused tests passed, including shared deduplication and independent-peer
minimums, elapsed versus measured ranking, incomplete coverage, sparse samples,
measured-unit preference, future line names, WHY precedence, bounded questions,
and a real in-memory database /ask call proving read-only behavior and no fake
zero runtime. Investigation test excludes LOW observation minutes from downtime.

Earlier baseline full run passed 50 tests with 11 PostgreSQL tests skipped before
shared domain helper integration. Root must run integrated full checks including
PostgreSQL and HTTP routes after merging domain/frontend branches.

## Integration

Requires the domain branch's `life_insight_service.py` and updated
`runtime_service.py`; those were copied locally only to exercise integration and
are not part of this branch's owned commit. Frontend agent owns the Ask UI and
life insight cards. No deployment or production stand operation was performed.

## Known limits

This is deterministic decision support, not an LLM chat or autonomous failure
analyst. History still uses at most the latest 20,000 rows per evidence stream;
truncation is disclosed. Unsupported questions get suggested supported questions.
Observed longer campaign duration is not proof of superior reliability. No
statistical-significance claim is made from the minimum sample threshold.
