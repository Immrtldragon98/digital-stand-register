#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../backend"
: "${DSR_TEST_DATABASE_URL:?Set a disposable PostgreSQL database URL whose database name ends in _test}"
python -m pytest -q tests/postgres "$@"
