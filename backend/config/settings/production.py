from .base import *
from django.core.exceptions import ImproperlyConfigured
import os

DEBUG = False

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# Logging
LOGGING['handlers']['file']['filename'] = '/var/log/gzeams/django.log'

# Enforce strict CORS in production.
CORS_ALLOW_ALL_ORIGINS = False
if not CORS_ALLOWED_ORIGINS:
    raise ImproperlyConfigured(
        'CORS_ALLOWED_ORIGINS must be configured in production settings.'
    )

# Restrict health metrics endpoint to explicit IP/CIDR allowlist in production.
if not os.getenv('HEALTH_METRICS_ALLOWLIST'):
    raise ImproperlyConfigured(
        'HEALTH_METRICS_ALLOWLIST must be configured in production settings.'
    )

# Require token for metrics endpoint in production.
if not os.getenv('HEALTH_METRICS_TOKEN'):
    raise ImproperlyConfigured(
        'HEALTH_METRICS_TOKEN must be configured in production settings.'
    )
