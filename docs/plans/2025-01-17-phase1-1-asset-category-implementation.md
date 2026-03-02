# Phase 1.1: Asset Category Implementation Plan

## Document Information

| Project | Description |
|---------|-------------|
| Plan Version | v1.0 |
| Created Date | 2026-01-17 |
| Target Module | Phase 1.1 Asset Category (资产分类体系) |
| Estimated Duration | 3-4 hours |
| Dependencies | Common Base Classes (must be implemented first) |

---

## Overview

This plan implements the Asset Category management module following the GZEAMS architecture:
- **Metadata-driven**: Categories can be system or custom (user-defined)
- **Tree structure**: Hierarchical parent-child relationships
- **Multi-organization**: Categories are isolated per organization
- **Deprecation support**: Built-in depreciation methods and useful life defaults

### Key Features

1. **Category Tree API** - Get complete category hierarchy in single response
2. **CRUD Operations** - Create, read, update, delete (soft delete) categories
3. **Custom Categories** - Users can extend system categories
4. **Deprecation Configuration** - Method and useful life per category
5. **Add Child Action** - Shortcut to add subcategory to parent

---

## Prerequisites

Before starting this module, ensure:
- [x] Common base classes are implemented (BaseModel, BaseModelSerializer, etc.)
- [x] PostgreSQL database with JSONB support
- [x] DRF is configured and working
- [x] Django app structure is created (`backend/apps/assets/`)

---

## Architecture Diagram

```
backend/apps/assets/
├── __init__.py
├── models.py              # AssetCategory model (inherits BaseModel)
├── serializers/
│   ├── __init__.py
│   └── category.py        # AssetCategorySerializer, AssetCategoryTreeSerializer
├── viewsets/
│   ├── __init__.py
│   └── category.py        # AssetCategoryViewSet
├── filters/
│   ├── __init__.py
│   └── category.py        # AssetCategoryFilter
├── services/
│   ├── __init__.py
│   └── category_service.py # AssetCategoryService
└── urls.py                # Category endpoints
```

---

## Implementation Tasks

### Task 1: Create AssetCategory Model

**File**: `backend/apps/assets/models.py`

