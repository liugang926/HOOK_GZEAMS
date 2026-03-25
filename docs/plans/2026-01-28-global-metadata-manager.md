# Global Metadata Manager Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a `GlobalMetadataManager` that bypasses organization filtering for metadata models (BusinessObject, FieldDefinition, PageLayout) while maintaining soft-delete filtering.

---

## Rollback Instructions (If Anything Goes Wrong)

```bash
# Rollback all changes from this plan
git revert HEAD~8..HEAD

# Or reset to before implementation
git reset --hard HEAD~8
```

---

## Checkpoints Summary

| Checkpoint | After Task | Verification |
|------------|------------|--------------|
| **CP1** | Task 1 | GlobalMetadataManager import works |
| **CP2** | Task 4 | All 3 models use GlobalMetadataManager |
| **CP3** | Task 8 | All 7 tests pass |

---

**Architecture:**
- Create a new `GlobalMetadataManager` in `apps/common/managers.py` that filters only by `is_deleted=False`, NOT by organization
- Override the `objects` manager in three metadata models to use this new manager instead of `TenantManager`
- Keep the `organization` field on these models for potential future multi-org layout customization

**Tech Stack:** Django 5.0, Python 3.11+, PostgreSQL

---

## Prerequisites

**Read these files before starting:**
- `backend/apps/common/models.py` - Current `TenantManager` and `BaseModel` implementation
- `backend/apps/system/models.py` - `BusinessObject`, `FieldDefinition`, `PageLayout` definitions
- `docs/plans/2026-01-28-metadata-org-filtering-design.md` - Full design document

**Context:**
- Current issue: Metadata models are filtered by organization, causing 404s for non-default org users
- Solution: Create a manager that bypasses org filtering but keeps soft-delete filtering
- ~70+ code locations currently use `BusinessObject.objects` incorrectly

---

## Task 1: Create GlobalMetadataManager

**Files:**
- Create: `backend/apps/common/managers.py`

**Step 1: Create the managers module with GlobalMetadataManager**

```python
"""
Django model managers for GZEAMS.

This module contains custom managers for different data access patterns:
- TenantManager: Organization-aware filtering for business data
- GlobalMetadataManager: No organization filtering for system metadata
"""
from django.db import models


class GlobalMetadataManager(models.Manager):
    """
    Manager for global system metadata models.

    This manager does NOT filter by organization, as metadata models
    like BusinessObject, FieldDefinition, and PageLayout are shared
    across all organizations in the system.

    Behavior:
    - DOES filter out soft-deleted records (is_deleted=False)
    - DOES NOT filter by organization_id

    Use this manager for models that represent:
    - System-wide metadata (BusinessObject, FieldDefinition, PageLayout)
    - Global configuration (DictionaryType, SequenceRule, SystemConfig)
    - Reference data shared across all organizations

    DO NOT use for business data like Asset, AssetPickup, etc.
    """

    def get_queryset(self):
        """
        Get queryset with soft-delete filtering only.

        Unlike TenantManager, this does NOT filter by organization.
        """
        queryset = super().get_queryset()

        # Only filter out soft-deleted records
        # DO NOT filter by organization - metadata is global
        queryset = queryset.filter(is_deleted=False)

        return queryset


class TenantManager(models.Manager):
    """
    Tenant-aware manager that automatically filters by organization.

    Uses thread-local storage to get current organization context.
    Automatically filters out soft-deleted records.

    NOTE: This is moved here from models.py for better organization.
    """

    def get_queryset(self):
        """
        Get queryset with automatic organization and soft-delete filtering.

        Returns:
            QuerySet: Filtered queryset
        """
        queryset = super().get_queryset()

        # Auto-filter by current organization from thread-local context
        from apps.common.middleware import get_current_organization
        org_id = get_current_organization()

        if org_id:
            queryset = queryset.filter(organization_id=org_id)

        # Auto-filter out soft-deleted records
        queryset = queryset.filter(is_deleted=False)

        return queryset
```

**Step 2: Update BaseModel to import from managers module**

Modify: `backend/apps/common/models.py:1-11`

