"""
Production settings for Railway deployment
"""
from .settings import *
import os

# Override DEBUG for production
DEBUG = False

# Railway automatically provides a PORT environment variable
ALLOWED_HOSTS = ['*']  # Railway handles the domain routing

# Database configuration for Railway PostgreSQL
# Railway provides individual database connection parameters
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('PGDATABASE', 'railway'),
        'USER': os.environ.get('PGUSER', 'postgres'),
        'PASSWORD': os.environ.get('PGPASSWORD', ''),
        'HOST': os.environ.get('PGHOST', 'localhost'),
        'PORT': os.environ.get('PGPORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
        },
    }
}

# Static files configuration for production
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Security settings for production
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Use Redis from Railway if available
redis_url = os.environ.get('REDIS_URL')
if redis_url:
    CELERY_BROKER_URL = redis_url
    CELERY_RESULT_BACKEND = redis_url
    
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': redis_url,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            },
            'TIMEOUT': CACHE_TIMEOUT_SECONDS,
        }
    }

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Logging configuration for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'stream': 'ext://sys.stdout',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'stockchart_project': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
