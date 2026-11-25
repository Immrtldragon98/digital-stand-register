# Domain handover — connector-only recovery

Base: d572c98ef4453ea3942b8291286730276228da98. Source was read through GitHub; local execution unavailable. Do not claim tests passed until CI runs this commit.

- Legacy stand/guide lifetime zero is not certified as known historical zero. Total lifetime remains unknown; measured_lifetime_hours and measured_history_complete expose the recorded ledger only.
- Actual RUNNING intervals use prefix sums and binary lookup; planned monthly PM never subtracts invented hours.
- Runtime corrections retain line lock then event refresh and now reject whitespace-only reasons. Public history exposes event_count/history_truncated.
- Component preparation/list preloads asset fitting histories; fallback recognizes a later uncached identity instead of hiding it.
- Missing preparation blocks Gauging. Explicit SKIPPED preparation requires a real reason; finalized preparations cannot deduct stock twice.
- POST /stands/{stand_id}/components/return with reason is an operator current action only on nonrunning stands. It releases fittings, retains REUSED identities/history, resets readiness to Pending/WIP, rejects no active fittings, and never increases NEW stock. Asset-before-fitting lock order matches finalization.
- Guide condition corrections require admin.
- Added eight domain-boundary tests including actual8h vs10h elapsed, unknown prior lifetime, two-stand reuse, no partial issues for unknown/insufficient stock, one-time finalization, missing-prep/skip and cache safety.

Remaining verification: run Python unit+real PostgreSQL suite and frontend contracts on integrated final tree; independent PM approval before main publication. No schema migration or historical plant-data edits added by this domain patch.