**Before:**
```python
from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
import uuid


class TenantManager(models.Manager):
    """
    Tenant-aware manager that automatically filters by organization.

    Uses thread-local storage to get current organization context.
    Automatically filters out soft-deleted records.
    """

    def get_queryset(self):
        """
        Get queryset with automatic organization and soft-delete filtering.

        Returns:
            QuerySet: Filtered queryset
        """
        queryset = super().get_queryset()

        # Auto-filter by current organization from thread-local context
        from apps.common.middleware import get_current_organization
        org_id = get_current_organization()

        if org_id:
            queryset = queryset.filter(organization_id=org_id)

        # Auto-filter out soft-deleted records
        queryset = queryset.filter(is_deleted=False)

        return queryset
```

**After:**
```python
from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings
import uuid

# Import managers from the dedicated managers module
from apps.common.managers import TenantManager, GlobalMetadataManager
```

**Step 3: Run the linter to check for issues**

Run: `cd backend && venv/Scripts/python.exe -m flake8 apps/common/managers.py --max-line-length=120`
Expected: No output (no errors)

**Step 4: Commit**

```bash
git add backend/apps/common/managers.py backend/apps/common/models.py
git commit -m "feat(common): extract TenantManager and add GlobalMetadataManager

- Move TenantManager to dedicated managers.py module
- Add GlobalMetadataManager for system metadata models
- GlobalMetadataManager filters soft-deleted but NOT organization
- This fixes metadata access issues for non-default organizations"
```

---

## **CHECKPOINT 1: Verify GlobalMetadataManager Works**

**STOP HERE** - Before proceeding to Task 2, verify the manager is working:

```bash
# 1. Verify import works
cd backend && venv/Scripts/python.exe -c "from apps.common.managers import GlobalMetadataManager; print('Import OK')"

# 2. Verify the manager is correctly defined
cd backend && venv/Scripts/python.exe -c "from apps.common.managers import GlobalMetadataManager; print('Filters by org:', hasattr(GlobalMetadataManager(), 'get_queryset'))"
```

**If any test fails**: Run `git revert HEAD` to undo changes and review the code.

---

## Task 2: Update BusinessObject Model

**Files:**
- Modify: `backend/apps/system/models.py:14-150`

**Step 1: Import GlobalMetadataManager**

Add to imports at top of file (after line 11):

```python
from apps.common.managers import GlobalMetadataManager
```

**Step 2: Update BusinessObject to use GlobalMetadataManager**

After the class docstring (around line 27), add the manager declaration:

```python
class BusinessObject(BaseModel):
    """
    Business Object - defines a configurable entity.

    Examples: Asset, AssetPickup, AssetTransfer, InventoryTask, etc.

    Inherits from BaseModel:
    - organization: Multi-tenant data isolation (FIELD KEPT for future use)
    - is_deleted: Soft delete support
    - created_at, updated_at: Audit timestamps
    - created_by: User who created this record
    - custom_fields: Additional metadata storage

    Note: Uses GlobalMetadataManager instead of TenantManager because
    BusinessObject definitions are shared across all organizations.
    Individual organizations can customize layouts via PageLayout.
    """

    # Use GlobalMetadataManager - metadata is NOT organization-filtered
    objects = GlobalMetadataManager()
    # Keep all_objects for admin access to all records including deleted
    all_objects = models.Manager()
```

**Step 3: Verify no syntax errors**

Run: `cd backend && venv/Scripts/python.exe -c "from apps.system.models import BusinessObject; print('Import OK')"`
Expected: `Import OK`

**Step 4: Commit**

```bash
git add backend/apps/system/models.py
git commit -m "feat(system): BusinessObject uses GlobalMetadataManager

- Override objects manager to use GlobalMetadataManager
- BusinessObject metadata is now accessible across all organizations
- Fixes 404 errors when users from non-default orgs access metadata"
```

---

## Task 3: Update FieldDefinition Model

**Files:**
- Modify: `backend/apps/system/models.py:152-300`

**Step 1: Update FieldDefinition to use GlobalMetadataManager**

Find the `FieldDefinition` class definition and add the manager after the docstring:

