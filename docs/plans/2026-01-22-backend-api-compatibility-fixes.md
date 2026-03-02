# Backend API Compatibility Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix missing and mismatched API endpoints identified in the frontend-backend compatibility analysis to enable full frontend functionality.

**Architecture:** Follow existing GZEAMS patterns - all ViewSets inherit from BaseModelViewSetWithBatch, all models inherit from BaseModel, use BaseResponse for standardized responses.

**Tech Stack:** Django 5.0, Django REST Framework, PostgreSQL, pytest

---

## Problem Statement

The compatibility analysis identified 79 issues across 4 modules:
- **Assets (87%)**: 3 missing APIs (QR code, batch status change)
- **Leasing (95%)**: 0 missing APIs - frontend API layer incomplete
- **Insurance (78%)**: 2 missing APIs, 1 mismatched endpoint, 1 missing business logic
- **Inventory (35%)**: 68 missing APIs - separate plan required

This plan focuses on **high-priority fixes** for Assets and Insurance modules that enable frontend functionality.

---

## Phase 1: Insurance Module Fixes (HIGH Priority)

### Task 1: Add `expiring-soon` endpoint to InsurancePolicyViewSet

**Files:**
- Modify: `backend/apps/insurance/viewsets.py:38-95` (InsurancePolicyViewSet)
- Test: `backend/apps/insurance/tests/test_api.py:222-243`

**Step 1: Write failing test for expiring_soon endpoint**

Add to `backend/apps/insurance/tests/test_api.py` after line 243:

```python
def test_filter_expiring_soon_with_days(self):
    """Test filtering policies expiring soon with custom days parameter."""
    unique_suffix = uuid.uuid4().hex[:8]

    # Create policy expiring in 15 days
    InsurancePolicy.objects.create(
        organization=self.organization,
        policy_no=f"POL-{unique_suffix}",
        company=self.company,
        insurance_type="property",
        start_date=date.today() - timedelta(days=350),
        end_date=date.today() + timedelta(days=15),
        total_insured_amount=100000,
        total_premium=5000,
        status='active',
        created_by=self.user
    )

    # Create policy expiring in 60 days
    InsurancePolicy.objects.create(
        organization=self.organization,
        policy_no=f"POL-{unique_suffix}-2",
        company=self.company,
        insurance_type="property",
        start_date=date.today() - timedelta(days=305),
        end_date=date.today() + timedelta(days=60),
        total_insured_amount=100000,
        total_premium=5000,
        status='active',
        created_by=self.user
    )

    url = '/api/insurance/policies/?expires_soon=true&days=30'
    response = self.client.get(url)

    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.assertTrue(response.data['success'])
    self.assertEqual(len(response.data['data']['results']), 1)
```

**Step 2: Run test to verify it fails**

```bash
cd C:\Users\ND\Desktop\Notting_Project\NEWSEAMS\backend
./venv/Scripts/python.exe -m pytest apps/insurance/tests/test_api.py::InsurancePolicyAPITest::test_filter_expiring_soon_with_days -v
```

Expected: FAIL - endpoint returns 0 results (days parameter not implemented)

**Step 3: Implement days parameter in expiring_soon filter**

Modify `backend/apps/insurance/filters.py` - find the `expires_soon` filter and add days parameter:

```python
# In InsurancePolicyFilter class, modify the expires_soon field:
expires_soon = django_filters.BooleanFilter(method='filter_expires_soon')
days = django_filters.NumberFilter(method='filter_expires_soon')

def filter_expires_soon(self, queryset, name, value):
    from datetime import timedelta
    if value in [True, 'true', 'True', '1']:
        days = int(self.data.get('days', 30))  # Default 30 days
        delta = date.today() + timedelta(days=days)
        return queryset.filter(end_date__lte=delta, status='active')
    return queryset
```

**Step 4: Run test to verify it passes**

```bash
./venv/Scripts/python.exe -m pytest apps/insurance/tests/test_api.py::InsurancePolicyAPITest::test_filter_expiring_soon_with_days -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/apps/insurance/filters.py backend/apps/insurance/tests/test_api.py
git commit -m "feat(insurance): add days parameter to expiring_soon filter"
```

