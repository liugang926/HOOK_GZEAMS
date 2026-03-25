#!/bin/bash
set -e

should_prepare_runtime=false
if [ "$1" = "python" ] && [ "$2" = "manage.py" ] && [ "$3" = "runserver" ]; then
    should_prepare_runtime=true
fi
if [ "$1" = "gunicorn" ]; then
    should_prepare_runtime=true
fi

echo "Waiting for database..."
db_host="${POSTGRES_HOST:-db}"
db_user="${POSTGRES_USER:-postgres}"
db_name="${POSTGRES_DB:-gzeams}"

while ! pg_isready -h "$db_host" -U "$db_user" -d "$db_name"; do
    sleep 1
done

if [ "$should_prepare_runtime" = true ]; then
    echo "Running migrations..."
    python manage.py migrate --noinput

    if [ "${BOOTSTRAP_DEFAULTS_ON_STARTUP:-1}" = "1" ]; then
        echo "Bootstrapping runtime defaults..."
        python manage.py bootstrap_defaults
    fi

    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

echo "Starting GZEAMS..."
exec "$@"
