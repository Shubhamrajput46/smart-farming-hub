#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate --no-input

# Optional: admin user (env me DJANGO_SUPERUSER_USERNAME / _EMAIL / _PASSWORD set ho tabhi)
if [[ -n "${DJANGO_SUPERUSER_USERNAME:-}" && -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]]; then
  python manage.py createsuperuser --no-input --email "${DJANGO_SUPERUSER_EMAIL:-admin@example.com}" || true
fi
