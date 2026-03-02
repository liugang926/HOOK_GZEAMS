# Backend Test Fixes and Development Continuation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix remaining 46 test failures (test isolation issues) and continue backend module development

**Architecture:**
- Fix test data isolation using pytest fixtures and database cleanup
- Complete remaining ViewSets with proper BaseResponse wrapping
- Add missing service layer implementations

**Tech Stack:** Django 5.0, DRF, pytest, PostgreSQL, BaseModel pattern

---

## Current Status

**Passing:** 688 tests (93.7%)
**Failing:** 46 tests

**Failure Breakdown:**
- `apps/assets/tests/test_api.py`: 9 failures (test isolation - pass individually)
- `apps/assets/tests/test_asset_models.py`: 2 failures (SequenceService not seeded)
- `apps/assets/tests/test_asset_services.py`: 1 failure (related to above)
- `apps/consumables/tests/test_api.py`: 11 failures (test data conflicts)
- `apps/inventory/tests/test_api.py`: 7 failures (similar isolation issues)
- `apps/workflows/tests/test_api.py`: 14 failures (test isolation)
- `apps/accounts/tests/test_services.py`: 1 failure
- `apps/permissions/tests/test_models.py`: 1 failure

---

## Task 1: Fix Test Data Isolation with Pytest Fixtures

**Problem:** Tests pass individually but fail when run together due to shared test data (duplicate codes, conflicting IDs).

**Files:**
- Create: `backend/apps/conftest.py`
- Modify: Test files that use hardcoded codes

**Step 1: Create global conftest.py with database cleanup**

```python
# In backend/apps/conftest.py:

import pytest
from django.core.management import call_command

@pytest.fixture(autouse=True)
def reset_database afterEach_test(db, request):
    """Clean up database after each test to ensure isolation."""
    yield
    # After each test, reset sequences to avoid ID conflicts
    call_command('reset_sequences', '--noinput')
```

**Step 2: Add reset_sequences command**

```python
# In backend/apps/management/commands/reset_sequences.py:

from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Reset database sequences to avoid ID conflicts in tests'

    def handle(self, *args, **options):
        # Get all sequence names
        with connection.cursor() as cursor:
            # Get table names
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
            """)
            tables = [row[0] for row in cursor.fetchall()]

            # Reset sequences for each table
            for table in tables:
                try:
                    cursor.execute(f"ALTER SEQUENCE {table}_id_seq RESTART WITH 1")
                    self.stdout.write(f"Reset sequence for {table}")
                except:
                    pass  # Table may not have a sequence
```

**Step 3: Update test files to use unique data generation**

```python
# In each test file, use faker or UUID-based codes:

import uuid
from faker import Faker

fake = Faker()

def test_create_category(self):
    """Test POST /api/consumables/categories/"""
    url = '/api/consumables/categories/'
    data = {
        'code': f'CAT_{uuid.uuid4().hex[:8]}',  # Unique code
        'name': fake.name(),
        'unit': '件'
    }
    response = self.client.post(url, data, format='json')
    self.assertEqual(response.status_code, status.HTTP_201_CREATED)
```

**Step 4: Run tests to verify**

```bash
cd backend
./venv/Scripts/python.exe -m pytest apps/consumables/tests/test_api.py -v --tb=short
```

Expected: Reduced test conflicts

**Step 5: Commit**

```bash
git add apps/conftest.py apps/management/commands/reset_sequences.py
git commit -m "test: add database reset between tests for isolation"
```

---

## Task 2: Fix Asset Model Tests (SequenceService)

**Problem:** Asset code generation fails because SequenceService is not seeded in tests.

**Files:**
- Modify: `backend/apps/assets/tests/test_asset_models.py`

**Step 1: Add SequenceService seeding to test setup**

```python
# In apps/assets/tests/test_asset_models.py:

from django.test import TestCase
from apps.assets.models import Asset, AssetCategory
from apps.accounts.models import User
from apps.organizations.models import Organization
from apps.system.services import SequenceService, SequenceRule

class AssetModelTest(TestCase):
    """Test Asset model methods."""

    def setUp(self):
        """Set up test data with seeded sequences."""
        # Create organization
        self.org = Organization.objects.create(
            name='Test Company',
            code='TEST001',
            org_type='company'
        )

        # Seed sequence rule for asset codes
        sequence_rule, _ = SequenceRule.objects.get_or_create(
            code='ASSET_CODE',
            defaults={
                'name': 'Asset Code Sequence',
                'pattern': '{PREFIX}{YYYY}{MM}{SEQ}',
                'prefix': 'ZC',
                'seq_length': 4,
                'reset_period': 'monthly',
                'current_value': 0,
                'is_active': True,
                'organization_id': self.org.id
            }
        )
        sequence_rule.current_value = 0
        sequence_rule.save()
```

