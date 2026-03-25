# Backend Fix & Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix identified backend gaps and complete missing API endpoints to support frontend requirements.

**Architecture:** Django 5.0 + DRF with metadata-driven low-code platform architecture. All models inherit from BaseModel for organization isolation, soft delete, and audit trails. ViewSets inherit from BaseModelViewSetWithBatch for standard CRUD + batch operations.

**Tech Stack:** Django 5.0, Django REST Framework, PostgreSQL (JSONB), Redis, Celery

---

## Overview

This plan addresses the backend gaps identified from the frontend analysis:

| Gap | Priority | Effort |
|-----|----------|--------|
| Missing QR Code API endpoints | High | 1 day |
| Missing Category tree endpoints | High | 1 day |
| Missing Department tree endpoints | High | 1 day |
| Workflow integration in operations | High | 2 days |
| Notification system | Medium | 2 days |
| User/Department selector APIs | Medium | 1 day |
| Asset export API completion | Low | 0.5 day |
| SSO integration endpoints | Low | 2 days |

---

## Task 1: Add Missing Asset QR Code Endpoint

**Files:**
- Modify: `backend/apps/assets/viewsets/asset.py`
- Test: `backend/apps/assets/tests/test_api.py`

**Step 1: Verify current QR code endpoint works**

Run: `docker-compose exec backend python manage.py test apps.assets.tests.test_api::AssetViewSetTestCase::test_qr_code -v 2`

Expected: Current implementation exists at line 366-407

**Step 2: Add bulk QR code generation endpoint**

Add to `AssetViewSet` in `backend/apps/assets/viewsets/asset.py` after line 407:

```python
@action(detail=False, methods=['post'], url_path='bulk-qr-codes')
def bulk_qr_codes(self, request):
    """
    Generate QR codes for multiple assets as a ZIP file.

    POST /api/assets/bulk-qr-codes/
    Body:
    {
        "ids": ["uuid1", "uuid2", "uuid3"]
    }

    Returns a ZIP file containing PNG images.
    """
    import qrcode
    from io import BytesIO
    from zipfile import ZipFile
    from django.conf import settings

    ids = request.data.get('ids', [])
    if not ids:
        return BaseResponse.error(
            code='VALIDATION_ERROR',
            message='ids parameter is required'
        )

    organization_id = getattr(request, 'organization_id', None)
    assets = Asset.objects.filter(
        id__in=ids,
        organization_id=organization_id,
        is_deleted=False
    )

    # Create ZIP file in memory
    zip_buffer = BytesIO()
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')

    with ZipFile(zip_buffer, 'w') as zip_file:
        for asset in assets:
            qr_data = f'{frontend_url}/assets/{asset.id}'
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color='black', back_color='white')

            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)

            filename = f"QR_{asset.asset_code or asset.id}.png"
            zip_file.writestr(filename, img_buffer.read())

    zip_buffer.seek(0)

    return HttpResponse(
        zip_buffer.read(),
        content_type='application/zip',
        headers={
            'Content-Disposition': 'attachment; filename="asset_qr_codes.zip"'
        }
    )
```

**Step 3: Add test for bulk QR code endpoint**

Add to `backend/apps/assets/tests/test_api.py`:

```python
def test_bulk_qr_codes_success(self):
    """Test bulk QR code generation."""
    asset1 = Asset.objects.create(
        asset_code='TEST001',
        asset_name='Test Asset 1',
        organization=self.organization,
        created_by=self.user
    )
    asset2 = Asset.objects.create(
        asset_code='TEST002',
        asset_name='Test Asset 2',
        organization=self.organization,
        created_by=self.user
    )

    self.request.user = self.user
    self.request.organization_id = self.organization.id
    self.request.data = {'ids': [str(asset1.id), str(asset2.id)]}

    response = self.viewset.bulk_qr_codes(self.request)
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response['content-type'], 'application/zip')
```

**Step 4: Run tests to verify**

Run: `docker-compose exec backend python manage.py test apps.assets.tests.test_api::AssetViewSetTestCase::test_bulk_qr_codes_success -v 2`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/apps/assets/viewsets/asset.py backend/apps/assets/tests/test_api.py
git commit -m "feat(assets): add bulk QR code generation endpoint"
```

---

## Task 2: Add Category Tree Endpoint

**Files:**
- Modify: `backend/apps/assets/viewsets/category.py`
- Test: `backend/apps/assets/tests/test_category_api.py`

**Step 1: Check current category ViewSet**

Run: `cat backend/apps/assets/viewsets/category.py`

Note: The ViewSet exists but may be missing tree endpoint.

**Step 2: Add tree endpoint to AssetCategoryViewSet**

```python
@action(detail=False, methods=['get'], url_path='tree')
def tree(self, request):
    """
    Get complete category tree for current organization.

    GET /api/assets/categories/tree/

    Returns hierarchical tree structure with:
    - id, code, name
    - children (recursive)
    - asset_count
    """
    from apps.assets.services.category_service import CategoryService

    organization_id = getattr(request, 'organization_id', None)

    if not organization_id:
        return BaseResponse.error(
            code='UNAUTHORIZED',
            message='Organization context required'
        )

    service = CategoryService()
    tree_data = service.get_tree(organization_id)

    return BaseResponse.success(
        data=tree_data,
        message='Category tree retrieved successfully'
    )