```python
from django.db import models
from apps.common.models import BaseModel

class AssetCategory(BaseModel):
    """
    Asset Category Model
    Supports hierarchical tree structure with parent-child relationships.
    System categories (is_custom=False) are predefined; users can create custom categories.
    """
    # Basic Information
    code = models.CharField(max_length=50, db_index=True,
                            help_text="Unique category code (e.g., '2001' for computer equipment)")
    name = models.CharField(max_length=200,
                            help_text="Category display name")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                              related_name='children',
                              help_text="Parent category for tree structure")
    full_name = models.CharField(max_length=500, editable=False,
                                 help_text="Full path name (e.g., 'Computer Equipment > Desktop')")

    # Tree Structure
    level = models.IntegerField(default=0, editable=False,
                                help_text="Tree level (0=root, 1=first child, ...)")
    sort_order = models.IntegerField(default=0,
                                     help_text="Display order within same level")

    # Category Type
    is_custom = models.BooleanField(default=False,
                                    help_text="True=user-created, False=system predefined")
    is_active = models.BooleanField(default=True,
                                    help_text="Category status (can be deactivated without deletion)")

    # Depreciation Configuration
    DEPRECIATION_METHODS = [
        ('straight_line', 'Straight Line Method'),
        ('double_declining', 'Double Declining Balance'),
        ('sum_of_years', 'Sum of Years Digits'),
        ('no_depreciation', 'No Depreciation'),
    ]
    depreciation_method = models.CharField(max_length=50,
                                           choices=DEPRECIATION_METHODS,
                                           default='straight_line')
    default_useful_life = models.IntegerField(default=60,
                                              help_text="Default useful life in months")
    residual_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00,
                                       help_text="Default residual value rate (%)")

    class Meta:
        db_table = 'asset_category'
        verbose_name = 'Asset Category'
        verbose_name_plural = 'Asset Categories'
        ordering = ['sort_order', 'code']
        indexes = [
            models.Index(fields=['organization', 'code']),
            models.Index(fields=['organization', 'parent']),
            models.Index(fields=['organization', 'is_deleted', 'is_active']),
        ]

    def __str__(self):
        return f"{self.code} - {self.full_name}"

    def save(self, *args, **kwargs):
        # Auto-calculate level and full_name before saving
        if self.parent:
            self.level = self.parent.level + 1
            self.full_name = f"{self.parent.full_name} > {self.name}"
        else:
            self.level = 0
            self.full_name = self.name
        super().save(*args, **kwargs)

    @classmethod
    def get_tree(cls, organization_id):
        """Get category tree for an organization."""
        categories = cls.objects.filter(
            organization_id=organization_id,
            is_deleted=False
        ).order_by('sort_order', 'code')

        # Build tree structure
        from collections import defaultdict
        children_map = defaultdict(list)
        root_categories = []

        for cat in categories:
            if cat.parent_id:
                children_map[cat.parent_id].append(cat)
            else:
                root_categories.append(cat)

        def build_tree(category):
            """Recursively build tree with children."""
            data = {
                'id': category.id,
                'code': category.code,
                'name': category.name,
                'full_name': category.full_name,
                'level': category.level,
                'is_custom': category.is_custom,
                'depreciation_method': category.depreciation_method,
                'default_useful_life': category.default_useful_life,
                'children': []
            }
            # Add children recursively
            for child in children_map.get(category.id, []):
                data['children'].append(build_tree(child))
            return data

        return [build_tree(cat) for cat in root_categories]

    def can_delete(self):
        """Check if category can be deleted (no children, no assets)."""
        has_children = self.children.filter(is_deleted=False).exists()
        # TODO: Check for assets when Asset model is implemented
        return not has_children
```

**Commit**: `feat(assets): create AssetCategory model with tree structure`

---

### Task 2: Create AssetCategory Serializers

**File**: `backend/apps/assets/serializers/category.py`

```python
from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer
from apps.assets.models import AssetCategory


class AssetCategorySerializer(BaseModelSerializer):
    """Serializer for AssetCategory CRUD operations."""

    parent_name = serializers.CharField(source='parent.name', read_only=True)
    depreciation_method_display = serializers.CharField(source='get_depreciation_method_display', read_only=True)
    has_children = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = AssetCategory
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'parent', 'parent_name', 'full_name',
            'level', 'sort_order', 'is_custom', 'is_active',
            'depreciation_method', 'depreciation_method_display',
            'default_useful_life', 'residual_rate', 'has_children',
        ]

    def get_has_children(self, obj):
        return obj.children.filter(is_deleted=False).exists()

    def validate(self, data):
        """Custom validation."""
        # Check if code already exists (within organization)
        if 'code' in data:
            code = data['code']
            org_id = self.context.get('organization_id')

            queryset = AssetCategory.objects.filter(
                organization_id=org_id,
                code=code,
                is_deleted=False
            )

            # Exclude current instance for updates
            if self.instance:
                queryset = queryset.exclude(id=self.instance.id)

            if queryset.exists():
                raise serializers.ValidationError({
                    'code': 'Category code already exists in this organization.'
                })

        # Prevent circular reference in parent
        parent = data.get('parent')
        if parent and self.instance:
            if self._is_descendant(parent, self.instance):
                raise serializers.ValidationError({
                    'parent': 'Cannot set a descendant as parent.'
                })

        return data

    def _is_descendant(self, parent, child):
        """Check if parent is a descendant of child (circular reference)."""
        current = child
        while current.parent_id:
            if current.parent_id == parent.id:
                return True
            current = current.parent
        return False


class AssetCategoryTreeSerializer(serializers.Serializer):
    """Serializer for category tree response."""

    id = serializers.UUIDField()
    code = serializers.CharField()
    name = serializers.CharField()
    full_name = serializers.CharField()
    level = serializers.IntegerField()
    is_custom = serializers.BooleanField()
    depreciation_method = serializers.CharField()
    default_useful_life = serializers.IntegerField()
    children = serializers.ListField(child=serializers.Serializer(), required=False)


class AssetCategoryCreateSerializer(AssetCategorySerializer):
    """Serializer for creating categories with simplified output."""

    class Meta(AssetCategorySerializer.Meta):
        fields = [
            'id', 'code', 'name', 'parent', 'full_name', 'level',
            'is_custom', 'depreciation_method', 'default_useful_life',
            'residual_rate', 'sort_order', 'is_active'
        ]


class AddChildSerializer(serializers.Serializer):
    """Serializer for add_child action."""

    code = serializers.CharField(max_length=50, required=True)
    name = serializers.CharField(max_length=200, required=True)
    depreciation_method = serializers.ChoiceField(
        choices=AssetCategory.DEPRECIATION_METHODS,
        default='straight_line'
    )
    default_useful_life = serializers.IntegerField(default=60)
    residual_rate = serializers.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    sort_order = serializers.IntegerField(default=0)
```