**Step 2: Run tests to verify**

```bash
./venv/Scripts/python.exe -m pytest apps/assets/tests/test_asset_models.py -v --tb=short
```

Expected: Asset code generation tests pass

**Step 3: Commit**

```bash
git add apps/assets/tests/test_asset_models.py
git commit -m "test: seed SequenceService in asset model tests"
```

---

## Task 3: Fix Consumables API Tests (Data Conflicts)

**Problem:** Consumable API tests fail with 409 CONFLICT due to duplicate codes.

**Files:**
- Modify: `backend/apps/consumables/tests/test_api.py`

**Step 1: Update tests to use UUID-based codes**

```python
# In apps/consumables/tests/test_api.py:

import uuid

class ConsumableCategoryAPITest(TestCase):
    """Test Consumable Category API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.org = Organization.objects.create(
            name=f'Test Company {uuid.uuid4().hex[:6]}',
            code=f'TEST{uuid.uuid4().hex[:6].upper()}',
            org_type='company'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{uuid.uuid4().hex[:6]}',
            email=f'test{uuid.uuid4().hex[:6]}@example.com',
            password='testpass123',
            organization=self.org
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.id))

    def test_list_categories(self):
        """Test GET /api/consumables/categories/"""
        # Use unique code
        code = f'CAT_{uuid.uuid4().hex[:8].upper()}'
        ConsumableCategory.objects.create(
            organization=self.org,
            code=code,
            name='Office Supplies',
            unit='件'
        )

        url = '/api/consumables/categories/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['data']['count'], 1)

    def test_create_category(self):
        """Test POST /api/consumables/categories/"""
        url = '/api/consumables/categories/'
        # Use unique code
        data = {
            'code': f'CAT_{uuid.uuid4().hex[:8].upper()}',
            'name': 'Electronics',
            'unit': '件'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
```

**Step 2: Run tests to verify**

```bash
./venv/Scripts/python.exe -m pytest apps/consumables/tests/test_api.py -v --tb=short
```

Expected: Reduced 409 CONFLICT errors

**Step 3: Commit**

```bash
git add apps/consumables/tests/test_api.py
git commit -m "test: use UUID-based codes in consumables API tests"
```

---

## Task 4: Fix Workflow Tests (Test Isolation)

**Problem:** Workflow tests fail when run in suite due to shared workflow instances.

**Files:**
- Modify: `backend/apps/workflows/tests/test_api.py`

**Step 1: Add setUp method for each test class**

```python
# In apps/workflows/tests/test_api.py:

import uuid

class WorkflowInstanceAPITest(TestCase):
    """Test Workflow Instance API endpoints."""

    def setUp(self):
        """Set up fresh data for each test."""
        self.org = Organization.objects.create(
            name=f'Test Org {uuid.uuid4().hex[:6]}',
            code=f'TEST{uuid.uuid4().hex[:6].upper()}',
            org_type='company'
        )
        self.admin = User.objects.create_superuser(
            username=f'admin_{uuid.uuid4().hex[:6]}',
            email=f'admin{uuid.uuid4().hex[:6]}@test.com',
            password='admin123',
            organization=self.org
        )
        self.user = User.objects.create_user(
            username=f'user_{uuid.uuid4().hex[:6]}',
            email=f'user{uuid.uuid4().hex[:6]}@test.com',
            password='testpass123',
            organization=self.org
        )

        # Create a fresh workflow definition for this test
        self.workflow_def = self._create_workflow_definition()
        self.workflow_instance = self._create_workflow_instance()

    def _create_workflow_definition(self):
        """Helper to create workflow definition."""
        from apps.workflows.models import WorkflowDefinition, WorkflowNode

        definition = WorkflowDefinition.objects.create(
            organization=self.org,
            name=f'Test Workflow {uuid.uuid4().hex[:6]}',
            code=f'WF_{uuid.uuid4().hex[:6].upper()}',
            version=1,
            definition_json={
                'nodes': [{
                    'id': 'start',
                    'type': 'start',
                    'position': {'x': 100, 'y': 100}
                }]
            },
            status='published',
            created_by=self.admin
        )
        return definition

    def _create_workflow_instance(self):
        """Helper to create workflow instance."""
        from apps.workflows.models import WorkflowInstance

        instance = WorkflowInstance.objects.create(
            organization=self.org,
            definition=self.workflow_def,
            title=f'Test Instance {uuid.uuid4().hex[:6]}',
            initiated_by=self.user,
            status='draft'
        )
        return instance
```

**Step 2: Run tests to verify**

```bash
./venv/Scripts/python.exe -m pytest apps/workflows/tests/test_api.py -v --tb=short
```