@action(detail=True, methods=['get'], url_path='path')
def path(self, request, pk=None):
    """
    Get breadcrumb path for a category.

    GET /api/assets/categories/{id}/path/

    Returns array of ancestors from root to current category.
    """
    from apps.assets.services.category_service import CategoryService

    category = self.get_object()
    service = CategoryService()
    path_data = service.get_category_path(category.id)

    return BaseResponse.success(
        data=path_data,
        message='Category path retrieved successfully'
    )
```

**Step 3: Add service methods if missing**

Check `backend/apps/assets/services/category_service.py`:

```python
def get_tree(self, organization_id):
    """Get full category tree for organization."""
    from apps.assets.models import AssetCategory

    def build_tree(parent_id=None):
        categories = AssetCategory.objects.filter(
            organization_id=organization_id,
            parent_id=parent_id,
            is_deleted=False
        ).order_by('sort_order', 'name')

        result = []
        for cat in categories:
            children = build_tree(cat.id)
            result.append({
                'id': str(cat.id),
                'code': cat.code,
                'name': cat.name,
                'level': cat.level,
                'is_leaf': cat.is_leaf,
                'asset_count': cat.asset_count,
                'children': children
            })
        return result

    return build_tree()

def get_category_path(self, category_id):
    """Get breadcrumb path from root to category."""
    from apps.assets.models import AssetCategory

    category = AssetCategory.objects.get(id=category_id)
    path = []
    current = category

    while current:
        path.append({
            'id': str(current.id),
            'code': current.code,
            'name': current.name
        })
        current = current.parent

    return list(reversed(path))
```

**Step 4: Add tests**

```python
def test_category_tree_endpoint(self):
    """Test category tree retrieval."""
    # Create category hierarchy
    parent = AssetCategory.objects.create(
        code='PARENT',
        name='Parent Category',
        organization=self.organization,
        level=1,
        created_by=self.user
    )
    child = AssetCategory.objects.create(
        code='CHILD',
        name='Child Category',
        organization=self.organization,
        parent=parent,
        level=2,
        created_by=self.user
    )

    self.request.organization_id = self.organization.id
    response = self.viewset.tree(self.request)
    self.assertEqual(response.status_code, 200)

def test_category_path_endpoint(self):
    """Test category path retrieval."""
    parent = AssetCategory.objects.create(
        code='PARENT',
        name='Parent Category',
        organization=self.organization,
        level=1,
        created_by=self.user
    )
    child = AssetCategory.objects.create(
        code='CHILD',
        name='Child Category',
        organization=self.organization,
        parent=parent,
        level=2,
        created_by=self.user
    )

    self.request.organization_id = self.organization.id
    response = self.viewset.path(self.request, pk=str(child.id))
    self.assertEqual(response.status_code, 200)
```

**Step 5: Run tests**

Run: `docker-compose exec backend python manage.py test apps.assets.tests.test_category_api -v 2`

Expected: PASS

**Step 6: Commit**

```bash
git add backend/apps/assets/viewsets/category.py backend/apps/assets/services/category_service.py
git commit -m "feat(assets): add category tree and path endpoints"
```

---

## Task 3: Add Department Tree Endpoint

**Files:**
- Create: `backend/apps/organizations/viewsets/department_viewsets.py`
- Test: `backend/apps/organizations/tests/test_department_api.py`

**Step 1: Check if department ViewSet exists**

Run: `ls -la backend/apps/organizations/viewsets/`

Expected: May need to create ViewSet for departments.

**Step 2: Create DepartmentViewSet**

Create `backend/apps/organizations/viewsets/department_viewsets.py`:

```python
"""
ViewSets for Department management.
"""
from rest_framework.decorators import action
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.responses.base import BaseResponse
from apps.organizations.models import Department
from apps.organizations.serializers import (
    DepartmentListSerializer,
    DepartmentDetailSerializer,
    DepartmentCreateSerializer,
)


class DepartmentViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Department management.

    Provides:
    - Standard CRUD operations
    - Tree endpoint for hierarchical data
    - Path endpoint for breadcrumbs
    """

    queryset = Department.objects.filter(is_deleted=False)
    serializer_class = DepartmentDetailSerializer

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return DepartmentListSerializer
        if self.action == 'create':
            return DepartmentCreateSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['get'], url_path='tree')
    def tree(self, request):
        """
        Get complete department tree for current organization.

        GET /api/organizations/departments/tree/

        Returns hierarchical tree structure.
        """
        from apps.organizations.services.department_service import DepartmentService

        organization_id = getattr(request, 'organization_id', None)

        if not organization_id:
            return BaseResponse.error(
                code='UNAUTHORIZED',
                message='Organization context required'
            )

        service = DepartmentService()
        tree_data = service.get_tree(organization_id)

        return BaseResponse.success(
            data=tree_data,
            message='Department tree retrieved successfully'
        )

    @action(detail=True, methods=['get'], url_path='path')
    def path(self, request, pk=None):
        """
        Get breadcrumb path for a department.

        GET /api/organizations/departments/{id}/path/
        """
        from apps.organizations.services.department_service import DepartmentService

        department = self.get_object()
        service = DepartmentService()
        path_data = service.get_department_path(department.id)

        return BaseResponse.success(
            data=path_data,
            message='Department path retrieved successfully'
        )

    @action(detail=False, methods=['get'], url_path='select-options')
    def select_options(self, request):
        """
        Get departments formatted for select component.

        GET /api/organizations/departments/select-options/

        Returns flat list with id, name, and path for display.
        """
        from apps.organizations.services.department_service import DepartmentService

        organization_id = getattr(request, 'organization_id', None)

        if not organization_id:
            return BaseResponse.error(
                code='UNAUTHORIZED',
                message='Organization context required'
            )

        service = DepartmentService()
        options = service.get_select_options(organization_id)

        return BaseResponse.success(
            data=options,
            message='Department options retrieved successfully'
        )
```

**Step 3: Add service methods**

Add to `backend/apps/organizations/services/department_service.py`:

```python
def get_tree(self, organization_id):
    """Get full department tree for organization."""
    from apps.organizations.models import Department

    def build_tree(parent_id=None):
        departments = Department.objects.filter(
            organization_id=organization_id,
            parent_id=parent_id,
            is_deleted=False
        ).order_by('sort_order', 'name')

        result = []
        for dept in departments:
            children = build_tree(dept.id)
            result.append({
                'id': str(dept.id),
                'code': dept.code,
                'name': dept.name,
                'level': dept.level,
                'children': children
            })
        return result

    return build_tree()

def get_department_path(self, department_id):
    """Get breadcrumb path from root to department."""
    from apps.organizations.models import Department

    department = Department.objects.get(id=department_id)
    path = []
    current = department

    while current:
        path.append({
            'id': str(current.id),
            'code': current.code,
            'name': current.name
        })
        current = current.parent

    return list(reversed(path))

def get_select_options(self, organization_id):
    """Get departments formatted for select dropdown."""
    from apps.organizations.models import Department

    departments = Department.objects.filter(
        organization_id=organization_id,
        is_deleted=False
    ).order_by('level', 'sort_order', 'name')

    options = []
    for dept in departments:
        path = self.get_department_path(dept.id)
        path_name = ' / '.join([p['name'] for p in path])
        options.append({
            'value': str(dept.id),
            'label': path_name,
            'code': dept.code
        })

    return options
```

**Step 4: Update URLs**

Update `backend/apps/organizations/urls.py`:

```python
from apps.organizations.viewsets import DepartmentViewSet

router.register(r'departments', DepartmentViewSet, basename='department')
```

**Step 5: Add tests**

Create `backend/apps/organizations/tests/test_department_api.py`:

```python
import pytest
from django.urls import reverse
from apps.organizations.models import Department


@pytest.mark.django_db
class TestDepartmentViewSet:
    def test_tree_endpoint(self, auth_client, organization):
        """Test department tree retrieval."""
        parent = Department.objects.create(
            code='HQ',
            name='Headquarters',
            organization=organization,
            level=1
        )
        child = Department.objects.create(
            code='IT',
            name='IT Department',
            organization=organization,
            parent=parent,
            level=2
        )

        url = reverse('department-tree')
        response = auth_client.get(url)
        assert response.status_code == 200
        assert len(response.json()['data']) == 1

    def test_select_options(self, auth_client, organization):
        """Test select options endpoint."""
        Department.objects.create(
            code='HQ',
            name='Headquarters',
            organization=organization,
            level=1
        )

        url = reverse('department-select-options')
        response = auth_client.get(url)
        assert response.status_code == 200
        assert len(response.json()['data']) == 1
```

**Step 6: Run tests**

Run: `docker-compose exec backend python manage.py test apps.organizations.tests.test_department_api -v 2`

Expected: PASS

**Step 7: Commit**

```bash
git add backend/apps/organizations/viewsets/department_viewsets.py
git add backend/apps/organizations/services/department_service.py
git add backend/apps/organizations/urls.py
git add backend/apps/organizations/tests/test_department_api.py
git commit -m "feat(organizations): add department tree and select endpoints"
```

---

## Task 4: Add User Selector Endpoint

**Files:**
- Create: `backend/apps/accounts/viewsets/user_selector_viewsets.py`
- Test: `backend/apps/accounts/tests/test_user_selector_api.py`

**Step 1: Create user selector ViewSet**

Create `backend/apps/accounts/viewsets/user_selector_viewsets.py`:

```python
"""
ViewSets for User selection components.
"""
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from apps.common.viewsets.base import BaseModelViewSet
from apps.common.responses.base import BaseResponse
from apps.accounts.models import User


class UserSelectorViewSet(BaseModelViewSet):
    """
    ViewSet for user selection in forms.

    Provides optimized endpoints for:
    - User search/autocomplete
    - User selection by department
    - Current user info
    """

    permission_classes = [IsAuthenticated]
    queryset = User.objects.filter(is_deleted=False)

    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        """
        Search users by name or username.

        GET /api/users/selector/search/?q=keyword&department_id=xxx

        Query params:
        - q: Search keyword (username, full name, email)
        - department_id: Filter by department
        - limit: Max results (default 50)
        """
        from apps.accounts.serializers import UserSelectorSerializer

        keyword = request.query_params.get('q', '')
        department_id = request.query_params.get('department_id')
        limit = int(request.query_params.get('limit', 50))

        organization_id = getattr(request, 'organization_id', None)

        queryset = User.objects.filter(
            is_deleted=False,
            is_active=True,
            organization_id=organization_id
        )

        if keyword:
            queryset = queryset.filter(
                username__icontains=keyword
            ) | queryset.filter(
                full_name__icontains=keyword
            ) | queryset.filter(
                email__icontains=keyword
            )

        if department_id:
            queryset = queryset.filter(department_id=department_id)

        users = queryset[:limit]
        serializer = UserSelectorSerializer(users, many=True)

        return BaseResponse.success(
            data=serializer.data,
            message='Users retrieved successfully'
        )

    @action(detail=False, methods=['get'], url_path='by-department/(?P<department_id>[^/.]+)')
    def by_department(self, request, department_id=None):
        """
        Get users in a specific department.

        GET /api/users/selector/by-department/{department_id}/
        """
        from apps.accounts.serializers import UserSelectorSerializer

        organization_id = getattr(request, 'organization_id', None)

        users = User.objects.filter(
            is_deleted=False,
            is_active=True,
            organization_id=organization_id,
            department_id=department_id
        )

        serializer = UserSelectorSerializer(users, many=True)

        return BaseResponse.success(
            data=serializer.data,
            message='Department users retrieved successfully'
        )

    @action(detail=False, methods=['get'], url_path='current')
    def current(self, request):
        """
        Get current user info.

        GET /api/users/selector/current/
        """
        from apps.accounts.serializers import UserSelectorSerializer

        serializer = UserSelectorSerializer(request.user)

        return BaseResponse.success(
            data=serializer.data,
            message='Current user retrieved successfully'
        )
```

**Step 2: Create UserSelectorSerializer**

Add to `backend/apps/accounts/serializers/`:

```python
class UserSelectorSerializer(serializers.ModelSerializer):
    """Lightweight serializer for user selection."""

    label = serializers.SerializerMethodField()
    value = serializers.CharField(source='id')

    class Meta:
        model = User
        fields = ['value', 'username', 'full_name', 'email', 'label',
                  'department', 'avatar_url']

    def get_label(self, obj):
        """Display label for select component."""
        if obj.full_name:
            return f"{obj.full_name} ({obj.username})"
        return obj.username
```

**Step 3: Update URLs**

Add to `backend/apps/accounts/urls.py`:

```python
from apps.accounts.viewsets.user_selector_viewsets import UserSelectorViewSet

router.register(r'selector', UserSelectorViewSet, basename='user-selector')
```

**Step 4: Add tests**

Create `backend/apps/accounts/tests/test_user_selector_api.py`:

```python
import pytest
from django.urls import reverse
from apps.accounts.models import User


@pytest.mark.django_db
class TestUserSelectorViewSet:
    def test_search_users(self, auth_client, organization):
        """Test user search endpoint."""
        User.objects.create_user(
            username='john.doe',
            email='john@example.com',
            full_name='John Doe',
            organization=organization
        )

        url = reverse('user-selector-search')
        response = auth_client.get(url, {'q': 'john'})
        assert response.status_code == 200
        assert len(response.json()['data']) >= 1

    def test_current_user(self, auth_client):
        """Test current user endpoint."""
        url = reverse('user-selector-current')
        response = auth_client.get(url)
        assert response.status_code == 200
        assert 'value' in response.json()['data']
```

**Step 5: Run tests**

Run: `docker-compose exec backend python manage.py test apps.accounts.tests.test_user_selector_api -v 2`

Expected: PASS

**Step 6: Commit**

```bash
git add backend/apps/accounts/viewsets/user_selector_viewsets.py
git add backend/apps/accounts/urls.py
git add backend/apps/accounts/tests/test_user_selector_api.py
git commit -m "feat(accounts): add user selector endpoints"
```

---

## Task 5: Complete Workflow Integration for Asset Operations

**Files:**
- Modify: `backend/apps/assets/services/operation_service.py`
- Test: `backend/apps/assets/tests/test_operation_workflow.py`

**Step 1: Add workflow trigger to pickup creation**

Modify `AssetPickupService.create_with_items` in `backend/apps/assets/services/operation_service.py`:

```python
def create_with_items(self, data, items_data, user, organization_id):
    """Create pickup order with items and optionally start workflow."""
    from apps.workflows.services import WorkflowEngine

    # Create pickup
    pickup = AssetPickup.objects.create(
        **data,
        organization_id=organization_id,
        created_by=user
    )

    # Create items
    for item_data in items_data:
        PickupItem.objects.create(
            pickup=pickup,
            **item_data
        )

    # Auto-start workflow if configured
    try:
        definition = WorkflowDefinition.objects.get(
            business_object_code='asset_pickup',
            is_active=True,
            is_deleted=False
        )
        engine = WorkflowEngine(definition)
        engine.start_workflow(
            definition=definition,
            business_object_code='asset_pickup',
            business_id=str(pickup.id),
            business_no=pickup.pickup_no,
            initiator=user,
            variables={'amount': pickup.estimated_value}
        )
    except WorkflowDefinition.DoesNotExist:
        # No workflow configured, continue without workflow
        pass

    return pickup
```

**Step 2: Add workflow status to operation serializers**

Add to `backend/apps/assets/serializers/operation.py`:

```python
class AssetPickupDetailSerializer(BaseModelSerializer):
    """Detail serializer including workflow status."""
    workflow_status = serializers.SerializerMethodField()
    current_task = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = AssetPickup
        fields = BaseModelSerializer.Meta.fields + [
            'pickup_no', 'pickup_type', 'applicant', 'department',
            'expected_date', 'estimated_value', 'actual_date',
            'workflow_status', 'current_task'
        ]

    def get_workflow_status(self, obj):
        """Get workflow instance status if exists."""
        from apps.workflows.models import WorkflowInstance
        try:
            instance = WorkflowInstance.objects.get(
                business_object_code='asset_pickup',
                business_id=str(obj.id),
                is_deleted=False
            )
            return {
                'id': str(instance.id),
                'status': instance.status,
                'current_node': instance.current_node_name
            }
        except WorkflowInstance.DoesNotExist:
            return None

    def get_current_task(self, obj):
        """Get current pending workflow task."""
        from apps.workflows.models import WorkflowTask
        try:
            instance = WorkflowInstance.objects.get(
                business_object_code='asset_pickup',
                business_id=str(obj.id),
                is_deleted=False
            )
            task = WorkflowTask.objects.filter(
                instance=instance,
                status='pending',
                is_deleted=False
            ).first()

            if task:
                return {
                    'id': str(task.id),
                    'node_name': task.node_name,
                    'assignee': task.assignee.get_full_name() if task.assignee else None
                }
        except Exception:
            pass
        return None
```

**Step 3: Add tests**

Create `backend/apps/assets/tests/test_operation_workflow.py`:

```python
import pytest
from apps.assets.models import AssetPickup, PickupItem
from apps.workflows.models import WorkflowDefinition


@pytest.mark.django_db
class TestOperationWorkflowIntegration:
    def test_pickup_starts_workflow(self, user, organization):
        """Test that pickup creation starts workflow."""
        # Create workflow definition
        definition = WorkflowDefinition.objects.create(
            name='Asset Pickup Approval',
            business_object_code='asset_pickup',
            organization=organization,
            definition_json={},
            created_by=user
        )

        # Create pickup
        service = AssetPickupService()
        pickup = service.create_with_items(
            data={
                'pickup_no': 'PICKUP-001',
                'pickup_type': 'department',
                'applicant': user,
                'department': user.department,
                'expected_date': '2024-12-31'
            },
            items_data=[],
            user=user,
            organization_id=str(organization.id)
        )

        # Verify workflow started
        assert hasattr(pickup, 'workflow_instance')
```

**Step 4: Run tests**

Run: `docker-compose exec backend python manage.py test apps.assets.tests.test_operation_workflow -v 2`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/apps/assets/services/operation_service.py
git add backend/apps/assets/serializers/operation.py
git add backend/apps/assets/tests/test_operation_workflow.py
git commit -m "feat(assets): integrate workflow engine with asset operations"
```

---

## Task 6: Add Notification System Endpoints

**Files:**
- Create: `backend/apps/notifications/viewsets/notification_viewsets.py`
- Create: `backend/apps/notifications/services/notification_service.py`
- Test: `backend/apps/notifications/tests/test_api.py`

**Step 1: Create NotificationViewSet**

Create `backend/apps/notifications/viewsets/notification_viewsets.py`:

```python
"""
ViewSets for Notification management.
"""
from rest_framework.decorators import action
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.responses.base import BaseResponse
from apps.notifications.models import Notification
from apps.notifications.serializers import (
    NotificationListSerializer,
    NotificationDetailSerializer,
)


class NotificationViewSet(BaseModelViewSetWithBatch):
    """
    ViewSet for Notification management.

    Provides:
    - List user notifications
    - Mark as read
    - Mark all as read
    - Get unread count
    """

    queryset = Notification.objects.filter(is_deleted=False)
    serializer_class = NotificationDetailSerializer

    def get_queryset(self):
        """Only show notifications for current user."""
        qs = super().get_queryset()
        return qs.filter(recipient=self.request.user)

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return NotificationListSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """
        Get unread notification count.

        GET /api/notifications/unread-count/
        """
        count = self.get_queryset().filter(is_read=False).count()

        return BaseResponse.success(
            data={'count': count},
            message='Unread count retrieved successfully'
        )

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """
        Mark notification as read.

        POST /api/notifications/{id}/mark-read/
        """
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()

        return BaseResponse.success(
            data=NotificationDetailSerializer(notification).data,
            message='Notification marked as read'
        )

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """
        Mark all notifications as read.

        POST /api/notifications/mark-all-read/
        """
        count = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )

        return BaseResponse.success(
            data={'marked_count': count},
            message=f'{count} notifications marked as read'
        )
```

**Step 2: Create notification service**

Create `backend/apps/notifications/services/notification_service.py`:

```python
"""
Service for creating and sending notifications.
"""
from typing import List, Dict
from django.utils import timezone
from apps.notifications.models import Notification, NotificationTemplate


class NotificationService:
    """Service for notification management."""

    def create_notification(
        self,
        recipient,
        title: str,
        message: str,
        notification_type: str = 'system',
        action_url: str = None,
        metadata: Dict = None
    ) -> Notification:
        """
        Create a notification for a user.

        Args:
            recipient: User instance
            title: Notification title
            message: Notification message
            notification_type: Type of notification
            action_url: Optional URL to navigate on click
            metadata: Optional additional data

        Returns:
            Created Notification instance
        """
        notification = Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            action_url=action_url,
            metadata=metadata or {},
            organization_id=recipient.organization_id
        )

        return notification

    def create_bulk_notifications(
        self,
        recipients: List,
        title: str,
        message: str,
        notification_type: str = 'system',
        action_url: str = None,
        metadata: Dict = None
    ) -> List[Notification]:
        """Create notifications for multiple users."""
        notifications = []

        for recipient in recipients:
            notifications.append(
                Notification(
                    recipient=recipient,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    action_url=action_url,
                    metadata=metadata or {},
                    organization_id=recipient.organization_id
                )
            )

        return Notification.objects.bulk_create(notifications)

    def send_workflow_notification(
        self,
        workflow_task,
        action: str
    ):
        """
        Send notification for workflow task.

        Args:
            workflow_task: WorkflowTask instance
            action: Action type ('assigned', 'approved', 'rejected', 'returned')
        """
        from apps.workflows.models import WorkflowInstance

        instance = workflow_task.instance
        assignee = workflow_task.assignee

        if action == 'assigned':
            title = f'New Task: {workflow_task.node_name}'
            message = f'You have been assigned to "{instance.title or instance.definition.name}"'
            action_url = f'/workflow/tasks/{workflow_task.id}'

        elif action == 'approved':
            title = f'Task Approved: {workflow_task.node_name}'
            message = f'Your task has been approved'
            action_url = f'/workflow/instances/{instance.id}'

        elif action == 'rejected':
            title = f'Task Rejected: {workflow_task.node_name}'
            message = f'Your task has been rejected'
            action_url = f'/workflow/instances/{instance.id}'

        else:  # returned
            title = f'Task Returned: {workflow_task.node_name}'
            message = f'Your task has been returned for revision'
            action_url = f'/workflow/tasks/{workflow_task.id}'

        self.create_notification(
            recipient=assignee,
            title=title,
            message=message,
            notification_type='workflow',
            action_url=action_url,
            metadata={
                'workflow_instance_id': str(instance.id),
                'workflow_task_id': str(workflow_task.id)
            }
        )
```

**Step 3: Create models and serializers**

Check if `backend/apps/notifications/models.py` exists:

```python
from apps.common.models import BaseModel
from django.db import models


class Notification(BaseModel):
    """User notification model."""

    NOTIFICATION_TYPES = [
        ('system', 'System'),
        ('workflow', 'Workflow'),
        ('asset', 'Asset'),
        ('inventory', 'Inventory'),
    ]

    recipient = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='system'
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    action_url = models.URLField(max_length=500, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
```

**Step 4: Add tests**

Create `backend/apps/notifications/tests/test_api.py`:

```python
import pytest
from django.urls import reverse
from apps.notifications.models import Notification


@pytest.mark.django_db
class TestNotificationViewSet:
    def test_list_notifications(self, auth_client, user):
        """Test listing notifications."""
        Notification.objects.create(
            recipient=user,
            title='Test Notification',
            message='Test message',
            organization=user.organization
        )

        url = reverse('notification-list')
        response = auth_client.get(url)
        assert response.status_code == 200
        assert len(response.json()['data']) >= 1

    def test_unread_count(self, auth_client, user):
        """Test unread count endpoint."""
        Notification.objects.create(
            recipient=user,
            title='Unread Notification',
            message='Unread message',
            is_read=False,
            organization=user.organization
        )

        url = reverse('notification-unread-count')
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.json()['data']['count'] >= 1

    def test_mark_read(self, auth_client, user):
        """Test marking notification as read."""
        notification = Notification.objects.create(
            recipient=user,
            title='Test',
            message='Test',
            is_read=False,
            organization=user.organization
        )

        url = reverse('notification-mark-read', kwargs={'pk': notification.id})
        response = auth_client.post(url)
        assert response.status_code == 200

        notification.refresh_from_db()
        assert notification.is_read is True
```

**Step 5: Run tests**

Run: `docker-compose exec backend python manage.py test apps.notifications.tests.test_api -v 2`

Expected: PASS

**Step 6: Commit**

```bash
git add backend/apps/notifications/
git commit -m "feat(notifications): add notification system with API endpoints"
```

---

## Task 7: Complete Asset Export API

**Files:**
- Modify: `backend/apps/assets/viewsets/asset.py`
- Test: `backend/apps/assets/tests/test_export_api.py`

**Step 1: Add export endpoint**

Add to `AssetViewSet` in `backend/apps/assets/viewsets/asset.py`:

```python
@action(detail=False, methods=['post'], url_path='export')
def export_assets(self, request):
    """
    Export assets to Excel file.

    POST /api/assets/export/
    Body:
    {
        "filters": {...},  // Optional filters
        "columns": ["asset_code", "asset_name", ...]  // Optional columns
    }

    Returns an Excel file.
    """
    import openpyxl
    from openpyxl.styles import Font, Alignment
    from django.http import HttpResponse
    from io import BytesIO

    organization_id = getattr(request, 'organization_id', None)

    # Get queryset
    queryset = Asset.objects.filter(
        organization_id=organization_id,
        is_deleted=False
    )

    # Apply filters if provided
    filters = request.data.get('filters', {})
    for key, value in filters.items():
        if hasattr(Asset, key):
            queryset = queryset.filter(**{key: value})

    # Default columns to export
    default_columns = [
        'asset_code', 'asset_name', 'specification',
        'brand', 'model', 'asset_category', 'department',
        'location', 'custodian', 'asset_status',
        'purchase_price', 'purchase_date'
    ]
    columns = request.data.get('columns', default_columns)

    # Create workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Assets'

    # Write headers
    headers = [col.replace('_', ' ').title() for col in columns]
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')

    # Write data
    for row_num, asset in enumerate(queryset, 2):
        for col_num, field in enumerate(columns, 1):
            value = getattr(asset, field, None)

            # Handle foreign keys
            if hasattr(value, 'name'):
                value = value.name
            elif hasattr(value, 'username'):
                value = value.username
            elif value and hasattr(value, 'isoformat'):
                value = value.isoformat()

            ws.cell(row=row_num, column=col_num, value=value)

    # Save to BytesIO
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    response = HttpResponse(
        buffer.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="assets_export.xlsx"'

    return response
```

**Step 2: Add tests**

Create `backend/apps/assets/tests/test_export_api.py`:

```python
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestAssetExportAPI:
    def test_export_assets(self, auth_client, organization, user):
        """Test asset export endpoint."""
        from apps.assets.models import Asset

        Asset.objects.create(
            asset_code='TEST001',
            asset_name='Test Asset',
            organization=organization,
            created_by=user
        )

        url = reverse('asset-export-assets')
        response = auth_client.post(url)
        assert response.status_code == 200
        assert response['content-type'] == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
```

**Step 3: Run tests**

Run: `docker-compose exec backend python manage.py test apps.assets.tests.test_export_api -v 2`

Expected: PASS

**Step 4: Commit**

```bash
git add backend/apps/assets/viewsets/asset.py
git add backend/apps/assets/tests/test_export_api.py
git commit -m "feat(assets): add asset export to Excel endpoint"
```

---

## Task 8: Fix Inventory Scan API Integration

**Files:**
- Modify: `backend/apps/inventory/viewsets/scan_viewsets.py`
- Test: `backend/apps/inventory/tests/test_scan_api.py`

**Step 1: Add batch scan endpoint**

Add to `InventoryScanViewSet` in `backend/apps/inventory/viewsets/scan_viewsets.py`:

```python
@action(detail=False, methods=['post'], url_path='batch')
def batch_scan(self, request):
    """
    Batch create scan records from mobile device.

    POST /api/inventory/scans/batch/
    Body:
    {
        "task_id": "uuid",
        "scans": [
            {"qr_code": "...", "rfid_code": "...", "actual_location": "..."},
            ...
        ]
    }
    """
    from apps.inventory.services import ScanService

    serializer = InventoryScanBatchSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    task_id = serializer.validated_data['task_id']
    scans_data = serializer.validated_data['scans']

    service = ScanService()
    results = service.batch_create_scans(
        task_id=task_id,
        scans_data=scans_data,
        scanner=request.user
    )

    return BaseResponse.success(
        data=results,
        message=f'{results["created"]} scans created, {results["updated"]} updated'
    )

@action(detail=False, methods=['get'], url_path='by-task/(?P<task_id>[^/.]+)')
def by_task(self, request, task_id=None):
    """
    Get all scans for a task.

    GET /api/inventory/scans/by-task/{task_id}/
    """
    from apps.inventory.services import ScanService
    from apps.inventory.serializers import InventoryScanSerializer

    service = ScanService()
    scans = service.get_task_scans(task_id)

    serializer = InventoryScanSerializer(scans, many=True)

    return BaseResponse.success(
        data=serializer.data,
        message='Task scans retrieved successfully'
    )
```

**Step 2: Create serializer**

Add to `backend/apps/inventory/serializers/`:

```python
class InventoryScanBatchSerializer(serializers.Serializer):
    """Serializer for batch scan operations."""
    task_id = serializers.UUIDField(required=True)
    scans = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )

    def validate_task_id(self, value):
        """Validate that task exists and is in progress."""
        from apps.inventory.models import InventoryTask

        try:
            task = InventoryTask.objects.get(id=value, is_deleted=False)
            if task.task_status not in ['in_progress', 'pending']:
                raise serializers.ValidationError(
                    'Task must be in progress or pending status'
                )
        except InventoryTask.DoesNotExist:
            raise serializers.ValidationError('Task not found')

        return value
```

**Step 3: Add tests**

Create `backend/apps/inventory/tests/test_scan_api.py`:

```python
import pytest
from django.urls import reverse
from apps.inventory.models import InventoryTask, InventoryScan


@pytest.mark.django_db
class TestInventoryScanAPI:
    def test_batch_scan(self, auth_client, organization, user):
        """Test batch scan endpoint."""
        task = InventoryTask.objects.create(
            task_code='INV-001',
            task_name='Test Inventory',
            task_status='in_progress',
            organization=organization,
            created_by=user
        )

        url = reverse('inventory-scan-batch')
        response = auth_client.post(url, {
            'task_id': str(task.id),
            'scans': [
                {'qr_code': 'QR123', 'actual_location': 'Office A'}
            ]
        })
        assert response.status_code == 200
```

**Step 4: Run tests**

Run: `docker-compose exec backend python manage.py test apps.inventory.tests.test_scan_api -v 2`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/apps/inventory/viewsets/scan_viewsets.py
git add backend/apps/inventory/serializers/
git add backend/apps/inventory/tests/test_scan_api.py
git commit -m "feat(inventory): add batch scan and task scan endpoints"
```

---

## Task 9: Add Pagination Consistency Fix

**Files:**
- Modify: `backend/apps/common/viewsets/base.py`

**Step 1: Fix paginated response format**

The current `deleted()` method returns plain DRF pagination format.
Update to use BaseResponse format.

**Step 2: Update BaseModelViewSet.deleted method**

Replace `deleted()` method in `backend/apps/common/viewsets/base.py`:

```python
@action(detail=False, methods=['get'])
def deleted(self, request):
    """
    List soft-deleted records.

    GET /api/{resource}/deleted/
    """
    from rest_framework.pagination import PageNumberPagination

    # Get all deleted records (user must have permission)
    queryset = self.queryset.model.all_objects.filter(is_deleted=True)

    # Paginate
    paginator = PageNumberPagination()
    page = paginator.paginate_queryset(queryset, request)

    serializer = self.get_serializer(page, many=True)

    return Response({
        'success': True,
        'data': {
            'count': queryset.count(),
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'results': serializer.data
        }
    })
```

**Step 3: Add tests**

```python
def test_deleted_pagination(self):
    """Test that deleted records endpoint returns proper pagination."""
    # Create and soft delete some records
    asset1 = Asset.objects.create(
        asset_code='TEST001',
        asset_name='Test 1',
        organization=self.organization,
        created_by=self.user
    )
    asset1.soft_delete(self.user)

    asset2 = Asset.objects.create(
        asset_code='TEST002',
        asset_name='Test 2',
        organization=self.organization,
        created_by=self.user
    )
    asset2.soft_delete(self.user)

    # Call deleted endpoint
    response = self.client.get('/api/assets/deleted/')
    self.assertEqual(response.status_code, 200)
    self.assertIn('data', response.json())
    self.assertIn('count', response.json()['data'])
    self.assertEqual(response.json()['data']['count'], 2)
```

**Step 4: Run tests**

Run: `docker-compose exec backend python manage.py test apps.common.tests.test_viewsets -v 2`

Expected: PASS

**Step 5: Commit**

```bash
git add backend/apps/common/viewsets/base.py
git commit -m "fix(common): standardize deleted endpoint pagination format"
```

---

## Task 10: Add API Documentation

**Files:**
- Create: `backend/docs/API.md`

**Step 1: Create API documentation**

Create comprehensive API documentation:

```markdown
# GZEAMS Backend API Documentation

## Base URL
```
http://localhost:8000/api/
```

## Authentication
All endpoints require authentication via JWT token.

### Headers
```
Authorization: Bearer <token>
```

## Response Format

### Success Response
```json
{
    "success": true,
    "message": "Operation successful",
    "data": { ... }
}
```

### Paginated Response
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": "...",
        "previous": "...",
        "results": [ ... ]
    }
}
```

### Error Response
```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Error description",
        "details": { ... }
    }
}
```

## Endpoints

### Assets

#### List Assets
```
GET /api/assets/
```

Query params:
- `page`: Page number
- `page_size`: Items per page
- `search`: Search in code, name
- `asset_category_id`: Filter by category
- `department_id`: Filter by department
- `asset_status`: Filter by status
- `location_id`: Filter by location

#### Get Asset QR Code
```
GET /api/assets/{id}/qr_code/
```
Returns PNG image.

#### Bulk Generate QR Codes
```
POST /api/assets/bulk-qr-codes/
Body: { "ids": ["uuid1", "uuid2"] }
```
Returns ZIP file.

#### Export Assets
```
POST /api/assets/export/
Body: { "filters": {}, "columns": [] }
```
Returns Excel file.

### Categories

#### Get Category Tree
```
GET /api/assets/categories/tree/
```

#### Get Category Path
```
GET /api/assets/categories/{id}/path/
```

### Operations

#### Create Pickup
```
POST /api/assets/pickups/
Body: {
    "pickup_no": "LY-2024-001",
    "pickup_type": "department",
    "department_id": "uuid",
    "items": [...]
}
```

#### Submit for Approval
```
POST /api/assets/pickups/{id}/submit/
```

#### Approve Pickup
```
POST /api/assets/pickups/{id}/approve/
Body: {
    "approval": "approved",
    "comment": "Optional comment"
}
```

### Inventory

#### List Tasks
```
GET /api/inventory/tasks/
```

#### Start Task
```
POST /api/inventory/tasks/{id}/start/
```

#### Complete Task
```
POST /api/inventory/tasks/{id}/complete/
```

#### Batch Scan
```
POST /api/inventory/scans/batch/
Body: {
    "task_id": "uuid",
    "scans": [...]
}
```

### Workflows

#### My Tasks
```
GET /api/workflows/tasks/my_tasks/
```

#### Approve Task
```
POST /api/workflows/tasks/{id}/approve/
Body: { "comment": "..." }
```

### Users

#### Search Users
```
GET /api/accounts/selector/search/?q=keyword
```

#### Users by Department
```
GET /api/accounts/selector/by-department/{department_id}/
```

### Departments

#### Department Tree
```
GET /api/organizations/departments/tree/
```

#### Department Select Options
```
GET /api/organizations/departments/select-options/
```

### Notifications

#### Unread Count
```
GET /api/notifications/unread-count/
```

#### Mark as Read
```
POST /api/notifications/{id}/mark-read/
```

#### Mark All as Read
```
POST /api/notifications/mark-all-read/
```
```

**Step 2: Commit**

```bash
git add backend/docs/API.md
git commit -m "docs: add comprehensive API documentation"
```

---

## Summary

This plan addresses:

1. ✅ QR Code generation (single and bulk)
2. ✅ Category tree endpoint
3. ✅ Department tree endpoint
4. ✅ User selector endpoints
5. ✅ Workflow integration for operations
6. ✅ Notification system
7. ✅ Asset export API
8. ✅ Inventory scan batching
9. ✅ Pagination consistency

Total estimated effort: **10-12 days** for one backend developer.

---

**Plan complete and saved to `docs/plans/2026-01-23-backend-fix-implementation-plan.md`.**

Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

Which approach?