---

### Task 2: Add `dashboard-stats` endpoint to InsurancePolicyViewSet

**Files:**
- Modify: `backend/apps/insurance/viewsets.py:38-95`
- Test: `backend/apps/insurance/tests/test_api.py`

**Step 1: Write failing test for dashboard_stats endpoint**

Add to `backend/apps/insurance/tests/test_api.py`:

```python
def test_get_dashboard_stats(self):
    """Test getting insurance dashboard statistics."""
    unique_suffix = uuid.uuid4().hex[:8]

    # Create active policies
    for i in range(3):
        InsurancePolicy.objects.create(
            organization=self.organization,
            policy_no=f"POL-{unique_suffix}-{i}",
            company=self.company,
            insurance_type="property",
            start_date=date.today(),
            end_date=date.today() + timedelta(days=365),
            total_insured_amount=100000 + i * 50000,
            total_premium=5000 + i * 1000,
            status='active',
            created_by=self.user
        )

    url = '/api/insurance/policies/dashboard-stats/'
    response = self.client.get(url)

    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.assertIn('total_policies', response.data)
    self.assertIn('total_insured_amount', response.data)
    self.assertIn('total_premium', response.data)
    self.assertEqual(response.data['total_policies'], 3)
```

**Step 2: Run test to verify it fails**

```bash
./venv/Scripts/python.exe -m pytest apps/insurance/tests/test_api.py::InsurancePolicyAPITest::test_get_dashboard_stats -v
```

Expected: FAIL - 404 Not Found

**Step 3: Implement dashboard_stats action**

Add to `backend/apps/insurance/viewsets.py` in `InsurancePolicyViewSet` class (after `summary` action):

```python
@action(detail=False, methods=['get'])
def dashboard_stats(self, request):
    """Get insurance dashboard statistics."""
    from django.db.models import Sum, Q

    policies = self.filter_queryset(self.get_queryset())

    stats = {
        'total_policies': policies.count(),
        'active_policies': policies.filter(status='active').count(),
        'draft_policies': policies.filter(status='draft').count(),
        'expired_policies': policies.filter(status='expired').count(),
        'total_insured_amount': policies.aggregate(
            total=Sum('total_insured_amount')
        )['total'] or 0,
        'total_annual_premium': policies.aggregate(
            total=Sum('total_premium')
        )['total'] or 0,
        'unpaid_premium': policies.filter(
            status='active'
        ).aggregate(
            total=Sum('total_premium')
        )['total'] or 0,
    }

    return Response(stats)
```

**Step 4: Run test to verify it passes**

```bash
./venv/Scripts/python.exe -m pytest apps/insurance/tests/test_api.py::InsurancePolicyAPITest::test_get_dashboard_stats -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/apps/insurance/viewsets.py backend/apps/insurance/tests/test_api.py
git commit -m "feat(insurance): add dashboard-stats endpoint for dashboard overview"
```

---

### Task 3: Add `record-payment` alias action for claim settlement

**Files:**
- Modify: `backend/apps/insurance/viewsets.py:260-273`
- Test: `backend/apps/insurance/tests/test_api.py:487-508`

**Step 1: Write failing test for record-payment endpoint**

```python
def test_record_claim_payment_via_alias(self):
    """Test recording claim payment using record-payment alias (PRD naming)."""
    unique_suffix = uuid.uuid4().hex[:8]
    claim = ClaimRecord.objects.create(
        organization=self.organization,
        policy=self.policy,
        incident_date=date.today(),
        incident_type='damage',
        incident_description=f'Test damage {unique_suffix}',
        claimed_amount=10000,
        approved_amount=8000,
        status='approved',
        created_by=self.user
    )

    url = f'/api/insurance/claims/{claim.id}/record-payment/'
    data = {'amount': 8000, 'payment_date': str(date.today())}
    response = self.client.post(url, data, format='json')

    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.assertEqual(response.data['status'], 'paid')
```

**Step 2: Run test to verify it fails**

```bash
./venv/Scripts/python.exe -m pytest apps/insurance/tests/test_api.py::ClaimRecordAPITest::test_record_claim_payment_via_alias -v
```

