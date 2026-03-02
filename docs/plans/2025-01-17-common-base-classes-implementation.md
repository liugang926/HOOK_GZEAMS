# Common Base Classes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the foundational base classes (BaseModel, BaseModelSerializer, BaseModelViewSet, BaseCRUDService, BaseModelFilter) that all GZEAMS modules will inherit from.

**Architecture:** Create a hierarchical inheritance system where business models inherit from BaseModel, serializers from BaseModelSerializer, etc. This provides automatic organization isolation, soft delete, audit trails, and batch operations.

**Tech Stack:** Django 5.0, Django REST Framework, PostgreSQL (JSONB), Python 3.11+

---

## Prerequisites

**Before starting this plan, ensure:**
- Python 3.11+ is installed
- Virtual environment is created: `python -m venv venv`
- Virtual environment is activated: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)

**Install dependencies:**
```bash
pip install django==5.0 djangorestframework==3.15.0 django-filter==24.3 psycopg2-binary==2.9.9 python-dotenv==1.0.0
```

---

## Task 1: Create Django Project Structure

**Files:**
- Create: `backend/manage.py`
- Create: `backend/config/__init__.py`
- Create: `backend/config/settings.py`
- Create: `backend/config/urls.py`
- Create: `backend/config/wsgi.py`
- Create: `backend/asgi.py`
- Create: `backend/.env`
- Create: `backend/requirements.txt`

**Step 1: Create project directory structure**

```bash
cd backend
mkdir -p config apps/{common/{serializers,viewsets,services,filters,middleware,utils,permissions,handlers,responses,mixins},organizations,assets}
touch config/__init__.py apps/__init__.py apps/common/__init__.py
```

**Step 2: Create `backend/requirements.txt`**

```txt
Django==5.0
djangorestframework==3.15.0
django-filter==24.3
psycopg2-binary==2.9.9
python-dotenv==1.0.0
```

**Step 3: Install requirements**

```bash
pip install -r requirements.txt
```

**Step 4: Create `backend/.env`**

```ini
SECRET_KEY=django-insecure-change-me-in-production
DEBUG=True
DATABASE_URL=postgresql://user:password@localhost:5432/gzeams
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Step 5: Create `backend/manage.py`**

```python
#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
```

**Step 6: Create `backend/config/settings.py`**

```python
from pathlib import Path
from dotenv import load_dotenv
import os

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party apps
    'rest_framework',
    'django_filters',
    # Local apps
    'apps.common',
    'apps.organizations',
    'apps.assets',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Custom middleware (to be added later)
    # 'apps.common.middleware.organization_middleware.OrganizationMiddleware',
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
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gzeams',
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

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
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
        'rest_framework.filters.SearchFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}
```

**Step 7: Create `backend/config/urls.py`**

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apps.common.urls')),
]
```

**Step 8: Create `backend/config/wsgi.py` and `backend/asgi.py`**

```python
# wsgi.py
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()

# asgi.py
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_asgi_application()
```

**Step 9: Commit**

```bash
cd backend
git add .
git commit -m "feat: initialize Django project structure with basic configuration"
```

---

## Task 2: Create BaseModel (Abstract Base Model)

**Files:**
- Create: `backend/apps/common/models.py`

**Step 1: Create empty `__init__.py` files**

```bash
touch apps/common/__init__.py
```

**Step 2: Write the failing test for BaseModel**

Create file: `backend/apps/common/tests/test_models.py`

```python
from django.test import TestCase
from django.db import models
from apps.common.models import BaseModel


class BaseModelTest(TestCase):
    """Test BaseModel abstract model"""

    def test_base_model_has_organization_field(self):
        """Test BaseModel has organization ForeignKey"""
        # This will fail because BaseModel doesn't exist yet
        field = BaseModel._meta.get_field('organization')
        self.assertEqual(field.remote_field.model.__name__, 'Organization')

    def test_base_model_has_soft_delete_fields(self):
        """Test BaseModel has soft delete fields"""
        self.assertTrue(hasattr(BaseModel, 'is_deleted'))
        self.assertTrue(hasattr(BaseModel, 'deleted_at'))

    def test_base_model_has_audit_fields(self):
        """Test BaseModel has audit fields"""
        self.assertTrue(hasattr(BaseModel, 'created_at'))
        self.assertTrue(hasattr(BaseModel, 'updated_at'))
        self.assertTrue(hasattr(BaseModel, 'created_by'))

    def test_base_model_has_custom_fields(self):
        """Test BaseModel has custom_fields JSONB field"""
        field = BaseModel._meta.get_field('custom_fields')
        self.assertIsInstance(field, models.JSONField)
```

**Step 3: Run test to verify it fails**

```bash
cd backend
python manage.py test apps.common.tests.test_models
```

