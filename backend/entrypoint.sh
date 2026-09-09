#!/usr/bin/env sh
# Apply DB migrations, then start the API server. [RES-04]
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
