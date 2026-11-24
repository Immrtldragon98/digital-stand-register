FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.lock ./requirements.lock
RUN pip install --no-cache-dir -r requirements.lock

COPY backend/ .
# Keep the Alembic migration directory explicit so the database revisions
# required by the live database are always present in the runtime image.
COPY backend/alembic/versions/ /app/alembic/versions/

RUN test -f /app/alembic/versions/20260913_pm_activity_log.py \
    && chmod +x /app/docker-entrypoint.sh

RUN python -m compileall -q app scripts \
    && python -m pytest -q --ignore=tests/postgres

EXPOSE 8000
ENTRYPOINT ["/app/docker-entrypoint.sh"]