Expected: Workflow tests pass in suite

**Step 3: Commit**

```bash
git add apps/workflows/tests/test_api.py
git commit -m "test: fix workflow test isolation with unique data"
```

---

## Task 5: Fix Inventory API Tests

**Problem:** Inventory tests fail due to similar isolation issues.

**Files:**
- Modify: `backend/apps/inventory/tests/test_api.py`

**Step 1: Add database truncation to setUp**

```python
# In apps/inventory/tests/test_api.py:

import uuid

class InventoryTaskAPITests(TestCase):
    """Test Inventory Task API endpoints."""

    def setUp(self):
        """Set up fresh data for each test."""
        # Clean up any existing data
        InventoryTask.objects.all().delete()
        InventoryScan.objects.all().delete()
        Asset.objects.all().delete()

        self.org = Organization.objects.create(
            name=f'Test Org {uuid.uuid4().hex[:6]}',
            code=f'TEST{uuid.uuid4().hex[:6].upper()}',
            org_type='company'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{uuid.uuid4().hex[:6]}',
            email=f'test{uuid.uuid4().hex[:6]}@example.com',
            password='testpass123',
            organization=self.org
        )
        self.admin = User.objects.create_superuser(
            username=f'admin_{uuid.uuid4().hex[:6]}',
            email=f'admin{uuid.uuid4().hex[:6]}@test.com',
            password='admin123',
            organization=self.org
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_ORGANIZATION_ID=str(self.org.id))
```

**Step 2: Run tests to verify**

```bash
./venv/Scripts/python.exe -m pytest apps/inventory/tests/test_api.py -v --tb=short
```

Expected: Inventory tests pass

**Step 3: Commit**

```bash
git add apps/inventory/tests/test_api.py
git commit -m "test: fix inventory test isolation"
```

---

## Task 6: Add List/Create Response Wrappers to Remaining ViewSets

**Problem:** Some ViewSets still use DRF's default response format instead of BaseResponse wrapper.

**Files:**
- Modify: `backend/apps/inventory/viewsets/inventory_viewset.py`

**Step 1: Add create() and list() overrides**

```python
# In apps/inventory/viewsets/inventory_viewset.py:

from rest_framework import status
from apps.common.responses.base import BaseResponse

class InventoryTaskViewSet(BaseModelViewSetWithBatch):
    """ViewSet for Inventory Task operations."""

    # ... existing code ...

    def create(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        # Use detail serializer for response
        instance = serializer.instance
        detail_serializer = InventoryTaskDetailSerializer(instance)

        return BaseResponse.created(
            data=detail_serializer.data,
            message='Inventory task created successfully'
        )

    def list(self, request, *args, **kwargs):
        """Override to wrap response in standard format."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return BaseResponse.success(data=serializer.data)
```

**Step 2: Run tests to verify**

```bash
./venv/Scripts/python.exe -m pytest apps/inventory/tests/test_api.py -v --tb=short
```

**Step 3: Commit**

```bash
git add apps/inventory/viewsets/inventory_viewset.py
git commit -m "feat: add BaseResponse wrapper to inventory ViewSets"
```

---

## Task 7: Final Verification and Summary

**Files:**
- Test: All apps

**Step 1: Run full test suite**

```bash
cd backend
./venv/Scripts/python.exe -m pytest apps/ --tb=no -q
```

Expected: 710+ passing, < 20 failing (95%+ pass rate)

**Step 2: Run specific failing test suites individually**

```bash
# Test each module in isolation
./venv/Scripts/python.exe -m pytest apps/workflows/tests/test_api.py -v --tb=short
./venv/Scripts/python.exe -m pytest apps/assets/tests/test_api.py -v --tb=short
./venv/Scripts/python.exe -m pytest apps/consumables/tests/test_api.py -v --tb=short
./venv/Scripts/python.exe -m pytest apps/inventory/tests/test_api.py -v --tb=short
```

**Step 3: Document remaining issues**

Create `docs/reports/test_status_report.md` with:
- Current pass rate
- List of remaining failures by category
- Root cause analysis
- Recommended next steps

**Step 4: Final commit**

```bash
git add .
git commit -m "test: improve test isolation, achieve 95%+ pass rate"
```

---

## Summary

After completing this plan:
- Test pass rate should reach 95%+ (710+ / 746 tests)
- Test isolation issues will be resolved with proper cleanup
- All ViewSets will use consistent BaseResponse format
- Remaining failures will be well-documented for future fixes

**Estimated time:** 3-4 hours for all 7 tasks

**Next Steps After This Plan:**
1. Fix remaining integration issues
2. Add missing API endpoints
3. Improve test coverage for edge cases
4. Performance optimization
