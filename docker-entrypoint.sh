#!/bin/bash
set -e

echo "Waiting for database..."
while ! pg_isready -h db -U postgres; do
    sleep 1
done

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting GZEAMS..."
exec "$@"
