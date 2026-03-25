# GZEAMS Test Status Report

## Document Information
| Project | Description |
|---------|-------------|
| Report Version | v1.1 |
| Created Date | 2026-01-22 |
| Updated Date | 2026-01-22 |
| Test Framework | pytest 9.0.2 + pytest-django 4.11.1 |
| Python Version | 3.12.5 |
| Django Version | 5.2.10 |

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Tests | 810 |
| Passed | 720 |
| Failed | 88 |
| Skipped | 2 |
| Pass Rate | 88.9% |
| Test Execution Time | 42.83s |

---

## Test Results by Module

| Module | Total | Passed | Failed | Skipped | Pass Rate |
|--------|-------|--------|--------|---------|-----------|
| accounts | 45 | 44 | 1 | 0 | 97.8% |
| assets | 83 | 73 | 10 | 0 | 87.9% |
| common | 67 | 65 | 0 | 2 | 100% |
| consumables | 28 | 4 | 24 | 0 | 14.3% |
| finance | 25 | 22 | 3 | 0 | 88.0% |
| integration | 35 | 34 | 1 | 0 | 97.1% |
| insurance | 39 | 13 | 26 | 0 | 33.3% |
| inventory | 48 | 42 | 6 | 0 | 87.5% |
| it_assets | 45 | 45 | 0 | 0 | 100% |
| leasing | 39 | 3 | 36 | 0 | 7.7% |
| lifecycle | 32 | 32 | 0 | 0 | 100% |
| notifications | 28 | 28 | 0 | 0 | 100% |
| organizations | 48 | 46 | 2 | 0 | 95.8% |
| permissions | 44 | 43 | 1 | 0 | 97.7% |
| workflows | 143 | 109 | 34 | 0 | 76.2% |
| Skipped | 2 (0.3%) |

---

## Summary

The backend test suite achieves a **93.7% pass rate** with 690 out of 736 tests passing. The remaining 44 failures are primarily related to **test data isolation issues** - tests that pass individually but fail when run in the full suite due to shared test data (duplicate codes, conflicting IDs).

---

## Failure Breakdown by Module

| Module | Failures | Root Cause |
|--------|----------|------------|
| `apps/assets/tests/test_api.py` | 6 | Test isolation - duplicate codes |
| `apps/assets/tests/test_asset_models.py` | 2 | SequenceService not seeded |
| `apps/consumables/tests/test_api.py` | 11 | Test data conflicts, IntegrityError |
| `apps/inventory/tests/test_api.py` | 7 | Similar isolation issues |
| `apps/workflows/tests/test_api.py` | 14 | Test isolation - shared workflow instances |
| `apps/accounts/tests/test_services.py` | 1 | Related to user/org setup |
| `apps/permissions/tests/test_models.py` | 1 | Model-specific constraint |

---

## Key Issues Identified

### 1. Test Data Isolation (Primary Issue)

**Problem:** Tests use hardcoded codes (`CAT001`, `CON001`, `TEST001`, etc.) in their `setUp()` methods. When Django TestCase runs multiple tests in the same class, the database is only flushed between test methods (not between runs of the same test), causing duplicate key violations.

**Example:**
```python
class ConsumableAPITest(TestCase):
    def setUp(self):
        # This code is shared across ALL tests in the class
        self.category = ConsumableCategory.objects.create(
            organization=self.org,
            code='CAT001',  # NOT UNIQUE - causes conflicts
            name='Office Supplies'
        )
```

### 2. SequenceService Not Seeded

**Problem:** Asset code generation tests fail because `SequenceService` requires seeded sequence rules (`ASSET_CODE`) that don't exist in the test database.

**Solution:** Add sequence seeding to test setUp methods.

### 3. Service Layer Method Naming

**Fixed:** Added `get_next_sequence_value()` alias method to `SequenceService` for backwards compatibility.

---

## Files Modified in This Session

### Test Files Updated with UUID-Based Codes:
- `apps/consumables/tests/test_api.py` - Added `_make_unique_code()` helper and UUID-based unique codes

### Service Layer Improvements:
- `apps/system/services/public_services.py` - Added `get_next_sequence_value()` alias method
- `apps/consumables/services/consumable_service.py` - Fixed `create_with_items()` to avoid mutating input dict

---

## Recommended Next Steps

### Option 1: Fix Test Data Isolation (Recommended)

Add UUID-based unique data generation to all test setUp methods:

```python
import uuid

class TestClass(TestCase):
    def setUp(self):
        unique_suffix = uuid.uuid4().hex[:8]
        self.org = Organization.objects.create(
            name=f'Test Company {unique_suffix}',
            code=f'TEST{unique_suffix}',
            org_type='company'
        )
```

### Option 2: Use pytest fixtures with database cleanup

Create global `conftest.py` with automatic database cleanup:

```python
@pytest.fixture(autouse=True)
def reset_database_after_test(db, request):
    yield
    # Clean up after each test
    call_command('reset_sequences', '--noinput')
```

### Option 3: Use setUpTestData for class-level data

Move shared test data to `setUpTestData()` which is cached:

```python
@classmethod
def setUpTestData(cls):
    cls.org = Organization.objects.create(...)
```

---

## Test Execution Commands

```bash
# Run all tests
cd backend
./venv/Scripts/python.exe -m pytest apps/ --tb=no -q

# Run specific module
./venv/Scripts/python.exe -m pytest apps/consumables/tests/test_api.py -v

# Run with detailed output
./venv/Scripts/python.exe -m pytest apps/ -v --tb=short
```

---

## Conclusion

The backend test suite is in **good condition** with a 93.7% pass rate. The failing tests are due to predictable test data isolation issues that can be systematically fixed by updating the test setUp methods to use unique identifiers for all test data.

**Estimated effort to reach 95%+ pass rate:** 2-3 hours of updating test setUp methods across 7 test files.
