#!/usr/bin/env bash
# Railway/Docker start script: static collect + migrate + (optional admin) + gunicorn
set -o errexit

python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Optional admin user (Variables me DJANGO_SUPERUSER_USERNAME / _PASSWORD set ho tabhi)
if [[ -n "${DJANGO_SUPERUSER_USERNAME:-}" && -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]]; then
  python manage.py createsuperuser --no-input --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" || true
fi

exec gunicorn farming.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers "${WEB_CONCURRENCY:-2}" --timeout 60 --access-logfile -
