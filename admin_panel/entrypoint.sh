#!/bin/bash

echo "🔄 Running database migrations..."
python manage.py migrate --noinput

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput || true

echo "🚀 Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 --workers 3 dxv_admin.wsgi:application