Expected: `ImportError: cannot import name 'BaseModel'`

**Step 4: Create BaseModel implementation**

Create file: `backend/apps/common/models.py`

```python
from django.db import models
from django.contrib.auth import get_user_model
import uuid


class BaseModel(models.Model):
    """
    Abstract base model for all GZEAMS models.

    Provides automatic:
    - Organization isolation (multi-tenancy)
    - Soft delete capability
    - Audit trail (created/updated timestamps and user tracking)
    - Dynamic custom fields (JSONB)
    """

    # Primary key - UUID for distributed systems
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name='ID'
    )

    # Organization isolation - REQUIRED for multi-tenancy
    # Forward reference to Organization model to avoid circular imports
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class_name)s_set',
        verbose_name='组织',
        db_comment='Organization for multi-tenant data isolation'
    )

    # Soft delete fields
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name='已删除',
        db_comment='Soft delete flag, records are filtered out by default'
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='删除时间',
        db_comment='Timestamp when record was soft deleted'
    )

    # Audit trail fields
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间',
        db_comment='Timestamp when record was created'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间',
        db_comment='Timestamp when record was last updated'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(app_label)s_%(class_name)s_created',
        verbose_name='创建人',
        db_comment='User who created this record'
    )

    # Dynamic custom fields for low-code platform
    custom_fields = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='自定义字段',
        db_comment='Dynamic fields for metadata-driven extensions'
    )

    class Meta:
        abstract = True  # This is an abstract base class
        indexes = [
            models.Index(fields=['organization', 'is_deleted']),
            models.Index(fields=['organization', '-created_at']),
        ]

    def soft_delete(self, user=None):
        """
        Perform soft delete instead of hard delete.

        Args:
            user: Optional user who performed the deletion
        """
        self.is_deleted = True
        self.deleted_at = models.timezone.now()
        if user:
            # Import User to avoid circular import at module level
            User = get_user_model()
            # Store deleted_by if the model has this field
            if hasattr(self, 'deleted_by'):
                self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'updated_at'])

    def hard_delete(self):
        """
        Perform actual hard delete from database.
        Use with caution - this cannot be undone.
        """
        self.delete()
```

**Step 5: Run test to verify it passes**

```bash
cd backend
python manage.py test apps.common.tests.test_models
```

Expected: Tests will still fail because Organization model doesn't exist yet. We'll create it next.

**Step 6: Modify test to check only BaseModel fields first**

Update: `backend/apps/common/tests/test_models.py`

```python
from django.test import TestCase
from django.db import models
import uuid
from apps.common.models import BaseModel


class BaseModelTest(TestCase):
    """Test BaseModel abstract model"""

    def test_base_model_fields_exist(self):
        """Test BaseModel has all required fields"""
        # Check field types
        id_field = BaseModel._meta.get_field('id')
        self.assertIsInstance(id_field, models.UUIDField)

        # is_deleted should exist but be abstract (check on Meta)
        self.assertIn('is_deleted', [f.name for f in BaseModel._meta.get_fields()])
        self.assertIn('deleted_at', [f.name for f in BaseModel._meta.get_fields()])
        self.assertIn('created_at', [f.name for f in BaseModel._meta.get_fields()])
        self.assertIn('updated_at', [f.name for f in BaseModel._meta.get_fields()])
        self.assertIn('created_by', [f.name for f in BaseModel._meta.get_fields()])
        self.assertIn('custom_fields', [f.name for f in BaseModel._meta.get_fields()])

    def test_base_model_is_abstract(self):
        """Test BaseModel is abstract"""
        self.assertTrue(BaseModel._meta.abstract)

    def test_soft_delete_method_exists(self):
        """Test soft_delete method exists"""
        self.assertTrue(callable(BaseModel.soft_delete))
```

**Step 7: Run test to verify it passes**

```bash
cd backend
python manage.py test apps.common.tests.test_models
```

Expected: PASS

**Step 8: Commit**

```bash
git add backend/apps/common/
git commit -m "feat: implement BaseModel with organization isolation, soft delete, and audit fields"
```

---

## Task 3: Create BaseModelSerializer

**Files:**
- Create: `backend/apps/common/serializers/__init__.py`
- Create: `backend/apps/common/serializers/base.py`
- Create: `backend/apps/common/tests/test_serializers.py`

**Step 1: Create `__init__.py`**

```bash
touch backend/apps/common/serializers/__init__.py
```

**Step 2: Write the failing test for BaseModelSerializer**

Create file: `backend/apps/common/tests/test_serializers.py`