**File**: `backend/apps/assets/serializers/__init__.py`

```python
from .category import (
    AssetCategorySerializer,
    AssetCategoryTreeSerializer,
    AssetCategoryCreateSerializer,
    AddChildSerializer,
)

__all__ = [
    'AssetCategorySerializer',
    'AssetCategoryTreeSerializer',
    'AssetCategoryCreateSerializer',
    'AddChildSerializer',
]
```

**Commit**: `feat(assets): create AssetCategory serializers`

---

### Task 3: Create AssetCategoryFilter

**File**: `backend/apps/assets/filters/category.py`

```python
import django_filters
from apps.common.filters.base import BaseModelFilter
from apps.assets.models import AssetCategory


class AssetCategoryFilter(BaseModelFilter):
    """Filter for AssetCategory list endpoint."""

    class Meta(BaseModelFilter.Meta):
        model = AssetCategory
        fields = BaseModelFilter.Meta.fields + [
            'code', 'parent', 'is_custom', 'is_active',
            'depreciation_method'
        ]

    # Custom filters
    code = django_filters.CharFilter(lookup_expr='icontains')
    parent = django_filters.UUIDFilter(field_name='parent_id')
    is_custom = django_filters.BooleanFilter()
    is_active = django_filters.BooleanFilter()
    search = django_filters.CharFilter(method='filter_search')

    def filter_search(self, queryset, name, value):
        """Search by code or name."""
        return queryset.filter(
            code__icontains=value
        ).union(
            queryset.filter(name__icontains=value)
        )
```

**File**: `backend/apps/assets/filters/__init__.py`

```python
from .category import AssetCategoryFilter

__all__ = ['AssetCategoryFilter']
```

**Commit**: `feat(assets): create AssetCategory filter`

---

### Task 4: Create AssetCategoryService

**File**: `backend/apps/assets/services/category_service.py`

```python
from apps.common.services.base_crud import BaseCRUDService
from apps.assets.models import AssetCategory


class AssetCategoryService(BaseCRUDService):
    """Service layer for AssetCategory business logic."""

    def __init__(self):
        super().__init__(AssetCategory)

    def get_tree(self, organization_id):
        """Get category tree for organization."""
        return AssetCategory.get_tree(organization_id)

    def add_child(self, parent_id, data, organization_id, user):
        """Add child category to parent."""
        try:
            parent = self.model_class.objects.get(
                id=parent_id,
                organization_id=organization_id,
                is_deleted=False
            )
        except AssetCategory.DoesNotExist:
            raise ValueError('Parent category not found')

        # Create child category
        child_data = {
            **data,
            'parent_id': parent.id,
            'organization_id': organization_id,
            'is_custom': True,
        }

        return self.create(child_data, user)

    def can_delete(self, category_id, organization_id):
        """Check if category can be deleted."""
        try:
            category = self.model_class.objects.get(
                id=category_id,
                organization_id=organization_id,
                is_deleted=False
            )
            return category.can_delete()
        except AssetCategory.DoesNotExist:
            return False

    def get_by_code(self, code, organization_id):
        """Get category by code within organization."""
        try:
            return self.model_class.objects.get(
                code=code,
                organization_id=organization_id,
                is_deleted=False
            )
        except AssetCategory.DoesNotExist:
            return None
```