Expected: FAIL - 404 Not Found

**Step 3: Add record-payment alias action**

Add to `backend/apps/insurance/viewsets.py` in `ClaimRecordViewSet` class (after `record_settlement`):

```python
@action(detail=True, methods=['post'], url_path='record-payment')
def record_payment_alias(self, request, pk=None):
    """Alias for record_settlement to match PRD naming convention."""
    return self.record_settlement(request, pk=pk)
```

**Step 4: Run test to verify it passes**

```bash
./venv/Scripts/python.exe -m pytest apps/insurance/tests/test_api.py::ClaimRecordAPITest::test_record_claim_payment_via_alias -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/apps/insurance/viewsets.py backend/apps/insurance/tests/test_api.py
git commit -m "feat(insurance): add record-payment alias for claim settlement"
```

---

### Task 4: Implement payment schedule generation on policy activation

**Files:**
- Modify: `backend/apps/insurance/viewsets.py:51-63`

**Step 1: Write failing test for payment schedule generation**

```python
def test_activate_policy_generates_payment_schedule(self):
    """Test that activating a policy generates payment schedule."""
    unique_suffix = uuid.uuid4().hex[:8]

    policy = InsurancePolicy.objects.create(
        organization=self.organization,
        policy_no=f"POL-{unique_suffix}",
        company=self.company,
        insurance_type="property",
        start_date=date.today(),
        end_date=date.today() + timedelta(days=365),
        total_insured_amount=1000000,
        total_premium=12000,
        payment_frequency='quarterly',
        status='draft',
        created_by=self.user
    )

    # Verify no payments exist
    self.assertEqual(policy.payments.count(), 0)

    url = f'/api/insurance/policies/{policy.id}/activate/'
    response = self.client.post(url)

    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.assertEqual(response.data['status'], 'active')

    # Verify payment schedule was generated
    self.assertEqual(policy.payments.count(), 4)  # Quarterly = 4 payments
    self.assertTrue(all(p.status == 'pending' for p in policy.payments.all()))
```

**Step 2: Run test to verify it fails**

```bash
./venv/Scripts/python.exe -m pytest apps/insurance/tests/test_api.py::InsurancePolicyAPITest::test_activate_policy_generates_payment_schedule -v
```

Expected: FAIL - 0 payments created

**Step 3: Implement payment schedule generation in activate action**

Replace the `activate` action in `backend/apps/insurance/viewsets.py`:

```python
@action(detail=True, methods=['post'])
def activate(self, request, pk=None):
    """Activate a draft policy and generate payment schedule."""
    policy = self.get_object()
    if policy.status != 'draft':
        return Response(
            {'error': 'Only draft policies can be activated.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    policy.status = 'active'
    policy.save(update_fields=['status'])

    # Generate payment schedule
    self._generate_payment_schedule(policy)

    serializer = self.get_serializer(policy)
    return Response(serializer.data)

def _generate_payment_schedule(self, policy):
    """Generate premium payment schedule based on payment frequency."""
    from apps.insurance.models import PremiumPayment
    from datetime import timedelta

    if policy.payment_frequency == 'annual':
        PremiumPayment.objects.create(
            organization_id=policy.organization_id,
            policy=policy,
            payment_no=f"PAY-{policy.policy_no}-01",
            due_date=policy.start_date,
            amount=policy.total_premium,
            created_by=policy.created_by
        )
        return

    intervals = {
        'semi_annual': timedelta(days=180),
        'quarterly': timedelta(days=90),
        'monthly': timedelta(days=30),
    }

    interval = intervals.get(policy.payment_frequency, timedelta(days=30))
    total_days = (policy.end_date - policy.start_date).days
    payment_count = max(1, int(total_days / interval.days))
    payment_amount = round(policy.total_premium / payment_count, 2)

    current_date = policy.start_date
    for i in range(payment_count):
        PremiumPayment.objects.create(
            organization_id=policy.organization_id,
            policy=policy,
            payment_no=f"PAY-{policy.policy_no}-{i+1:02d}",
            due_date=current_date,
            amount=payment_amount,
            created_by=policy.created_by
        )
        current_date += interval
```