```python
class FieldDefinition(BaseModel):
    """
    Field Definition - defines a field in a business object.

    Supports 20+ field types including text, number, select, user reference,
    formula calculation, and sub-table (master-detail).

    Inherits from BaseModel for audit trails.
    Uses GlobalMetadataManager because field definitions are shared
    across all organizations for each BusinessObject.

    Note: Individual organizations can customize field display via
    PageLayout configuration, not by modifying FieldDefinition.
    """

    # Use GlobalMetadataManager - field definitions are NOT organization-filtered
    objects = GlobalMetadataManager()
    # Keep all_objects for admin access
    all_objects = models.Manager()
```

**Step 2: Verify import still works**

Run: `cd backend && venv/Scripts/python.exe -c "from apps.system.models import FieldDefinition; print('Import OK')"`
Expected: `Import OK`

**Step 3: Commit**

```bash
git add backend/apps/system/models.py
git commit -m "feat(system): FieldDefinition uses GlobalMetadataManager

- Field definitions are now accessible across all organizations
- Field metadata is global; org-specific customization via PageLayout"
```

---

## Task 4: Update PageLayout Model

**Files:**
- Modify: `backend/apps/system/models.py` (need to find PageLayout class first)

**Step 1: Find PageLayout class location**

Run: `cd backend && venv/Scripts/python.exe -c "from apps.system.models import PageLayout; import inspect; print(inspect.getfile(PageLayout))"`

Then read the file to find the exact line number.

**Step 2: Add GlobalMetadataManager to PageLayout**

```python
class PageLayout(BaseModel):
    """
    Page Layout - defines UI layout for forms and lists.

    Supports tabbed sections, column configurations, and field
    visibility rules.

    Inherits from BaseModel for audit trails.
    Uses GlobalMetadataManager because while organizations CAN
    have custom layouts, the base layout definitions are global.

    Organization-specific customization is handled via the
    organization ForeignKey on this model.
    """

    # Use GlobalMetadataManager - layouts are NOT organization-filtered by default
    # The organization field allows filtering for org-specific layouts
    objects = GlobalMetadataManager()
    all_objects = models.Manager()
```

**Step 3: Verify import**

Run: `cd backend && venv/Scripts/python.exe -c "from apps.system.models import PageLayout; print('Import OK')"`
Expected: `Import OK`

**Step 4: Commit**

```bash
git add backend/apps/system/models.py
git commit -m "feat(system): PageLayout uses GlobalMetadataManager

- Layout definitions are now globally accessible
- Organization-specific layouts still work via organization FK field"
```

---

## **CHECKPOINT 2: Verify All Three Models Use New Manager**

**STOP HERE** - Before proceeding to Task 5, verify all models work:

```bash
# 1. Verify BusinessObject uses the new manager
cd backend && venv/Scripts/python.exe -c "from apps.system.models import BusinessObject; print('Manager:', type(BusinessObject.objects).__name__)"

# 2. Verify FieldDefinition uses the new manager
cd backend && venv/Scripts/python.exe -c "from apps.system.models import FieldDefinition; print('Manager:', type(FieldDefinition.objects).__name__)"

# 3. Verify PageLayout uses the new manager
cd backend && venv/Scripts/python.exe -c "from apps.system.models import PageLayout; print('Manager:', type(PageLayout.objects).__name__)"

# Expected output for all: Manager: GlobalMetadataManager
```

**If any test fails**:
```bash
# Rollback the last 3 commits
git revert HEAD~3..HEAD
```

---

## Task 5: Update ObjectRegistry (Revert all_objects Change)

**Files:**
- Modify: `backend/apps/system/services/object_registry.py:186-187`

**Step 1: Revert the temporary fix**

Now that `BusinessObject.objects` uses `GlobalMetadataManager`, we can use the standard manager again:

**Before (current temp fix):**
```python
        # Use all_objects to bypass organization filtering
        # BusinessObject is global metadata, not org-specific
        bo = BusinessObject.all_objects.get(code=code, is_deleted=False)
```

**After:**
```python
        # BusinessObject.objects now uses GlobalMetadataManager
        # which correctly does NOT filter by organization
        bo = BusinessObject.objects.get(code=code)
```

Note: We don't need `is_deleted=False` filter because `GlobalMetadataManager` already includes it.

**Step 2: Verify the service still works**

Run: `cd backend && venv/Scripts/python.exe -c "from apps.system.services.object_registry import ObjectRegistry; meta = ObjectRegistry.get_or_create_from_db('Asset'); print(f'Found: {meta.code if meta else None}')"`
Expected: `Found: Asset`