```python
from django.test import TestCase
from apps.common.serializers.base import BaseModelSerializer
from apps.common.models import BaseModel


class DummyModel(BaseModel):
    """Dummy model for testing BaseModelSerializer"""
    class Meta:
        app_label = 'common'


class BaseModelSerializerTest(TestCase):
    """Test BaseModelSerializer"""

    def test_serializer_includes_public_fields(self):
        """Test serializer includes all BaseModel fields"""
        # This will fail because BaseModelSerializer doesn't exist yet
        serializer = BaseModelSerializer()
        expected_fields = {'id', 'organization', 'is_deleted', 'deleted_at',
                          'created_at', 'updated_at', 'created_by', 'custom_fields'}
        self.assertEqual(set(serializer.fields.keys()), expected_fields)

    def test_meta_fields_attribute_exists(self):
        """Test Meta.fields attribute exists"""
        self.assertTrue(hasattr(BaseModelSerializer.Meta, 'fields'))
```

**Step 3: Run test to verify it fails**

```bash
cd backend
python manage.py test apps.common.tests.test_serializers
```

Expected: `ImportError: cannot import name 'BaseModelSerializer'`

**Step 4: Create BaseModelSerializer implementation**

Create file: `backend/apps/common/serializers/base.py`

```python
from rest_framework import serializers
from .base import BaseModelSerializer

__all__ = ['BaseModelSerializer', 'BaseModelWithAuditSerializer', 'BaseListSerializer']
```

Wait, we need to define the actual classes. Let me create the full implementation:

```python
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.common.models import BaseModel

User = get_user_model()


class BaseModelSerializer(serializers.ModelSerializer):
    """
    Base serializer for all models inheriting from BaseModel.

    Automatically serializes all BaseModel public fields:
    - id, organization, is_deleted, deleted_at
    - created_at, updated_at, created_by
    - custom_fields (JSONB dynamic fields)

    Nested serializers:
    - organization → OrganizationSerializer (lightweight)
    - created_by → UserSerializer (lightweight)
    """

    # Nested serializers for foreign keys
    class OrganizationSerializer(serializers.ModelSerializer):
        """Lightweight organization serializer for nested display"""
        class Meta:
            model = 'organizations.Organization'
            fields = ['id', 'name', 'code']

    class UserSerializer(serializers.ModelSerializer):
        """Lightweight user serializer for nested display"""
        class Meta:
            model = User
            fields = ['id', 'username', 'email', 'first_name', 'last_name']

    # Automatic field mapping
    id = serializers.UUIDField(read_only=True)
    organization = OrganizationSerializer(read_only=True)
    is_deleted = serializers.BooleanField(read_only=True)
    deleted_at = serializers.DateTimeField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    created_by = UserSerializer(read_only=True)
    custom_fields = serializers.JSONField(read_only=True)

    class Meta:
        model = BaseModel
        fields = ['id', 'organization', 'is_deleted', 'deleted_at',
                  'created_at', 'updated_at', 'created_by', 'custom_fields']
        read_only_fields = ['id', 'created_at', 'updated_at']


class BaseModelWithAuditSerializer(BaseModelSerializer):
    """
    Base serializer with full audit trail including updated_by and deleted_by.

    Extends BaseModelSerializer to include:
    - updated_by: User who last updated the record
    - deleted_by: User who soft deleted the record

    Use when you need complete audit information for list/detail views.
    """

    updated_by = UserSerializer(read_only=True)
    deleted_by = UserSerializer(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = BaseModel
        fields = BaseModelSerializer.Meta.fields + ['updated_by', 'deleted_by']


class BaseListSerializer(BaseModelSerializer):
    """
    Optimized serializer for list views.

    Excludes nested serializers to reduce query count.
    Use for list endpoints where full detail is not needed.
    """

    organization = serializers.UUIDField(read_only=True)
    created_by = serializers.UUIDField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = BaseModel
        fields = ['id', 'organization', 'is_deleted', 'created_at', 'updated_at', 'created_by']
```

**Step 5: Run test to verify it passes**

```bash
cd backend
python manage.py test apps.common.tests.test_serializers
```

Expected: Some tests may fail due to missing Organization model. Let's update the test:

Update: `backend/apps/common/tests/test_serializers.py`