**File**: `backend/apps/assets/services/__init__.py`

```python
from .category_service import AssetCategoryService

__all__ = ['AssetCategoryService']
```

**Commit**: `feat(assets): create AssetCategory service layer`

---

### Task 5: Create AssetCategoryViewSet

**File**: `backend/apps/assets/viewsets/category.py`

```python
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets.base import BaseModelViewSet
from apps.common.responses.base import BaseResponse
from apps.assets.models import AssetCategory
from apps.assets.serializers import (
    AssetCategorySerializer,
    AssetCategoryTreeSerializer,
    AssetCategoryCreateSerializer,
    AddChildSerializer,
)
from apps.assets.filters import AssetCategoryFilter
from apps.assets.services import AssetCategoryService


class AssetCategoryViewSet(BaseModelViewSet):
    """
    ViewSet for Asset Category management.

    Provides:
    - Standard CRUD operations
    - Tree endpoint for hierarchical data
    - add_child action for quick subcategory creation
    """
    queryset = AssetCategory.objects.all()
    serializer_class = AssetCategorySerializer
    filterset_class = AssetCategoryFilter
    service = AssetCategoryService()

    def get_serializer_context(self):
        """Add organization_id to serializer context."""
        context = super().get_serializer_context()
        # organization_id is set by middleware/get_queryset
        return context

    def perform_create(self, serializer):
        """Set organization and created_by on create."""
        organization_id = getattr(self.request, 'organization_id', None)
        serializer.save(
            organization_id=organization_id,
            created_by=self.request.user
        )

    def perform_update(self, serializer):
        """Set updated_by on update."""
        serializer.save(updated_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        """Override to check if category can be deleted."""
        instance = self.get_object()

        if not instance.can_delete():
            return BaseResponse.error_response(
                code='VALIDATION_ERROR',
                message='Cannot delete category with children or associated assets.',
                details={'reason': 'has_children_or_assets'}
            )

        # Perform soft delete
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='tree')
    def tree(self, request):
        """Get complete category tree."""
        organization_id = getattr(request, 'organization_id', None)

        if not organization_id:
            return BaseResponse.error_response(
                code='UNAUTHORIZED',
                message='Organization context required'
            )

        tree_data = self.service.get_tree(organization_id)

        serializer = AssetCategoryTreeSerializer(tree_data, many=True)

        return BaseResponse.success_response(
            data=serializer.data[0] if serializer.data else {},
            message='Query successful'
        )

    @action(detail=True, methods=['post'], url_path='add_child')
    def add_child(self, request, pk=None):
        """Add child category to this category."""
        parent = self.get_object()
        serializer = AddChildSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        child = self.service.add_child(
            parent_id=parent.id,
            data=serializer.validated_data,
            organization_id=request.organization_id,
            user=request.user
        )

        response_serializer = AssetCategoryCreateSerializer(child)

        return BaseResponse.success_response(
            data=response_serializer.data,
            message='Create successful'
        )
```

**File**: `backend/apps/assets/viewsets/__init__.py`

```python
from .category import AssetCategoryViewSet

__all__ = ['AssetCategoryViewSet']
```

**Commit**: `feat(assets): create AssetCategory ViewSet with tree endpoint`