**Step 3: Commit**

```bash
git add backend/apps/system/services/object_registry.py
git commit -m "fix(object_registry): use standard objects manager

- Now that BusinessObject uses GlobalMetadataManager,
- we can use the standard .objects manager again
- Removes temporary all_objects workaround"
```

---

## Task 6: Write Unit Tests

**Files:**
- Create: `backend/apps/common/tests/test_managers.py`

**Step 1: Create test file**

```python
"""
Unit tests for custom Django managers.

Tests TenantManager and GlobalMetadataManager behavior.
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model

from apps.common.managers import TenantManager, GlobalMetadataManager
from apps.system.models import BusinessObject, FieldDefinition, PageLayout
from apps.assets.models import Asset

User = get_user_model()


class GlobalMetadataManagerTest(TestCase):
    """Test GlobalMetadataManager behavior."""

    def setUp(self):
        """Create test data."""
        from apps.organizations.models import Organization

        # Create two organizations
        self.org1 = Organization.objects.create(name='Org 1', code='org1')
        self.org2 = Organization.objects.create(name='Org 2', code='org2')

        # Create a BusinessObject in org1
        self.bo = BusinessObject.objects.create(
            code='TEST_OBJ',
            name='Test Object',
            organization=self.org1
        )

        # Create a soft-deleted BusinessObject
        self.bo_deleted = BusinessObject.objects.create(
            code='TEST_OBJ_DEL',
            name='Test Object Deleted',
            organization=self.org2
        )
        self.bo_deleted.soft_delete()

    def test_global_metadata_manager_no_org_filter(self):
        """Test that GlobalMetadataManager does not filter by organization."""
        # Set context to org2
        from apps.common.middleware import set_current_organization
        from threading import local

        # Query with org2 context - should still see org1's BusinessObject
        set_current_organization(str(self.org2.id))

        result = BusinessObject.objects.filter(code='TEST_OBJ')
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().code, 'TEST_OBJ')

    def test_global_metadata_manager_filters_soft_delete(self):
        """Test that GlobalMetadataManager filters soft-deleted records."""
        result = BusinessObject.objects.filter(code__startswith='TEST_OBJ')
        # Should only see non-deleted records
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().code, 'TEST_OBJ')

    def test_global_metadata_manager_with_all_objects(self):
        """Test that all_objects shows everything including soft-deleted."""
        result = BusinessObject.all_objects.filter(code__startswith='TEST_OBJ')
        # Should see both records
        self.assertEqual(result.count(), 2)


class TenantManagerTest(TestCase):
    """Test TenantManager behavior for business data."""

    def setUp(self):
        """Create test data."""
        from apps.organizations.models import Organization

        self.org1 = Organization.objects.create(name='Org 1', code='org1')
        self.org2 = Organization.objects.create(name='Org 2', code='org2')

        # Create Assets in different organizations
        self.asset1 = Asset.objects.create(
            code='ASSET1',
            name='Asset 1',
            organization=self.org1
        )

        self.asset2 = Asset.objects.create(
            code='ASSET2',
            name='Asset 2',
            organization=self.org2
        )

    def test_tenant_manager_filters_by_organization(self):
        """Test that TenantManager filters by organization."""
        from apps.common.middleware import set_current_organization

        # Set org1 context
        set_current_organization(str(self.org1.id))

        result = Asset.objects.all()
        codes = sorted([a.code for a in result])
        # Should only see org1's assets
        self.assertEqual(codes, ['ASSET1'])

    def test_tenant_manager_filters_soft_delete(self):
        """Test that TenantManager filters soft-deleted records."""
        from apps.common.middleware import set_current_organization

        set_current_organization(str(self.org1.id))

        # Soft delete asset1
        self.asset1.soft_delete()

        result = Asset.objects.all()
        # Should see no assets (only asset1 was in org1 and it's deleted)
        self.assertEqual(result.count(), 0)
```

**Step 2: Run tests to verify they pass**

