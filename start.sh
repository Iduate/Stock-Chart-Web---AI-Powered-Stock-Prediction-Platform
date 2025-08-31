#!/bin/bash

# Set Django settings module for production
export DJANGO_SETTINGS_MODULE=stockchart_project.settings_production

# Run database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist (optional, for production)
# python manage.py shell -c "
# from django.contrib.auth import get_user_model
# User = get_user_model()
# if not User.objects.filter(email='admin@stockchart.com').exists():
#     User.objects.create_superuser(email='admin@stockchart.com', password='your_secure_password')
# "

# Start the application
exec gunicorn stockchart_project.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120