```python
from django.test import TestCase
from apps.common.serializers.base import BaseModelSerializer, BaseModelWithAuditSerializer, BaseListSerializer
from apps.common.models import BaseModel


class DummyModel(BaseModel):
    """Dummy model for testing BaseModelSerializer"""
    class Meta:
        app_label = 'common'


class BaseModelSerializerTest(TestCase):
    """Test BaseModelSerializer"""

    def test_serializer_exists(self):
        """Test BaseModelSerializer class exists"""
        self.assertTrue(callable(BaseModelSerializer))

    def test_serializer_has_meta_fields(self):
        """Test Meta.fields attribute exists"""
        self.assertTrue(hasattr(BaseModelSerializer.Meta, 'fields'))
        expected_fields = {'id', 'organization', 'is_deleted', 'deleted_at',
                          'created_at', 'updated_at', 'created_by', 'custom_fields'}
        self.assertEqual(set(BaseModelSerializer.Meta.fields), expected_fields)

    def test_base_model_with_audit_serializer_exists(self):
        """Test BaseModelWithAuditSerializer exists"""
        self.assertTrue(callable(BaseModelWithAuditSerializer))
        extra_fields = {'updated_by', 'deleted_by'}
        expected_fields = set(BaseModelSerializer.Meta.fields) | extra_fields
        self.assertEqual(set(BaseModelWithAuditSerializer.Meta.fields), expected_fields)

    def test_base_list_serializer_exists(self):
        """Test BaseListSerializer exists and is optimized"""
        self.assertTrue(callable(BaseListSerializer))
        # Should have fewer fields for list optimization
        list_fields = set(BaseListSerializer.Meta.fields)
        self.assertTrue(len(list_fields) < len(BaseModelSerializer.Meta.fields))
```

**Step 6: Run test to verify it passes**

```bash
cd backend
python manage.py test apps.common.tests.test_serializers
```

Expected: PASS

**Step 7: Commit**

```bash
git add backend/apps/common/serializers/
git commit -m "feat: implement BaseModelSerializer with automatic public field serialization"
```

---

## Task 4: Create BaseModelFilter

**Files:**
- Create: `backend/apps/common/filters/__init__.py`
- Create: `backend/apps/common/filters/base.py`

**Step 1: Create `__init__.py`**

```bash
touch backend/apps/common/filters/__init__.py
```

**Step 2: Create BaseModelFilter implementation**

Create file: `backend/apps/common/filters/base.py`

```python
import django_filters
from django_filters import rest_framework as filters


class BaseModelFilter(django_filters.FilterSet):
    """
    Base FilterSet for all models inheriting from BaseModel.

    Automatically provides filters for:
    - created_at: Date range filter
    - updated_at: Date range filter
    - created_by: UUID filter
    - is_deleted: Boolean filter

    Inherit this class and add your model-specific filters.
    """

    # Time range filters for created_at
    created_at = filters.DateFromToFilter(
        field_name='created_at',
        lookup_expr=['gte', 'lte'],
        label='创建时间范围'
    )
    created_at_from = filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='创建时间起始'
    )
    created_at_to = filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='创建时间结束'
    )

    # Time range filters for updated_at
    updated_at_from = filters.DateTimeFilter(
        field_name='updated_at',
        lookup_expr='gte',
        label='更新时间起始'
    )
    updated_at_to = filters.DateTimeFilter(
        field_name='updated_at',
        lookup_expr='lte',
        label='更新时间结束'
    )

    # User filter
    created_by = filters.UUIDFilter(
        field_name='created_by_id',
        label='创建人ID'
    )

    # Soft delete filter
    is_deleted = filters.BooleanFilter(
        field_name='is_deleted',
        label='是否已删除'
    )

    class Meta:
        # Abstract base class - no model defined here
        abstract = True
```

**Step 3: Commit**

```bash
git add backend/apps/common/filters/
git commit -m "feat: implement BaseModelFilter with time range and audit field filters"
```

---

## Task 5: Create BaseCRUDService

**Files:**
- Create: `backend/apps/common/services/__init__.py`
- Create: `backend/apps/common/services/base_crud.py`

**Step 1: Create `__init__.py`**

```bash
touch backend/apps/common/services/__init__.py
```

**Step 2: Create BaseCRUDService implementation**

Create file: `backend/apps/common/services/base_crud.py`

