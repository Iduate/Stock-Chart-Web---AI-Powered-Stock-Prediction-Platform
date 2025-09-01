#!/bin/bash

# Railway startup script for Django
echo "🚀 Starting Railway deployment..."

# Wait a bit for database to be ready
echo "⏳ Waiting for database connection..."
sleep 5

# Check if we're in Railway environment
if [ "$RAILWAY_ENVIRONMENT" = "true" ] || [ -n "$RAILWAY_ENVIRONMENT_NAME" ]; then
    echo "🌐 Detected Railway environment"
    export DEBUG=false
    
    # Check database connection
    if [ -n "$PGDATABASE" ]; then
        echo "📊 PostgreSQL database detected: $PGDATABASE"
    else
        echo "⚠️  No PostgreSQL detected, will use SQLite fallback"
    fi
fi

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput --verbosity 0

# Apply database migrations
echo "🔄 Applying database migrations..."
python manage.py migrate --noinput --verbosity 1

# Create superuser if it doesn't exist (optional)
echo "👤 Checking for superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(is_superuser=True).exists():
    print('Creating superuser...');
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123');
    print('Superuser created: admin / admin123');
else:
    print('Superuser already exists');
" 2>/dev/null || echo "Superuser creation skipped"

# Start the application
echo "🌟 Starting Gunicorn server..."
exec gunicorn stockchart_project.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --keep-alive 2 \
    --max-requests 1000 \
    --preload \
    --log-level info \
    --access-logfile - \
    --error-logfile -
