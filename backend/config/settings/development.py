from .base import *
import os

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Detect if running in Docker environment
# Use PostgreSQL if DATABASE_URL is set (Docker), otherwise use SQLite (local dev)
if os.getenv('DATABASE_URL'):
    # Running in Docker - use PostgreSQL from DATABASE_URL
    # Don't override DATABASES from base.py which uses dj_database_url
    pass
else:
    # Local development without Docker - use SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Show emails in console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Additional dev middleware
if DEBUG:
    INSTALLED_APPS.append('django_extensions')
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']

    # Configure debug toolbar to skip API requests
    DEBUG_TOOLBAR_CONFIG = {
        'SKIP_TEMPLATE_CALLBACKS': True,
        'ENABLE_STACKTRACES': False,
        # Show toolbar only for non-API requests
        'SHOW_TOOLBAR_CALLBACK': lambda request: not request.path.startswith('/api/'),
    }

# Disable SSL requirements in dev
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
