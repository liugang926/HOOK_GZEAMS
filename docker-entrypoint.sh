#!/bin/bash
set -e

should_bootstrap_defaults=false
if [ "$1" = "python" ] && [ "$2" = "manage.py" ] && [ "$3" = "runserver" ]; then
    should_bootstrap_defaults=true
fi
if [ "$1" = "gunicorn" ]; then
    should_bootstrap_defaults=true
fi

echo "Waiting for database..."
while ! pg_isready -h db -U postgres; do
    sleep 1
done

echo "Running migrations..."
python manage.py migrate --noinput

if [ "${BOOTSTRAP_DEFAULTS_ON_STARTUP:-1}" = "1" ] && [ "$should_bootstrap_defaults" = true ]; then
    echo "Bootstrapping runtime defaults..."
    python manage.py bootstrap_defaults
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting GZEAMS..."
exec "$@"