**Step 4: Run test to verify it passes**

```bash
./venv/Scripts/python.exe -m pytest apps/insurance/tests/test_api.py::InsurancePolicyAPITest::test_activate_policy_generates_payment_schedule -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/apps/insurance/viewsets.py backend/apps/insurance/tests/test_api.py
git commit -m "feat(insurance): auto-generate payment schedule on policy activation"
```

---

## Phase 2: Assets Module Fixes (MEDIUM Priority)

### Task 5: Add QR code image generation endpoint

**Files:**
- Modify: `backend/apps/assets/viewsets.py`
- Test: `backend/apps/assets/tests/test_api.py`

**Step 1: Install qrcode dependency**

```bash
cd C:\Users\ND\Desktop\Notting_Project\NEWSEAMS\backend
./venv/Scripts/pip.exe install qrcode[pil]
```

**Step 2: Add qrcode to requirements.txt**

```bash
echo "qrcode[pil]>=7.4.0" >> requirements.txt
```

**Step 3: Write failing test for QR code endpoint**

Add to `backend/apps/assets/tests/test_api.py`:

```python
def test_get_asset_qr_code(self):
    """Test getting asset QR code image."""
    asset = Asset.objects.create(
        organization=self.organization,
        asset_category=self.category,
        asset_code=f"AST-{uuid.uuid4().hex[:8]}",
        asset_name="Test Asset",
        purchase_price=Decimal('10000.00'),
        created_by=self.user
    )

    url = f'/api/assets/assets/{asset.id}/qr_code/'
    response = self.client.get(url)

    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.assertEqual(response['Content-Type'], 'image/png')
```

**Step 4: Run test to verify it fails**

```bash
./venv/Scripts/python.exe -m pytest apps/assets/tests/test_api.py::AssetAPITest::test_get_asset_qr_code -v
```

Expected: FAIL - 404 Not Found

**Step 5: Implement QR code generation action**

Add to `backend/apps/assets/viewsets.py` in `AssetViewSet` class:

```python
import qrcode
from io import BytesIO
from django.http import HttpResponse

@action(detail=True, methods=['get'])
def qr_code(self, request, pk=None):
    """Generate QR code image for the asset."""
    asset = self.get_object()

    # Generate QR code containing asset URL for scanning
    qr_data = f"{settings.FRONTEND_URL}/assets/{asset.id}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return HttpResponse(
        buffer.getvalue(),
        content_type='image/png',
        headers={
            'Content-Disposition': f'inline; filename="qr_{asset.asset_code}.png"'
        }
    )
```

**Step 6: Add FRONTEND_URL to settings**

Add to `backend/config/settings.py`:

```python
# Frontend URL for QR code generation
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
```

**Step 7: Run test to verify it passes**

```bash
./venv/Scripts/python.exe -m pytest apps/assets/tests/test_api.py::AssetAPITest::test_get_asset_qr_code -v
```

Expected: PASS

**Step 8: Commit**

```bash
git add backend/apps/assets/viewsets.py backend/apps/assets/tests/test_api.py backend/config/settings.py requirements.txt
git commit -m "feat(assets): add QR code image generation endpoint"
```

---

### Task 6: Add batch change status endpoint

**Files:**
- Modify: `backend/apps/assets/viewsets.py`
- Test: `backend/apps/assets/tests/test_api.py`

**Step 1: Write failing test for batch_change_status endpoint**

```python
def test_batch_change_status(self):
    """Test batch changing asset status."""
    unique_suffix = uuid.uuid4().hex[:8]

    assets = []
    for i in range(3):
        asset = Asset.objects.create(
            organization=self.organization,
            asset_category=self.category,
            asset_code=f"AST-{unique_suffix}-{i}",
            asset_name=f"Test Asset {i}",
            purchase_price=Decimal('10000.00'),
            asset_status='in_use',
            created_by=self.user
        )
        assets.append(asset)

    url = '/api/assets/assets/batch_change_status/'
    data = {
        'ids': [str(a.id) for a in assets],
        'new_status': 'maintenance'
    }
    response = self.client.post(url, data, format='json')

    self.assertEqual(response.status_code, status.HTTP_200_OK)
    self.assertEqual(response.data['summary']['succeeded'], 3)

    # Verify all assets updated
    for asset in assets:
        asset.refresh_from_db()
        self.assertEqual(asset.asset_status, 'maintenance')
```

