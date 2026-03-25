from .base import *
import os
import dj_database_url

DEBUG = True

# Use PostgreSQL for tests.
# Supports local overrides while keeping container defaults:
# - TEST_DATABASE_URL
# - TEST_DB_NAME / TEST_DB_USER / TEST_DB_PASSWORD / TEST_DB_HOST / TEST_DB_PORT
test_database_url = os.getenv('TEST_DATABASE_URL', '').strip()
if test_database_url:
    parsed_test_db = dj_database_url.parse(test_database_url, conn_max_age=0)
    parsed_test_db['ATOMIC_REQUESTS'] = False
    DATABASES = {'default': parsed_test_db}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('TEST_DB_NAME', 'gzeams_test'),
            'USER': os.getenv('TEST_DB_USER', 'postgres'),
            'PASSWORD': os.getenv('TEST_DB_PASSWORD', 'postgres'),
            'HOST': os.getenv('TEST_DB_HOST', 'db'),
            'PORT': os.getenv('TEST_DB_PORT', '5432'),
            'ATOMIC_REQUESTS': False,
        }
    }

# Add testserver for API tests
ALLOWED_HOSTS = list(ALLOWED_HOSTS) + ['testserver', 'localhost', '127.0.0.1']

# Use in-memory cache for tests (no Redis required)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    }
}

# Disable celery for tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Faster password hashing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Test-specific REST Framework settings
# Use BasicAuthentication for simpler testing (in addition to JWT)
REST_FRAMEWORK = {
    **dict(REST_FRAMEWORK),  # Inherit base settings
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',  # For testing
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'TEST_REQUEST_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# Disable CSRF for API tests
REST_FRAMEWORK['DEFAULT_SCHEMA_CLASS'] = 'rest_framework.schemas.coreapi.AutoSchema'