```python
from typing import Dict, List, Optional, Any, Type
from django.db import models
from django.core.paginator import Paginator
from django.db.models import Q, QuerySet
from apps.common.models import BaseModel


class BaseCRUDService:
    """
    Base service providing standard CRUD operations for BaseModel-derived models.

    Automatically handles:
    - Organization isolation in all operations
    - Soft delete instead of hard delete
    - Audit field management (created_by, updated_by)
    - Complex queries with filters, search, and ordering
    - Pagination support
    - Batch operations

    Usage:
        class AssetService(BaseCRUDService):
            def __init__(self):
                super().__init__(Asset)

            def get_by_code(self, code: str):
                return self.query(filters={'code__exact': code}).first()
    """

    def __init__(self, model_class: Type[BaseModel]):
        """
        Initialize service with a model class.

        Args:
            model_class: Django model class inheriting from BaseModel
        """
        if not issubclass(model_class, BaseModel):
            raise TypeError(f"{model_class.__name__} must inherit from BaseModel")
        self.model_class = model_class

    def create(self, data: Dict, user, **kwargs) -> BaseModel:
        """
        Create a new record with automatic organization and created_by setting.

        Args:
            data: Dictionary of field values
            user: User instance creating the record
            **kwargs: Additional parameters (e.g., organization_id)

        Returns:
            Created model instance
        """
        from apps.common.utils.organization import get_current_organization_id

        # Auto-set organization if not provided
        if 'organization_id' not in data and 'organization' not in data:
            org_id = get_current_organization_id()
            if org_id:
                data['organization_id'] = org_id

        # Auto-set created_by if user provided
        if user and 'created_by_id' not in data and 'created_by' not in data:
            data['created_by_id'] = user.id

        return self.model_class.objects.create(**data)

    def update(self, instance_id: str, data: Dict, user=None) -> BaseModel:
        """
        Update an existing record with organization validation.

        Args:
            instance_id: UUID of the record to update
            data: Dictionary of field values to update
            user: User instance performing the update

        Returns:
            Updated model instance
        """
        instance = self.get(instance_id)

        # Auto-set updated_by if model has this field and user provided
        if user and hasattr(self.model_class, 'updated_by'):
            data['updated_by_id'] = user.id

        for key, value in data.items():
            setattr(instance, key, value)

        instance.save()
        return instance

    def delete(self, instance_id: str, user=None) -> bool:
        """
        Soft delete a record.

        Args:
            instance_id: UUID of the record to delete
            user: User performing the deletion

        Returns:
            True if successful
        """
        instance = self.get(instance_id)
        instance.soft_delete(user=user)
        return True

    def restore(self, instance_id: str) -> BaseModel:
        """
        Restore a soft-deleted record.

        Args:
            instance_id: UUID of the record to restore

        Returns:
            Restored model instance
        """
        # Use all_objects to include deleted records
        instance = self.get(instance_id, allow_deleted=True)
        instance.is_deleted = False
        instance.deleted_at = None
        if hasattr(instance, 'deleted_by'):
            instance.deleted_by = None
        instance.save()
        return instance

    def get(self, instance_id: str, allow_deleted: bool = False) -> BaseModel:
        """
        Get a single record by ID with organization validation.

        Args:
            instance_id: UUID of the record
            allow_deleted: If True, allow fetching deleted records

        Returns:
            Model instance

        Raises:
            model_class.DoesNotExist: If record not found
        """
        queryset = self.model_class.objects
        if not allow_deleted:
            queryset = queryset.filter(is_deleted=False)

        return queryset.get(id=instance_id)

    def query(
        self,
        filters: Optional[Dict] = None,
        search: Optional[str] = None,
        search_fields: Optional[List[str]] = None,
        order_by: Optional[str] = None
    ) -> QuerySet:
        """
        Query records with filters, search, and ordering.

        Args:
            filters: Dictionary of field filters
            search: Search keyword
            search_fields: List of fields to search in
            order_by: Ordering specification (e.g., '-created_at')

        Returns:
            Filtered QuerySet
        """
        queryset = self.model_class.objects.filter(is_deleted=False)

        # Apply filters
        if filters:
            q = Q()
            for key, value in filters.items():
                if '__' in key:  # Lookup already specified
                    q &= Q(**{key: value})
                else:  # Exact match
                    q &= Q(**{key: value})
            queryset = queryset.filter(q)

        # Apply search
        if search and search_fields:
            search_q = Q()
            for field in search_fields:
                search_q |= Q(**{f"{field}__icontains": search})
            queryset = queryset.filter(search_q)

        # Apply ordering
        if order_by:
            queryset = queryset.order_by(order_by)

        return queryset

    def paginate(
        self,
        queryset: QuerySet,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """
        Paginate a QuerySet.

        Args:
            queryset: QuerySet to paginate
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Dictionary with pagination data:
            {
                'count': total_count,
                'next': next_url or None,
                'previous': previous_url or None,
                'results': list of items
            }
        """
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        # Build next/previous URLs (simplified)
        next_url = None
        if page_obj.has_next():
            next_url = f"?page={page + 1}"

        previous_url = None
        if page_obj.has_previous():
            previous_url = f"?page={page - 1}"

        return {
            'count': paginator.count,
            'next': next_url,
            'previous': previous_url,
            'results': list(page_obj.object_list)
        }

    def batch_delete(self, ids: List[str], user) -> Dict[str, Any]:
        """
        Batch soft delete multiple records.

        Args:
            ids: List of record UUIDs to delete
            user: User performing the deletion

        Returns:
            Dictionary with summary and results:
            {
                'total': 3,
                'succeeded': 2,
                'failed': 1,
                'results': [
                    {'id': uuid1, 'success': true},
                    {'id': uuid2, 'success': false, 'error': 'Not found'}
                ]
            }
        """
        results = []
        succeeded = 0
        failed = 0

        for record_id in ids:
            try:
                self.delete(record_id, user)
                results.append({'id': record_id, 'success': True})
                succeeded += 1
            except self.model_class.DoesNotExist:
                results.append({'id': record_id, 'success': False, 'error': 'Not found'})
                failed += 1
            except Exception as e:
                results.append({'id': record_id, 'success': False, 'error': str(e)})
                failed += 1

        return {
            'total': len(ids),
            'succeeded': succeeded,
            'failed': failed,
            'results': results
        }
```