**Step 2: Run test to verify it fails**

```bash
./venv/Scripts/python.exe -m pytest apps/assets/tests/test_api.py::AssetAPITest::test_batch_change_status -v
```

Expected: FAIL - 404 Not Found

**Step 3: Implement batch_change_status action**

Add to `backend/apps/assets/viewsets.py` in `AssetViewSet` class:

```python
@action(detail=False, methods=['post'])
def batch_change_status(self, request):
    """Batch change asset status."""
    from apps.common.responses.base import BaseResponse

    ids = request.data.get('ids', [])
    new_status = request.data.get('new_status')

    if not ids:
        return Response(
            {'success': False, 'error': {'code': 'MISSING_IDS', 'message': 'IDs are required'}},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not new_status:
        return Response(
            {'success': False, 'error': {'code': 'MISSING_STATUS', 'message': 'New status is required'}},
            status=status.HTTP_400_BAD_REQUEST
        )

    results = []
    succeeded = 0
    failed = 0

    for asset_id in ids:
        try:
            asset = Asset.objects.get(id=asset_id, organization_id=request.user.organization_id)
            asset.asset_status = new_status
            asset.save()
            succeeded += 1
            results.append({'id': str(asset_id), 'success': True})
        except Asset.DoesNotExist:
            failed += 1
            results.append({'id': str(asset_id), 'success': False, 'error': 'Asset not found'})

    return Response({
        'success': True,
        'message': f'Batch status change completed',
        'summary': {
            'total': len(ids),
            'succeeded': succeeded,
            'failed': failed
        },
        'results': results
    })
```

**Step 4: Run test to verify it passes**

```bash
./venv/Scripts/python.exe -m pytest apps/assets/tests/test_api.py::AssetAPITest::test_batch_change_status -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add backend/apps/assets/viewsets.py backend/apps/assets/tests/test_api.py
git commit -m "feat(assets): add batch change status endpoint"
```

---

## Phase 3: Verify All Changes

### Task 7: Run full test suite for modified modules

**Step 1: Run Insurance tests**

```bash
cd C:\Users\ND\Desktop\Notting_Project\NEWSEAMS\backend
./venv/Scripts/python.exe -m pytest apps/insurance/tests/test_api.py -v --tb=short
```

Expected: All tests PASS

**Step 2: Run Assets tests**

```bash
./venv/Scripts/python.exe -m pytest apps/assets/tests/test_api.py -v --tb=short
```

Expected: All tests PASS

**Step 3: Run business closure integration tests**

```bash
./venv/Scripts/python.exe -m pytest apps/integration/tests/test_business_closure.py -v
```

Expected: 8/8 tests PASS

---

## Summary

This plan implements 6 tasks to fix the identified API compatibility issues:

| Task | Module | Description | Estimated Time |
|------|--------|-------------|----------------|
| 1 | Insurance | Add days parameter to expiring_soon filter | 30 min |
| 2 | Insurance | Add dashboard-stats endpoint | 45 min |
| 3 | Insurance | Add record-payment alias | 20 min |
| 4 | Insurance | Implement payment schedule generation | 1 hour |
| 5 | Assets | Add QR code generation endpoint | 45 min |
| 6 | Assets | Add batch change status endpoint | 45 min |
| 7 | All | Verify with test suite | 15 min |
| **Total** | | | **~4 hours** |

### After This Plan

The following issues remain but are **out of scope** for this plan:
- **Inventory Phase 4.2, 4.4, 4.5** - Requires separate implementation plan (18-36 days)
- **Leasing frontend API layer** - Frontend only, backend complete
- **Test isolation issues** - Non-blocking, affects CI/CD only

### Next Steps After Completion

1. Run full backend test suite to verify no regressions
2. Update API documentation to reflect new endpoints
3. Coordinate with frontend team to integrate new endpoints
4. Create implementation plan for Inventory Phase 4.4 (Assignment)
