#!/bin/sh
set -eu

if [ "${DSR_ENVIRONMENT:-production}" = "staging" ]; then
    python scripts/staging_fixture.py --validate-only
fi

echo "Applying database migrations..."
alembic upgrade head

if [ "${DSR_ENVIRONMENT:-production}" = "staging" ]; then
    python scripts/staging_fixture.py
fi

echo "Starting Digital Stand Register API..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