---

### Task 6: Configure URLs

**File**: `backend/apps/assets/urls.py`

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.assets.viewsets import AssetCategoryViewSet

router = DefaultRouter()
router.register(r'categories', AssetCategoryViewSet, basename='assetcategory')

urlpatterns = [
    path('api/assets/', include(router.urls)),
]
```

**File**: `backend/config/urls.py` (add to main URL config)

```python
urlpatterns += [
    path('', include('apps.assets.urls')),
]
```

**Commit**: `feat(assets): configure category URLs`

---

### Task 7: Create Unit Tests

**File**: `backend/apps/assets/tests/test_models.py`

```python
from django.test import TestCase
from apps.assets.models import AssetCategory
from apps.organizations.models import Organization
from django.contrib.auth import get_user_model

User = get_user_model()


class AssetCategoryModelTest(TestCase):
    """Test AssetCategory model."""

    def setUp(self):
        self.org = Organization.objects.create(name='Test Org', code='TEST')
        self.user = User.objects.create_user(username='testuser')

    def test_category_creation(self):
        """Test creating a root category."""
        category = AssetCategory.objects.create(
            organization=self.org,
            code='2001',
            name='Computer Equipment',
            created_by=self.user
        )
        self.assertEqual(category.level, 0)
        self.assertEqual(category.full_name, 'Computer Equipment')

    def test_child_category_level(self):
        """Test child category inherits parent level + 1."""
        parent = AssetCategory.objects.create(
            organization=self.org,
            code='2001',
            name='Computer Equipment',
            created_by=self.user
        )
        child = AssetCategory.objects.create(
            organization=self.org,
            code='200101',
            name='Desktop',
            parent=parent,
            created_by=self.user
        )
        self.assertEqual(child.level, 1)
        self.assertEqual(child.full_name, 'Computer Equipment > Desktop')

    def test_can_delete_no_children(self):
        """Test category without children can be deleted."""
        category = AssetCategory.objects.create(
            organization=self.org,
            code='2001',
            name='Computer Equipment',
            created_by=self.user
        )
        self.assertTrue(category.can_delete())

    def test_cannot_delete_with_children(self):
        """Test category with children cannot be deleted."""
        parent = AssetCategory.objects.create(
            organization=self.org,
            code='2001',
            name='Computer Equipment',
            created_by=self.user
        )
        AssetCategory.objects.create(
            organization=self.org,
            code='200101',
            name='Desktop',
            parent=parent,
            created_by=self.user
        )
        self.assertFalse(parent.can_delete())
```

**File**: `backend/apps/assets/tests/test_api.py`

```python
from django.test import TestCase
from rest_framework.test import APIClient
from apps.organizations.models import Organization
from django.contrib.auth import get_user_model
from apps.assets.models import AssetCategory

User = get_user_model()


