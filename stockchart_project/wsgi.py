"""
WSGI config for stockchart_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys

# Print diagnostic information
print("Python version:", sys.version)
print("Current directory:", os.getcwd())
print("PYTHONPATH:", sys.path)

# Ensure environment variables are set
if 'RAILWAY_ENVIRONMENT' not in os.environ:
    print("Setting RAILWAY_ENVIRONMENT=True")
    os.environ['RAILWAY_ENVIRONMENT'] = 'True'

# Set PORT if not already set
if 'PORT' not in os.environ:
    print("Setting default PORT=8000")
    os.environ['PORT'] = '8000'

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockchart_project.settings')

# Print settings module path
print("Django settings module:", os.environ.get('DJANGO_SETTINGS_MODULE'))

try:
    application = get_wsgi_application()
    print("WSGI application initialized successfully")
except Exception as e:
    print("Error initializing WSGI application:", str(e))
    raise