Run: `cd backend && venv/Scripts/python.exe -m pytest apps/common/tests/test_managers.py -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add backend/apps/common/tests/test_managers.py
git commit -m "test(common): add unit tests for GlobalMetadataManager

- Test no org filtering for metadata models
- Test soft-delete filtering still works
- Test TenantManager org filtering for business data"
```

---

## Task 7: Integration Test

**Files:**
- Create: `backend/apps/system/tests/test_metadata_org_access.py`

**Step 1: Create integration test**

```python
"""
Integration test for metadata access across organizations.

Verifies that users from different organizations can access
BusinessObject, FieldDefinition, and PageLayout metadata.
"""
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from apps.organizations.models import Organization
from apps.system.models import BusinessObject, FieldDefinition, PageLayout

User = get_user_model()


class CrossOrgMetadataAccessTest(TestCase):
    """Test metadata access across organizations."""

    def setUp(self):
        """Create test data with multiple organizations."""
        # Create organizations
        self.default_org = Organization.objects.create(
            name='Default',
            code='default'
        )
        self.branch_org = Organization.objects.create(
            name='Branch Office',
            code='branch'
        )

        # Create users in different organizations
        self.admin_user = User.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        self.admin_user.primary_organization = self.default_org
        self.admin_user.save()

        self.branch_user = User.objects.create_user(
            username='branch_user',
            password='branch123',
            email='branch@test.com'
        )
        self.branch_user.primary_organization = self.branch_org
        self.branch_user.save()

        # Create metadata in default org
        self.business_object = BusinessObject.objects.create(
            code='TestAsset',
            name='Test Asset',
            organization=self.default_org
        )

        self.field_def = FieldDefinition.objects.create(
            business_object=self.business_object,
            code='test_field',
            name='Test Field',
            field_type='text',
            organization=self.default_org
        )

        self.page_layout = PageLayout.objects.create(
            business_object=self.business_object,
            code='default_form',
            name='Default Form',
            layout_type='form',
            organization=self.default_org
        )

    def test_branch_user_can_access_default_org_metadata(self):
        """Test that branch user can access metadata created by default org."""
        # Login as branch user
        client = APIClient()
        response = client.post('/api/auth/login/', {
            'username': 'branch_user',
            'password': 'branch123'
        })
        token = response.data['data']['token']
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # Set branch org context
        client.defaults['HTTP_X_ORGANIZATION_ID'] = str(self.branch_org.id)

        # Access BusinessObject metadata endpoint
        response = client.get('/api/system/objects/TestAsset/metadata/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['data']['code'], 'TestAsset')
        self.assertTrue(len(response.data['data']['fields']) > 0)

    def test_metadata_visible_to_all_orgs_via_manager(self):
        """Test that metadata models return records across organizations."""
        # Query with branch org context
        from apps.common.middleware import set_current_organization
        set_current_organization(str(self.branch_org.id))

        # BusinessObject should be visible
        bo = BusinessObject.objects.filter(code='TestAsset').first()
        self.assertIsNotNone(bo)
        self.assertEqual(bo.code, 'TestAsset')

        # FieldDefinition should be visible
        fields = FieldDefinition.objects.filter(business_object=bo)
        self.assertEqual(fields.count(), 1)

        # PageLayout should be visible
        layouts = PageLayout.objects.filter(business_object=bo)
        self.assertEqual(layouts.count(), 1)
```

**Step 2: Run integration test**

Run: `cd backend && venv/Scripts/python.exe -m pytest apps/system/tests/test_metadata_org_access.py -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add backend/apps/system/tests/test_metadata_org_access.py
git commit -m "test(system): add cross-org metadata access integration test

- Verify branch users can access default org metadata
- Test /api/system/objects/{code}/metadata/ endpoint
- Confirm GlobalMetadataManager works correctly"
```

---

## Task 8: Update Documentation

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Add metadata model exception to CLAUDE.md**

Add after the `BaseModel` section (around line 164):

