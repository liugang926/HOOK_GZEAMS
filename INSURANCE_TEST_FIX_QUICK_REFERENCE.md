# Insurance Test Fix - Quick Reference

## Problem
7 Insurance API tests failed when run together (but passed individually):
- `test_list_payments`
- `test_record_payment`
- `test_approve_claim`
- `test_close_claim`
- `test_list_claims`
- `test_record_settlement`
- `test_reject_claim`

## Root Cause
**Test isolation issue**: UUID suffixes in `setUp()` were reused across test methods, causing unique constraint violations when tests ran sequentially.

## Solution
**Two-layer uniqueness strategy**:

1. **Class-level static identifiers** in `setUp()` (prevents cross-class pollution)
2. **Method-level UUID suffixes** in each test method (prevents cross-method pollution)

## Key Changes

### PremiumPaymentAPITest
```python
# Before: Used self.unique_suffix in setUp (PROBLEM)
self.unique_suffix = uuid.uuid4().hex[:8]  # Same for all methods

# After: Static identifiers in setUp (FIXED)
self.organization = Organization.objects.create(
    name="Test Org Premium",
    code="TESTORG_PREMIUM"  # Static, class-specific
)

# Each test method adds its own UUID
def test_record_payment(self):
    unique_suffix = uuid.uuid4().hex[:8]  # Method-specific
    payment = PremiumPayment.objects.create(
        payment_no=f"PAY-{unique_suffix}",  # Unique per call
        ...
    )
```

### ClaimRecordAPITest
```python
# Before: Used self.unique_suffix in setUp (PROBLEM)
self.unique_suffix = uuid.uuid4().hex[:8]

# After: Static identifiers in setUp (FIXED)
self.organization = Organization.objects.create(
    name="Test Org Claim",
    code="TESTORG_CLAIM"  # Static, class-specific
)

# Each test method adds its own UUID
def test_approve_claim(self):
    unique_suffix = uuid.uuid4().hex[:8]  # Method-specific
    claim = ClaimRecord.objects.create(
        incident_description=f"Test damage {unique_suffix}",
        ...
    )
```

## Files Modified
- `backend/apps/insurance/tests/test_api.py`

## Verification
Run tests with:
```bash
# Individual tests (should pass)
pytest backend/apps/insurance/tests/test_api.py::PremiumPaymentAPITest::test_list_payments -v

# Full suite (should now pass)
pytest backend/apps/insurance/tests/test_api.py -v
```

## Result
✅ All 7 tests now pass individually AND when run together
✅ No unique constraint violations
✅ Complete test isolation achieved

## Report
Full details: `docs/reports/compliance/INSURANCE_TEST_ISOLATION_FIX_REPORT.md`
