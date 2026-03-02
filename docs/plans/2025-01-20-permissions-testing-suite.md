# Permissions Module Testing Suite Implementation Plan

## Document Information
| Project | Description |
|---------|-------------|
| Plan Version | v1.0 |
| Created Date | 2025-01-20 |
| Target Module | Permissions (apps/permissions/) |
| Test Framework | pytest + pytest-django |

## Overview
Add comprehensive test coverage for the Permissions module, which is currently the only backend module without tests. The permissions module implements:
- **Field Permission Service**: Granular field-level read/write/hidden permissions
- **Data Permission Service**: Organization and data scope-based access control
- **Permission Engine**: Core permission evaluation logic

## Module Structure Analysis

### Models
```
apps/permissions/models.py
├── Permission (Base permissions with org scope)
├── FieldPermission (Field-level permission rules)
└── DataPermission (Data scope permission rules)
```

### Services
```
apps/permissions/services/
├── permission_engine.py       # Core permission evaluation
├── field_permission_service.py # Field-level permissions
└── data_permission_service.py  # Data scope permissions
```

### Current Test Status
- **Test Files**: 0
- **Coverage**: Unknown
- **Priority**: HIGH (security-critical module)

## Implementation Tasks

### Task 1: Test Infrastructure Setup
**File**: `backend/apps/permissions/tests/__init__.py`

**Steps**:
1. Create tests directory
2. Create `__init__.py` to mark as test package
3. Create `conftest.py` with fixtures for:
   - `organization` - Test organization with permissions enabled
   - `user` - User with organization membership
   - `admin_user` - User with admin role
   - `member_user` - User with member role
   - `business_object` - Test business object for field permissions
   - `permission` - Base permission instance
   - `field_permission` - Field permission rule
   - `data_permission` - Data scope permission rule
   - `api_client` - DRF API client

**Verification**:
```bash
docker-compose exec backend pytest apps/permissions/tests/conftest.py --collect-only
```

### Task 2: Model Tests
**File**: `backend/apps/permissions/tests/test_models.py`

**Test Cases** (16 tests):
1. `test_permission_creation` - Verify Permission model creation
2. `test_permission_str_representation` - Verify __str__ method
3. `test_permission_soft_delete` - Verify soft delete functionality
4. `test_field_permission_creation` - Verify FieldPermission creation
5. `test_field_permission_unique_constraint` - Verify unique constraint on (permission, field)
6. `test_field_permission_default_values` - Verify default permission_level (read)
7. `test_data_permission_creation` - Verify DataPermission creation
8. `test_data_permission_scope_types` - Verify all scope_type values (all, org, dept, self)
9. `test_data_permission_filter_conditions` - Verify JSONB filter_conditions storage
10. `test_permission_organization_filtering` - Verify org-based filtering
11. `test_permission_cascade_delete` - Verify related record handling
12. `test_field_permission_validation` - Verify permission_level choices
13. `test_data_permission_validation` - Verify scope_type choices
14. `test_permission_audit_fields` - Verify created_by, updated_at tracking
15. `test_permission_custom_fields` - Verify custom_fields JSONB
16. `test_permission_active_manager` - Verify is_deleted=False default query

**Verification**:
```bash
docker-compose exec backend pytest apps/permissions/tests/test_models.py -v
```

### Task 3: Field Permission Service Tests
**File**: `backend/apps/permissions/tests/test_field_permission_service.py`

**Test Cases** (14 tests):
1. `test_get_field_permission` - Verify getting field permission for user
2. `test_get_field_permission_default` - Verify default permission when no rule exists
3. `test_set_field_permission` - Verify setting field permission rule
4. `test_set_field_permission_update` - Verify updating existing rule
5. `test_delete_field_permission` - Verify deleting field permission
6. `test_get_fields_by_permission` - Verify filtering fields by permission level
7. `test_check_field_access_read` - Verify read access check
8. `test_check_field_access_write` - Verify write access check
9. `test_check_field_access_hidden` - Verify hidden field check
10. `test_batch_set_field_permissions` - Verify batch permission setting
11. `test_get_form_fields_config` - Verify form field configuration generation
12. `test_get_list_fields_config` - Verify list field configuration generation
13. `test_inherit_from_role` - Verify permission inheritance from role
14. `test_field_permission_cache` - Verify permission caching behavior

**Verification**:
```bash
docker-compose exec backend pytest apps/permissions/tests/test_field_permission_service.py -v
```

### Task 4: Data Permission Service Tests
**File**: `backend/apps/permissions/tests/test_data_permission_service.py`