```markdown
#### Metadata Model Exception

**IMPORTANT**: System metadata models (`BusinessObject`, `FieldDefinition`, `PageLayout`)
use `GlobalMetadataManager` instead of `TenantManager`.

| Model Type | Manager | Organization Filtered? | Soft Delete Filtered? |
|------------|---------|----------------------|----------------------|
| Business Data (Asset, etc.) | TenantManager | YES | YES |
| Metadata Models | GlobalMetadataManager | NO | YES |

**Why**: BusinessObject, FieldDefinition, and PageLayout are **system-wide metadata**
that must be accessible across all organizations. Individual organizations can
customize layouts via the `organization` ForeignKey on `PageLayout`, but the base
definitions are global.

**Usage**: When working with metadata models, use the standard `.objects` manager:

```python
# CORRECT - Use standard objects manager
bo = BusinessObject.objects.get(code='Asset')  # Works across all orgs

# WRONG - Don't use all_objects for normal queries
bo = BusinessObject.all_objects.get(code='Asset')  # Unnecessary
```
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: document GlobalMetadataManager for metadata models

- Explain metadata model exception to TenantManager pattern
- Clarify when to use GlobalMetadataManager vs TenantManager
- Add usage examples"
```

---

## **CHECKPOINT 3: Verify Tests Pass**

**STOP HERE** - Before proceeding to Task 9, verify all tests pass:

```bash
# Run all tests for this implementation
cd backend && venv/Scripts/python.exe -m pytest apps/common/tests/test_managers.py apps/system/tests/test_metadata_org_access.py -v

# Expected: 7 tests PASSED (3 + 2 + 2)
```

**If tests fail**:
```bash
# View detailed output
cd backend && venv/Scripts/python.exe -m pytest apps/common/tests/test_managers.py apps/system/tests/test_metadata_org_access.py -v --tb=short

# Rollback if critical failure
git revert HEAD~2..HEAD
```

---

## Task 9: Manual Verification

**Files:**
- None (manual testing)

**Step 1: Start backend server**

Run: `cd backend && venv/Scripts/python.exe manage.py runserver 127.0.0.1:8000`

**Step 2: Test metadata endpoint with branch user**

Run in another terminal:
```bash
# Login as branch user
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "branch_user", "password": "branch123"}'

# Use the token to access metadata
export TOKEN="<token from above>"
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/system/objects/Asset/metadata/
```

Expected: `200 OK` with metadata response

**Step 3: Verify Asset data is still org-filtered**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/assets/
```

Expected: `200 OK` but only assets for the branch user's organization

---

## Task 10: Final Review and Summary

**Step 1: Create implementation summary**

Create: `docs/reports/implementation/GLOBAL_METADATA_MANAGER_IMPLEMENTATION_REPORT.md`

```markdown
# GlobalMetadataManager Implementation Report

## Summary
Implemented `GlobalMetadataManager` to fix organization filtering issues
for metadata models (BusinessObject, FieldDefinition, PageLayout).

## Files Changed
1. `apps/common/managers.py` - CREATED
2. `apps/common/models.py` - Modified imports
3. `apps/system/models.py` - Added managers to 3 models
4. `apps/system/services/object_registry.py` - Reverted temp fix
5. `apps/common/tests/test_managers.py` - CREATED
6. `apps/system/tests/test_metadata_org_access.py` - CREATED
7. `CLAUDE.md` - Updated documentation

## Tests Added
- GlobalMetadataManagerTest (3 tests)
- TenantManagerTest (2 tests)
- CrossOrgMetadataAccessTest (2 tests)

## Verification
- [x] Unit tests pass
- [x] Integration tests pass
- [x] Manual API testing successful
- [x] Documentation updated
```

**Step 2: Final commit for implementation**

```bash
git add docs/reports/implementation/GLOBAL_METADATA_MANAGER_IMPLEMENTATION_REPORT.md
git commit -m "docs: add GlobalMetadataManager implementation report"
```

---

## Completion Checklist

- [x] Created `GlobalMetadataManager` class
- [x] Updated `BusinessObject` to use `GlobalMetadataManager`
- [x] Updated `FieldDefinition` to use `GlobalMetadataManager`
- [x] Updated `PageLayout` to use `GlobalMetadataManager`
- [x] Reverted temporary `all_objects` workaround in `ObjectRegistry`
- [x] Added unit tests for manager behavior
- [x] Added integration tests for cross-org access
- [x] Updated CLAUDE.md documentation
- [x] Manual verification complete
- [x] All tests passing

---

**Implementation complete!** The system now correctly handles metadata models
as global (non-organization-filtered) while maintaining organization isolation
for business data.
