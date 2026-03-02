# Django Project Setup Implementation Plan

## Document Information

| Project | Description |
|---------|-------------|
| Plan Version | v1.0 |
| Created Date | 2026-01-17 |
| Target | Django 5.0 + DRF Project Initialization |
| Estimated Duration | 2-3 hours |

---

## Overview

This plan sets up the foundational Django project structure for GZEAMS (固定资产管理系统) following the architecture:
- Django 5.0 with Django REST Framework
- PostgreSQL with JSONB support
- Modular apps structure under `backend/apps/`
- Docker Compose for containerization
- Celery for async tasks

---

## Prerequisites

- Docker and Docker Compose installed
- Python 3.11+ installed locally
- Git initialized

---

## Directory Structure

```
NEWSEAMS/
├── backend/
│   ├── config/                 # Project settings
│   │   ├── __init__.py
│   │   ├── settings/
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # Base settings
│   │   │   ├── development.py  # Dev settings
│   │   │   ├── production.py   # Prod settings
│   │   │   └── test.py         # Test settings
│   │   ├── urls.py             # Root URL config
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── apps/                   # All Django apps
│   │   ├── __init__.py
│   │   ├── common/             # Common base classes
│   │   ├── organizations/      # Multi-org module
│   │   ├── accounts/           # User & auth
│   │   └── assets/             # Asset management
│   ├── manage.py
│   └── requirements/
│       ├── base.txt
│       ├── development.txt
│       └── production.txt
├── frontend/                   # Vue3 frontend
├── docker-compose.yml
├── Dockerfile.backend
├── .env.example
└── .gitignore
```

---

## Implementation Tasks

### Task 1: Create Project Structure

```bash
# Create main directories
mkdir -p backend/config/settings backend/requirements backend/apps
mkdir -p frontend

# Create app directories
cd backend/apps
mkdir -p common/{models,serializers,viewsets,filters,services,handlers,utils}
mkdir -p organizations
mkdir -p accounts
mkdir -p assets/{models,serializers,viewsets,filters,services,tests}
mkdir -p workflows
mkdir -p inventory
mkdir -p system
mkdir -p sso

# Create __init__.py files
find . -type d -exec touch {}/__init__.py \;
```

**Commit**: `chore: create Django project directory structure`

---

### Task 2: Create Requirements Files

**File**: `backend/requirements/base.txt`

```txt
# Django Core
Django==5.0.1
djangorestframework==3.14.0
django-cors-headers==4.3.1

# Database
psycopg2-binary==2.9.9
dj-database-url==2.1.0

# Authentication
djangorestframework-simplejwt==5.3.1

# Celery
celery==5.3.6
redis==5.0.1
django-redis==5.4.0

# Utilities
python-decouple==3.8
python-dotenv==1.0.0
pytz==2023.3

# Validation
django-filter==23.5
marshmallow==3.20.1

# Monitoring
django-prometheus==2.3.1

# DRF Extensions
drf-spectacular==0.27.0
```

**File**: `backend/requirements/development.txt`

```txt
-r base.txt

# Development Tools
django-debug-toolbar==4.2.0
ipython==8.19.0
django-extensions==3.2.3

# Testing
pytest==7.4.3
pytest-django==4.7.0
pytest-cov==4.1.0
factory-boy==3.3.0
faker==20.1.0

# Code Quality
black==23.12.1
flake8==7.0.0
isort==5.13.2
mypy==1.7.1
```

**File**: `backend/requirements/production.txt`

```txt
-r base.txt

gunicorn==21.2.0
sentry-sdk==1.39.1
```

**Commit**: `chore: create Python requirements files`

---

### Task 3: Create Django Settings

**File**: `backend/config/settings/base.py`

```python
"""
Base Django settings for GZEAMS project.
"""
import os
from pathlib import Path
from datetime import timedelta
import dj_database_url

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Security
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
]

LOCAL_APPS = [
    'apps.common',
    'apps.organizations',
    'apps.accounts',
    'apps.assets',
    'apps.workflows',
    'apps.inventory',
    'apps.system',
    'apps.sso',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.common.middleware.OrganizationMiddleware',  # Custom org middleware
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/gzeams'),
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'EXCEPTION_HANDLER': 'apps.common.handlers.exceptions.custom_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# CORS Settings
CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:5173,http://127.0.0.1:5173'
).split(',')
CORS_ALLOW_CREDENTIALS = True

# Redis Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://redis:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'gzeams',
    }
}

# Celery Configuration
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://redis:6379/1')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://redis:6379/2')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# drf-spectacular (OpenAPI)
SPECTACULAR_SETTINGS = {
    'TITLE': 'GZEAMS API',
    'DESCRIPTION': 'Hook Fixed Assets Management System API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SCHEMA_PATH_PREFIX': '/api',
}
```

**File**: `backend/config/settings/development.py`

```python
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Show emails in console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Additional dev middleware
if DEBUG:
    INSTALLED_APPS.append('django_extensions')
    INSTALLED_APPS.append('debug_toolbar')
    MIDDLEWARE.append('debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1']

# Disable SSL requirements in dev
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
```

**File**: `backend/config/settings/production.py`

```python
from .base import *

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
```

**File**: `backend/config/settings/test.py`

```python
from .base import *

DEBUG = True

# Use in-memory database for tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable celery for tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Faster password hashing
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]
```

**Commit**: `feat(config): create Django settings`

---

### Task 4: Create manage.py

**File**: `backend/manage.py`

```python
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
```

**Commit**: `chore: create manage.py`

---

### Task 5: Create URL Configuration

**File**: `backend/config/urls.py`

