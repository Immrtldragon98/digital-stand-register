# Bugs and suggestions

Open **Bugs & Suggestions** in the main navigation (inside the menu on mobile). Choose Bug or Suggestion, enter a short title and details, and submit. A reporter name and app page are optional. No account is required to submit.

The app shows a reference such as `FB-000001` after the server acknowledges receipt. A local draft is retained when offline. Uncertain submissions preserve their request UUID and can be retried without duplicating the report. Drafts never submit automatically. Clearing a local draft does not delete a server report.

Admins use the same page's private inbox to filter by type/status, write review notes, and mark reports Open, In progress, Resolved or Declined. Report content and review notes are not publicly readable; reporter names are self-reported.

Public submissions are text-only and bounded. The affected page strips query strings/fragments. The server stores a keyed hash of the peer address rather than a raw IP and limits new submissions to 20 per connection per hour. Existing retry receipts remain recoverable after that limit. No automatic email, GitHub issue, external AI call or plant-data mutation is triggered by a report.

Migration: `20261126_feedback_reports`, after `20261124_command_receipts`. Tests cover real API role enforcement, receipt recovery, validation, rate limits, draft restoration and concurrent PostgreSQL retries.