class AssetCategoryAPITest(TestCase):
    """Test AssetCategory API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.org = Organization.objects.create(name='Test Org', code='TEST')
        self.user = User.objects.create_user(username='testuser')
        self.client.force_authenticate(user=self.user)
        self.client.cookies['X-Organization-ID'] = str(self.org.id)

    def test_list_categories(self):
        """Test GET /api/assets/categories/"""
        AssetCategory.objects.create(
            organization=self.org,
            code='2001',
            name='Computer Equipment',
            created_by=self.user
        )

        response = self.client.get('/api/assets/categories/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])

    def test_create_category(self):
        """Test POST /api/assets/categories/"""
        data = {
            'code': '2001',
            'name': 'Computer Equipment',
            'depreciation_method': 'straight_line',
            'default_useful_life': 60
        }
        response = self.client.post('/api/assets/categories/', data)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data['success'])

    def test_get_category_tree(self):
        """Test GET /api/assets/categories/tree/"""
        AssetCategory.objects.create(
            organization=self.org,
            code='2001',
            name='Computer Equipment',
            created_by=self.user
        )

        response = self.client.get('/api/assets/categories/tree/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['success'])
        self.assertIn('children', response.data['data'])

    def test_delete_category_with_children_fails(self):
        """Test DELETE with children returns validation error."""
        parent = AssetCategory.objects.create(
            organization=self.org,
            code='2001',
            name='Computer Equipment',
            created_by=self.user
        )
        AssetCategory.objects.create(
            organization=self.org,
            code='200101',
            name='Desktop',
            parent=parent,
            created_by=self.user
        )

        response = self.client.delete(f'/api/assets/categories/{parent.id}/')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['error']['code'], 'VALIDATION_ERROR')
```

**Commit**: `test(assets): create unit tests for category model and API`

---

## API Coverage Verification

| API Endpoint | Implementation | Status |
|-------------|----------------|--------|
| GET `/api/assets/categories/tree/` | AssetCategoryViewSet.tree() | Task 5 |
| GET `/api/assets/categories/` | BaseModelViewSet.list() | Inherited |
| GET `/api/assets/categories/{id}/` | BaseModelViewSet.retrieve() | Inherited |
| POST `/api/assets/categories/` | BaseModelViewSet.create() | Inherited |
| PUT `/api/assets/categories/{id}/` | BaseModelViewSet.update() | Inherited |
| DELETE `/api/assets/categories/{id}/` | AssetCategoryViewSet.destroy() | Task 5 |
| POST `/api/assets/categories/{id}/add_child/` | AssetCategoryViewSet.add_child() | Task 5 |

---

## PRD Compliance Checklist

| PRD Requirement | Implementation | Status |
|----------------|----------------|--------|
| Inherits from BaseModel | `class AssetCategory(BaseModel)` | Task 1 |
| Organization isolation | Via BaseModel.org field | Inherited |
| Soft delete support | Via BaseModel.is_deleted | Inherited |
| Audit fields | Via BaseModel (created_at, updated_at, created_by) | Inherited |
| Tree structure support | parent FK + level + get_tree() method | Task 1 |
| Custom categories | is_custom boolean field | Task 1 |
| Depreciation config | depreciation_method + default_useful_life | Task 1 |
| Add child action | @action add_child() | Task 5 |
| Standard API response | Uses BaseResponse | Task 5 |
| Standard error codes | Via BaseResponse.error_response() | Inherited |

---

## Definition of Done

- [ ] All models created with proper BaseModel inheritance
- [ ] All serializers inherit from BaseModelSerializer
- [ ] ViewSet inherits from BaseModelViewSet
- [ ] Tree endpoint returns wrapped response format
- [ ] DELETE validates children before allowing deletion
- [ ] All unit tests pass
- [ ] API responses follow standard format (success, message, data)
- [ ] Error responses use standard error codes
- [ ] Code committed with descriptive messages

---

## Execution Order (TDD Approach)

1. **Write failing test** for model → **Run** (expect fail) → **Implement model** → **Run** (expect pass) → **Commit**
2. **Write failing test** for serializer → **Run** → **Implement serializer** → **Run** → **Commit**
3. **Write failing test** for filter → **Run** → **Implement filter** → **Run** → **Commit**
4. **Write failing test** for service → **Run** → **Implement service** → **Run** → **Commit**
5. **Write failing test** for ViewSet → **Run** → **Implement ViewSet** → **Run** → **Commit**
6. **Write failing test** for URL routing → **Run** → **Configure URLs** → **Run** → **Commit**
7. **Integration test** full API flow → **Fix issues** → **Run** → **Final commit**

---

## Next Steps

After completing Phase 1.1:
1. Implement Phase 1.2 (Multi-Organization)
2. Implement Phase 1.3 (Business Metadata)
3. Continue with remaining Phase 1 modules

---

**Plan Version**: v1.0
**Created**: 2026-01-17
**Author**: GZEAMS Development Team
