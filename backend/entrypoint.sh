#!/bin/bash

set -e

echo "Applying database migrations via Alembic..."
alembic upgrade head

echo "Executing test suite..."
pytest

echo "Starting Uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 5000 --workers 1