#!/bin/bash

echo "🚀 Simple Railway startup..."

# Basic environment check
echo "PORT: $PORT"
echo "PGDATABASE: $PGDATABASE"

# Apply migrations (basic)
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

echo "🔄 Applying migrations..."
python manage.py migrate --noinput

# Start with minimal Gunicorn config
echo "🌟 Starting server..."
exec gunicorn stockchart_project.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 1 \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