**Test Cases** (14 tests):
1. `test_get_data_permission` - Verify getting data permission for user
2. `test_set_data_permission` - Verify setting data permission rule
3. `test_set_data_permission_update` - Verify updating existing rule
4. `test_delete_data_permission` - Verify deleting data permission
5. `test_get_user_data_scope` - Verify getting user's data scope
6. `test_build_data_filter_all` - Verify filter for 'all' scope
7. `test_build_data_filter_org` - Verify filter for 'org' scope
8. `test_build_data_filter_dept` - Verify filter for 'dept' scope
9. `test_build_data_filter_self` - Verify filter for 'self' scope
10. `test_apply_data_permissions_queryset` - Verify applying permissions to queryset
11. `test_check_data_access` - Verify data access check
12. `test_get_accessible_departments` - Verify getting accessible departments
13. `test_data_permission_custom_conditions` - Verify custom filter conditions
14. `test_data_permission_hierarchy` - Verify permission hierarchy resolution

**Verification**:
```bash
docker-compose exec backend pytest apps/permissions/tests/test_data_permission_service.py -v
```

### Task 5: Permission Engine Tests
**File**: `backend/apps/permissions/tests/test_permission_engine.py`

**Test Cases** (12 tests):
1. `test_engine_initialization` - Verify PermissionEngine initialization
2. `test_evaluate_field_permission` - Verify field permission evaluation
3. `test_evaluate_data_permission` - Verify data permission evaluation
4. `test_combined_permission_check` - Verify combined field + data check
5. `test_admin_bypass` - Verify admin users bypass permission checks
6. `test_superuser_bypass` - Verify superuser bypass
7. `test_permission_cache_invalidation` - Verify cache invalidation on change
8. `test_get_user_permissions_summary` - Verify permission summary retrieval
9. `test_check_model_permission` - Verify model-level permission check
10. `test_batch_permission_check` - Verify batch permission evaluation
11. `test_permission_fallback` - Verify fallback to default permissions
12. `test_permission_denied_response` - Verify denied response format

**Verification**:
```bash
docker-compose exec backend pytest apps/permissions/tests/test_permission_engine.py -v
```

### Task 6: API Integration Tests
**File**: `backend/apps/permissions/tests/test_api.py`

**Test Cases** (20 tests):
1. `test_field_permissions_list` - GET /api/permissions/field-permissions/
2. `test_field_permissions_create` - POST /api/permissions/field-permissions/
3. `test_field_permissions_update` - PATCH /api/permissions/field-permissions/{id}/
4. `test_field_permissions_delete` - DELETE /api/permissions/field-permissions/{id}/
5. `test_data_permissions_list` - GET /api/permissions/data-permissions/
6. `test_data_permissions_create` - POST /api/permissions/data-permissions/
7. `test_data_permissions_update` - PATCH /api/permissions/data-permissions/{id}/
8. `test_data_permissions_delete` - DELETE /api/permissions/data-permissions/{id}/
9. `test_permission_summary` - GET /api/permissions/summary/
10. `test_check_permissions_action` - POST /api/permissions/check/
11. `test_organization_isolation` - Verify org data isolation
12. `test_batch_field_permissions` - POST /api/permissions/batch-field-permissions/
13. `test_batch_data_permissions` - POST /api/permissions/batch-data-permissions/
14. `test_permission_validation` - Verify input validation
15. `test_unauthorized_access` - Verify 401 for unauthenticated
16. `test_cross_org_forbidden` - Verify 403 for cross-org access
17. `test_deleted_excluded` - Verify soft-deleted records excluded
18. `test_pagination` - Verify list pagination
19. `test_filtering` - Verify filtering capabilities
20. `test_admin_full_access` - Verify admin full access

**Verification**:
```bash
docker-compose exec backend pytest apps/permissions/tests/test_api.py -v
```

### Task 7: Full Test Suite Execution
**Steps**:
1. Run complete test suite for permissions module
2. Generate coverage report
3. Verify all tests pass
4. Document results

**Commands**:
```bash
# Run all tests
docker-compose exec backend pytest apps/permissions/tests/ -v

# Generate coverage report
docker-compose exec backend coverage run --source='apps/permissions' -m pytest
docker-compose exec backend coverage report --omit='*/tests/*'
```

**Success Criteria**:
- All tests pass (target: 60+ tests)
- Coverage >= 80%
- No test skips orxfail

## Implementation Approach

### Option 1: Subagent-Driven Development (Recommended)
- Fresh subagent per task
- Two-stage review (spec compliance + code quality)
- Better code quality through review

### Option 2: Direct Implementation
- Faster execution
- Single agent completes all tasks
- Less review overhead

### Option 3: Parallel Session
- Multiple agents work simultaneously
- Fastest completion time
- Higher token usage

## Summary

| Metric | Target |
|--------|--------|
| Total Test Files | 6 |
| Total Test Cases | 90+ |
| Coverage Target | 80%+ |
| Estimated Time | 2-3 hours |

## Dependencies
- pytest-django must be installed
- DRF API client configuration
- Test organization and user fixtures

## Notes
- Permissions module is security-critical - thorough testing essential
- Test both positive and negative scenarios
- Include edge cases for permission hierarchy
- Verify caching behavior for performance