```python
"""
URL configuration for GZEAMS project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API docs
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API endpoints (apps will register here)
    path('api/auth/', include('apps.accounts.urls')),
    path('api/organizations/', include('apps.organizations.urls')),
    path('api/assets/', include('apps.assets.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom admin site config
admin.site.site_header = 'GZEAMS Administration'
admin.site.site_title = 'GZEAMS Admin Portal'
admin.site.index_title = 'Welcome to GZEAMS'
```

**Commit**: `feat(config): create root URL configuration`

---

### Task 6: Create WSGI/ASGI

**File**: `backend/config/wsgi.py`

```python
"""
WSGI config for GZEAMS project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
application = get_wsgi_application()
```

**File**: `backend/config/asgi.py`

```python
"""
ASGI config for GZEAMS project.
"""
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
application = get_asgi_application()
```

**Commit**: `feat(config): create WSGI/ASGI configs`

---

### Task 7: Create Organization Middleware

**File**: `backend/apps/common/middleware.py`

```python
"""
Custom middleware for GZEAMS.
"""
from django.utils.deprecation import MiddlewareMixin
from rest_framework.exceptions import PermissionDenied


class OrganizationMiddleware(MiddlewareMiddleware):
    """
    Extract organization_id from request headers and attach to request.

    Expects: X-Organization-ID header
    Sets: request.organization_id
    """

    def process_request(self, request):
        """Extract organization ID from headers."""
        org_id = request.headers.get('X-Organization-ID') or request.COOKIES.get('organization_id')

        if org_id:
            try:
                request.organization_id = org_id
            except (ValueError, TypeError):
                raise PermissionDenied('Invalid organization ID format')
        else:
            request.organization_id = None

        return None
```

**Commit**: `feat(common): create organization middleware`

---

### Task 8: Create Docker Configuration

**File**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    container_name: gzeams-postgres
    environment:
      POSTGRES_DB: gzeams
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: gzeams-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: gzeams-backend
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - ./backend:/app
      - static_files:/app/staticfiles
      - media_files:/app/media
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/gzeams
      - REDIS_URL=redis://redis:6379/0

  celery_worker:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: gzeams-celery
    command: celery -A config worker -l info
    volumes:
      - ./backend:/app
    env_file:
      - .env
    depends_on:
      - db
      - redis
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/gzeams
      - REDIS_URL=redis://redis:6379/0

  celery_beat:
    build:
      context: .
      dockerfile: Dockerfile.backend
    container_name: gzeams-celery-beat
    command: celery -A config beat -l info
    volumes:
      - ./backend:/app
    env_file:
      - .env
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
  redis_data:
  static_files:
  media_files:
```

**File**: `Dockerfile.backend`

```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements /app/requirements
RUN pip install --upgrade pip && \
    pip install -r requirements/development.txt

# Copy application
COPY backend /app

# Create logs directory
RUN mkdir -p /app/logs

# Run migrations on start
COPY docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0", "8000"]
```

**File**: `docker-entrypoint.sh`

```bash
#!/bin/bash
set -e

echo "Waiting for database..."
while ! pg_isready -h db -U postgres; do
    sleep 1
done

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting GZEAMS..."
exec "$@"
```

**File**: `.env.example`

```env
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/gzeams

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

**File**: `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.venv

# Django
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal
/media
/staticfiles
/.coverage
/htmlcov/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Testing
.pytest_cache/
.coverage
htmlcov/

# Docker
docker-compose.override.yml
```

**Commit**: `feat(docker): add Docker Compose configuration`

---

### Task 9: Create Celery Configuration

**File**: `backend/config/celery.py`

```python
"""
Celery configuration for GZEAMS.
"""
import os
from celery import Celery

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('gzeams')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery."""
    print(f'Request: {self.request!r}')
```

**File**: `backend/config/__init__.py`

```python
# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app

__all__ = ('celery_app',)
```

**Commit**: `feat(celery): add Celery configuration`

---

### Task 10: Create Initial App Placeholders

**File**: `backend/apps/common/models.py`

```python
"""
Common base models - placeholder.
Will be implemented in common base classes plan.
"""
pass
```

**File**: `backend/apps/accounts/models.py`

```python
"""
User and authentication models - placeholder.
"""
from django.contrib.auth.models import AbstractUser
from apps.common.models import BaseModel


class User(AbstractUser, BaseModel):
    """
    Custom User model extending Django's AbstractUser.

    Adds organization support via BaseModel inheritance.
    """
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
```

**File**: `backend/apps/organizations/models.py`

```python
"""
Organization models - placeholder.
"""
from apps.common.models import BaseModel


class Organization(BaseModel):
    """
    Organization model for multi-tenant support.
    """
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'organizations'
```

**File**: `backend/apps/assets/models.py`

```python
"""
Asset models - placeholder.
"""
pass
```

**Commit**: `feat(apps): create initial model placeholders`

---

### Task 11: Verify Setup

```bash
# Start services
docker-compose up -d

# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser

# Check logs
docker-compose logs -f backend

# Access admin
# http://localhost:8000/admin/

# Access API docs
# http://localhost:8000/api/docs/
```

**Commit**: `chore: verify Django project setup`

---

## Definition of Done

- [ ] All directories created with `__init__.py` files
- [ ] Requirements files created (base, dev, prod)
- [ ] Settings files created (base, dev, prod, test)
- [ ] Docker Compose starts successfully
- [ ] Database connection works
- [ ] Redis connection works
- [ ] Migrations run successfully
- [ ] Admin panel accessible
- [ ] API docs accessible
- [ ] Celery worker runs

---

## Next Steps

1. Implement Common Base Classes (see `2025-01-17-common-base-classes-implementation.md`)
2. Implement Organizations Module
3. Implement Accounts/User Module
4. Implement Assets Module (Phase 1.1)

---

**Plan Version**: v1.0
**Created**: 2026-01-17
**Author**: GZEAMS Development Team
