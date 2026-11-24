# Availability and offline dashboard

The preferred frontend is https://digital-stand-register-app.onrender.com/dashboard/
(Render Static Site `srv-dc2k5qui0phs73b3stn0`, auto-deploying `main`).
The original Node website is retained for existing bookmarks.

The static site is built with:

    cd frontend && npm ci --include=dev && npm run test:api && npm run build:static

Publish `frontend/out`; set `NEXT_PUBLIC_API_URL` to the HTTPS API URL ending in `/api/v1`.
The API must allow the exact static site's origin in `CORS_ORIGINS`. Keep that value
in the API Blueprint configuration as well as Render's environment settings.
The existing Node frontend and its same-origin proxy remain compatible.

The static CDN removes the frontend's idle spin-down. The free Render API can still
sleep after inactivity; Neon can also suspend idle compute. First-time visitors
need a successful API response before any dashboard data is available. No free
hosting setup here guarantees uninterrupted live writes or an uptime SLA.

After a successful dashboard read, the browser saves a timestamped, API-scoped
copy. Failed reads keep that copy visible and label it as old. Reconnection runs
with bounded delays and reacts to online/visibility events. A successful refresh
updates the original sync time; a failed refresh never does. The initial running
count is unknown, never a fabricated zero. Browser storage can be cleared or
unavailable, so this is a convenience copy, not a database backup.

Static builds precache public exported HTML, route payloads, scripts and images
in a versioned service-worker cache. After installation and a subsequent visit,
the interface can reopen offline. API requests, authentication and all writes
bypass that cache. Service-worker updates wait for older tabs to close to avoid
mixing bundles across releases. Other screens still require live data.

Stand changes always preflight fresh running positions and replacement readiness.
No write is automatically replayed. If saving cannot be confirmed, check current
stands before submitting again. Existing mill data, accounts and history remain
in the original API and database; changing frontend origins requires signing in
again because browser sessions and local snapshots are scoped to an origin.

Verification: `npm run test:api`, `npm run build`, `npm run test:proxy`, then
`NEXT_PUBLIC_API_URL=https://your-api/api/v1 npm run build:static` in `frontend`.
