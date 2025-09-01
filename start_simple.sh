#!/bin/bash

echo "🚀 Simple Railway startup..."

# Extended environment check
echo "---- Environment Variables ----"
echo "PORT: $PORT"
echo "PGDATABASE: $PGDATABASE"
echo "PGUSER: $PGUSER"
echo "PGHOST: $PGHOST"
echo "PGPORT: $PGPORT"
echo "RAILWAY_ENVIRONMENT: $RAILWAY_ENVIRONMENT"
echo "RAILWAY_ENVIRONMENT_NAME: $RAILWAY_ENVIRONMENT_NAME"
echo "-----------------------------"

# Check if PORT is set, use default if not
if [ -z "$PORT" ]; then
    echo "⚠️ PORT is not set, defaulting to 8000"
    export PORT=8000
fi

# Apply migrations (basic)
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

echo "🔄 Applying migrations..."
python manage.py migrate --noinput

# Start with enhanced Gunicorn config
echo "🌟 Starting server on port $PORT..."
exec gunicorn stockchart_project.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile - \
    --log-level debug \
    --capture-output