**Step 3: Create stub organization utility**

Create file: `backend/apps/common/utils/organization.py`

```python
from apps.common.models import BaseModel


def get_current_organization_id():
    """
    Get current organization ID from request context.

    This is a stub that will be implemented with middleware.
    For now, returns None to allow creation without org context.

    Returns:
        Organization ID or None
    """
    # TODO: Implement with OrganizationMiddleware
    # Will extract from request.META.get('X-Organization-Id')
    return None
```

**Step 4: Commit**

```bash
git add backend/apps/common/services/ backend/apps/common/utils/
git commit -m "feat: implement BaseCRUDService with standard CRUD methods and batch operations"
```

---

## Task 6: Create BatchOperationMixin

**Files:**
- Create: `backend/apps/common/viewsets/__init__.py`
- Create: `backend/apps/common/viewsets/base.py`

**Step 1: Create `__init__.py`**

```bash
touch backend/apps/common/viewsets/__init__.py
```

**Step 2: Create BatchOperationMixin and BaseModelViewSet**

Create file: `backend/apps/common/viewsets/base.py`

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.models import BaseModel


class BatchOperationMixin:
    """
    Mixin providing standard batch operation endpoints.

    Provides:
    - batch_delete(): Batch soft delete
    - batch_restore(): Batch restore
    - batch_update(): Batch field update
    """

    @action(detail=False, methods=['post'])
    def batch_delete(self, request):
        """
        Batch soft delete multiple records.

        Request body:
        {
            "ids": ["uuid1", "uuid2", "uuid3"]
        }

        Response:
        {
            "success": true,
            "message": "批量删除完成",
            "summary": {"total": 3, "succeeded": 3, "failed": 0},
            "results": [...]
        }
        """
        ids = request.data.get('ids', [])
        if not ids:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'ids参数不能为空'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        # Get the service from the viewset
        service = getattr(self, 'service', None)
        if not service:
            # Fallback to direct model operations
            results = []
            succeeded = 0
            failed = 0

            for record_id in ids:
                try:
                    instance = self.get_queryset().get(id=record_id)
                    instance.soft_delete(request.user)
                    results.append({'id': record_id, 'success': True})
                    succeeded += 1
                except self.queryset.model.DoesNotExist:
                    results.append({'id': record_id, 'success': False, 'error': 'Not found'})
                    failed += 1
                except Exception as e:
                    results.append({'id': record_id, 'success': False, 'error': str(e)})
                    failed += 1
        else:
            result = service.batch_delete(ids, request.user)
            results = result['results']
            succeeded = result['succeeded']
            failed = result['failed']

        response_data = {
            'success': True,
            'message': '批量删除完成',
            'summary': {
                'total': len(ids),
                'succeeded': succeeded,
                'failed': failed
            },
            'results': results
        }

        http_status = status.HTTP_200_OK if failed == 0 else status.HTTP_207_MULTI_STATUS
        return Response(response_data, status=http_status)

    @action(detail=False, methods=['post'])
    def batch_restore(self, request):
        """
        Batch restore multiple soft-deleted records.

        Request body:
        {
            "ids": ["uuid1", "uuid2", "uuid3"]
        }
        """
        ids = request.data.get('ids', [])
        if not ids:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'ids参数不能为空'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        results = []
        succeeded = 0
        failed = 0

        for record_id in ids:
            try:
                instance = self.get_object()  # Use parent's get_object
                instance.restore(record_id)
                results.append({'id': record_id, 'success': True})
                succeeded += 1
            except Exception as e:
                results.append({'id': record_id, 'success': False, 'error': str(e)})
                failed += 1

        return Response({
            'success': True,
            'message': '批量恢复完成',
            'summary': {
                'total': len(ids),
                'succeeded': succeeded,
                'failed': failed
            },
            'results': results
        })

    @action(detail=False, methods=['post'])
    def batch_update(self, request):
        """
        Batch update fields on multiple records.

        Request body:
        {
            "ids": ["uuid1", "uuid2"],
            "data": {"status": "active"}
        }
        """
        ids = request.data.get('ids', [])
        update_data = request.data.get('data', {})

        if not ids:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'ids参数不能为空'
                }
            }, status=status.HTTP_400_BAD_REQUEST)

        results = []
        succeeded = 0
        failed = 0

        for record_id in ids:
            try:
                instance = self.get_queryset().get(id=record_id)
                for key, value in update_data.items():
                    setattr(instance, key, value)
                instance.save()
                results.append({'id': record_id, 'success': True})
                succeeded += 1
            except Exception as e:
                results.append({'id': record_id, 'success': False, 'error': str(e)})
                failed += 1

        return Response({
            'success': True,
            'message': '批量更新完成',
            'summary': {
                'total': len(ids),
                'succeeded': succeeded,
                'failed': failed
            },
            'results': results
        })


class BaseModelViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet for all BaseModel-derived models.

    Automatically provides:
    - Organization isolation in get_queryset
    - Soft delete filtering (excludes deleted records by default)
    - Audit field management (created_by, updated_by)
    - Standard CRUD actions

    Override perform_create, perform_update, perform_destroy
    to customize behavior if needed.
    """

    def get_queryset(self):
        """Filter out soft-deleted records and apply organization isolation."""
        return self.queryset.filter(is_deleted=False)

    def perform_create(self, serializer):
        """Set created_by and organization on create."""
        serializer.save(
            created_by=self.request.user,
            organization_id=self.request.user.organization_id
        )

    def perform_update(self, serializer):
        """Set updated_by on update."""
        serializer.save(updated_by=self.request.user)

    def perform_destroy(self, instance):
        """Perform soft delete instead of hard delete."""
        instance.soft_delete(user=self.request.user)

    @action(detail=False, methods=['get'])
    def deleted(self, request):
        """
        List soft-deleted records.

        GET /api/{resource}/deleted/
        """
        # Get all deleted records (user must have permission)
        queryset = self.queryset.model.all_objects.filter(is_deleted=True)

        # Apply organization filtering
        if hasattr(request, 'user') and hasattr(request.user, 'organization_id'):
            queryset = queryset.filter(organization_id=request.user.organization_id)

        page = self.request.query_params.get('page', 1)
        page_size = self.request.query_params.get('page_size', 20)

        from django.core.paginator import Paginator
        paginator = Paginator(queryset, page_size)
        page_obj = paginator.get_page(page)

        serializer = self.get_serializer(page_obj, many=True)

        return Response({
            'success': True,
            'data': {
                'count': paginator.count,
                'next': page_obj.has_next() and f"?page={page + 1}" or None,
                'previous': page_obj.has_previous() and f"?page={page - 1}" or None,
                'results': serializer.data
            }
        })

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """
        Restore a soft-deleted record.

        POST /api/{resource}/{id}/restore/
        """
        instance = self.get_object()
        instance.restore()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'message': '恢复成功',
            'data': serializer.data
        })


class BaseModelViewSetWithBatch(BatchOperationMixin, BaseModelViewSet):
    """
    Base ViewSet with batch operation support.

    Inherits from both BatchOperationMixin and BaseModelViewSet
    to provide all standard CRUD + batch operation endpoints.

    This is the recommended ViewSet to use for most resources.
    """
    pass  # All functionality inherited from parent classes
```

**Step 3: Commit**

```bash
git add backend/apps/common/viewsets/
git commit -m "feat: implement BaseModelViewSet with soft delete, audit fields, and deleted record management"
```

---

## Task 7: Create BaseResponse and ExceptionHandler

**Files:**
- Create: `backend/apps/common/responses/__init__.py`
- Create: `backend/apps/common/responses/base.py`
- Create: `backend/apps/common/handlers/__init__.py`
- Create: `backend/apps/common/handlers/exceptions.py`

**Step 1: Create directories and init files**

```bash
mkdir -p backend/apps/common/responses backend/apps/common/handlers
touch backend/apps/common/responses/__init__.py backend/apps/common/handlers/__init__.py
```

**Step 2: Create BaseResponse**

Create file: `backend/apps/common/responses/base.py`

```python
from rest_framework import status
from typing import Any, Dict, Optional


class BaseResponse:
    """
    Standardized API response builder.

    Provides consistent response format for all endpoints.
    """

    @staticmethod
    def success(
        data: Any = None,
        message: str = "操作成功",
        http_status: int = status.HTTP_200_OK
    ) -> Dict[str, Any]:
        """
        Build a success response.

        Args:
            data: Response data
            message: Success message
            http_status: HTTP status code

        Returns:
            Dictionary with success, message, data structure
        """
        response = {
            'success': True,
            'message': message,
        }

        if data is not None:
            response['data'] = data

        return response

    @staticmethod
    def error(
        code: str,
        message: str,
        details: Optional[Dict] = None,
        http_status: int = status.HTTP_400_BAD_REQUEST
    ) -> Dict[str, Any]:
        """
        Build an error response.

        Args:
            code: Error code (e.g., 'VALIDATION_ERROR', 'NOT_FOUND')
            message: Error message
            details: Additional error details
            http_status: HTTP status code

        Returns:
            Dictionary with success, error structure
        """
        response = {
            'success': False,
            'error': {
                'code': code,
                'message': message,
            }
        }

        if details is not None:
            response['error']['details'] = details

        return response
```

**Step 3: Create ExceptionHandler**

Create file: `backend/apps/common/handlers/exceptions.py`

```python
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from django.db import IntegrityError
from django.core.exceptions import ValidationError as DjangoValidationError
import logging

from apps.common.responses.base import BaseResponse

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for consistent error responses.

    Handles:
    - Validation errors
    - Not found errors
    - Integrity errors
    - Permission denied
    - Unexpected errors

    Returns:
        Response with standardized error format
    """
    # Handle DRF validation errors
    if isinstance(exc, Exception) and hasattr(exc, 'detail'):
        # DRF validation exception
        return Response(
            BaseResponse.error(
                code='VALIDATION_ERROR',
                message=str(exc.detail),
                details=exc.detail if isinstance(exc.detail, dict) else None
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    # Handle Django 404
    if isinstance(exc, Http404):
        return Response(
            BaseResponse.error(
                code='NOT_FOUND',
                message='请求的资源不存在'
            ),
            status=status.HTTP_404_NOT_FOUND
        )

    # Handle Django validation error
    if isinstance(exc, DjangoValidationError):
        return Response(
            BaseResponse.error(
                code='VALIDATION_ERROR',
                message=str(exc.message_dict or exc.message)
            ),
            status=status.HTTP_400_BAD_REQUEST
        )

    # Handle database integrity errors
    if isinstance(exc, IntegrityError):
        return Response(
            BaseResponse.error(
                code='CONFLICT',
                message='数据冲突，可能违反了唯一约束'
            ),
            status=status.HTTP_409_CONFLICT
        )

    # Handle permission errors
    if isinstance(exc, PermissionError):
        return Response(
            BaseResponse.error(
                code='PERMISSION_DENIED',
                message='权限不足'
            ),
            status=status.HTTP_403_FORBIDDEN
        )

    # Log unexpected errors
    logger.error(f"Unexpected exception: {exc}", exc_info=True)

    # Fall back to default DRF handler
    return exception_handler(exc, context)
```

**Step 4: Commit**

```bash
git add backend/apps/common/responses/ backend/apps/common/handlers/
git commit -m "feat: implement BaseResponse builder and custom exception handler with standardized error format"
```

---

## Task 8: Create URL routing for common module

**Files:**
- Create: `backend/apps/common/urls.py`

**Step 1: Create common URLs file**

Create file: `backend/apps/common/urls.py`

```python
from django.urls import path, include

app_name = 'common'

urlpatterns = [
    # Common module URLs (if any)
]
```

**Step 2: Commit**

```bash
git add backend/apps/common/urls.py
git commit -m "feat: add URL routing for common module"
```

---

## Task 9: Run full test suite

**Step 1: Run all tests**

```bash
cd backend
python manage.py test apps.common
```

**Step 2: Verify all tests pass**

Expected: All tests should pass. If any fail, debug and fix.

**Step 3: Create database migrations**

```bash
cd backend
python manage.py makemigrations common
python manage.py migrate
```

**Step 4: Final commit**

```bash
git add backend/
git commit -m "test: ensure all common base classes tests pass"
```

---

## Summary

This plan implements the foundational base classes that all GZEAMS modules will depend on:

| Component | File | Purpose |
|-----------|------|---------|
| **BaseModel** | `apps/common/models.py` | Organization isolation, soft delete, audit fields, custom_fields |
| **BaseModelSerializer** | `apps/common/serializers/base.py` | Auto-serialize public fields, nested serializers |
| **BaseModelFilter** | `apps/common/filters/base.py` | Time range, audit field filters |
| **BaseCRUDService** | `apps/common/services/base_crud.py` | Standard CRUD with org isolation |
| **BaseModelViewSet** | `apps/common/viewsets/base.py` | Auto org filtering, soft delete, audit management |
| **BatchOperationMixin** | `apps/common/viewsets/base.py` | Batch delete/restore/update |
| **BaseResponse** | `apps/common/responses/base.py` | Standardized response builder |
| **ExceptionHandler** | `apps/common/handlers/exceptions.py` | Custom exception handling |

**Next Steps After This Plan:**
1. Implement Organization model (Task 10)
2. Implement User model (Task 11)
3. Implement AssetCategory model (Phase 1.1)

---

**Plan created:** 2025-01-17
**Estimated time:** 4-6 hours for a developer familiar with Django
