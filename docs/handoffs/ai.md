# AI engineer handover — remote recovery
## Implemented and audited
- PM message confirmation records reviewed PM history only. It has no OperationService import or hidden stand/stock write; no absent date is invented by its fallback.
- PM edits/deletes and backdated entries are admin-only; completed future records are rejected. Input text fields and action batches are bounded.
- Report actions are typed, finite-confidence proposals. Zero confidence requires review. Confirmed selected actions must all validate SAFE and commit atomically through run_command/OperationService(auto_commit=False); any later execution failure rolls back the entire batch and receipt.
- Report timestamps without offsets are explicitly Asia/Kolkata, not assumed UTC or midnight.
- Provider diagnostics expose exception class/status, not provider response bodies or untrusted content.
- Knowledge uploads read at most12MB+1 and limit archive expansion, text, rows and PDF pages. Worker extraction avoids blocking the async loop; malformed files produce400 and duplicate concurrent insertion409.
- Both analytics endpoints bound recent evidence to20,000 rows/stream, disclose truncation and identify life as inferred snapshot elapsed days, not measured mill runtime. Dynamic lines supported. Merged date intervals avoid constructing century-long daily sets.
## Verification
Nine new boundary tests are committed for GitHub CI, including history-only PM/idempotent replay, invalid-batch rollback, confidence0/NaN rejection, report later-execution rollback, plant timezone, archive/text bounds and bounded evidence intervals. No local runtime was available, so execution evidence must come from the branch CI and integrated release CI.
## Capability limits
Optional Gemini JSON extraction + deterministic templates + keyword document search + rule/statistical screening; not a trained predictive-maintenance model or proven causal/root-cause engine. Historical snapshots remain inferred. Provider free-tier availability is external. Bounded parsers are not malware sandboxing. Offline mutations are not replayed by AI.
