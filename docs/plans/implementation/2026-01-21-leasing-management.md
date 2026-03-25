# Leasing Management Implementation Plan

> Implementation plan for Asset Leasing Management module following TDD approach

## Document Information
| Field | Value |
|-------|-------|
| **Module** | Leasing Management |
| **PRD Reference** | `docs/plans/leasing_management/LEASING_MANAGEMENT_PRD.md` |
| **Created** | 2026-01-21 |
| **Estimated Time** | 5-6 hours |

---

## Goal

Implement a complete asset leasing management system with:
- Lease contract management (draft, active, completed, terminated states)
- Rent payment tracking and scheduling
- Asset return processing with condition assessment
- Lease extension/renewal handling
- Organization-based data isolation
- Soft delete support

---

## Architecture

```
backend/apps/leasing/
├── __init__.py
├── models.py              # 5 Models: LeaseContract, LeaseItem, RentPayment, LeaseReturn, LeaseExtension
├── serializers.py         # 5 Serializers inheriting BaseModelSerializer
├── viewsets.py            # 5 ViewSets inheriting BaseModelViewSetWithBatch
├── filters.py             # 3 FilterSets inheriting BaseModelFilter
├── urls.py                # URL routing
├── admin.py               # Django admin configuration
└── tests/
    ├── __init__.py
    └── test_api.py        # API tests

frontend/src/
├── api/leasing.js         # API client
└── views/leasing/
    └── LeaseContractList.vue  # Contract list page
```

---

## Tech Stack

- **Backend**: Django 5.0, DRF, PostgreSQL (JSONB)
- **Frontend**: Vue 3 (Composition API), Element Plus
- **Base Classes**: BaseModel, BaseModelSerializer, BaseModelViewSetWithBatch, BaseModelFilter

---

## Pre-Implementation Checklist

- [ ] Read PRD: `docs/plans/leasing_management/LEASING_MANAGEMENT_PRD.md`
- [ ] Verify BaseModel exists at `apps/common/models.py`
- [ ] Verify BaseModelSerializer exists at `apps/common/serializers/base.py`
- [ ] Verify BaseModelViewSetWithBatch exists at `apps/common/viewsets/base.py`
- [ ] Verify BaseModelFilter exists at `apps/common/filters/base.py`
- [ ] Create feature branch: `git checkout -b feature/leasing-management`

---

## Implementation Tasks (TDD Approach)

### Task 1: Create leasing module structure

**Files:**
- Create: `backend/apps/leasing/__init__.py`
- Create: `backend/apps/leasing/tests/__init__.py`

**Step 1: Create the module directory structure**
```bash
mkdir -p backend/apps/leasing/tests
```

**Step 2: Create __init__.py files**
```bash
# backend/apps/leasing/__init__.py
touch backend/apps/leasing/__init__.py
echo """Leasing management module.""" > backend/apps/leasing/__init__.py

# backend/apps/leasing/tests/__init__.py
touch backend/apps/leasing/tests/__init__.py
```

**Step 3: Verify structure**
```bash
ls -la backend/apps/leasing/
```

---

### Task 2: Implement LeaseContract Model

**Files:**
- Create: `backend/apps/leasing/models.py` (LeaseContract class)
- Test: `backend/apps/leasing/tests/test_models.py`

**Step 1: Write the failing test**

```python
# backend/apps/leasing/tests/test_models.py
"""Tests for Leasing models."""
import uuid
from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.leasing.models import LeaseContract
from apps.organizations.models import Organization
from apps.accounts.models import User


class LeaseContractModelTest(TestCase):
    """LeaseContract Model Tests."""

    def setUp(self):
        """Set up test data with unique codes."""
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.organization = Organization.objects.create(
            name=f"Test Organization {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_{self.unique_suffix}",
            email=f"test{self.unique_suffix}@example.com",
            organization=self.organization
        )

    def test_contract_no_auto_generation(self):
        """Test contract number is auto-generated."""
        contract = LeaseContract.objects.create(
            organization=self.organization,
            lessee_name=f"Test Lessee {self.unique_suffix}",
            start_date="2026-01-01",
            end_date="2026-12-31",
            total_rent=12000,
            created_by=self.user
        )
        self.assertIsNotNone(contract.contract_no)
        self.assertTrue(contract.contract_no.startswith('ZL'))

    def test_is_active_method(self):
        """Test contract is_active method."""
        from django.utils import timezone

        contract = LeaseContract.objects.create(
            organization=self.organization,
            lessee_name=f"Test Lessee {self.unique_suffix}",
            start_date="2026-01-01",
            end_date="2026-12-31",
            actual_start_date=timezone.now().date(),
            status="active",
            total_rent=12000,
            created_by=self.user
        )
        self.assertTrue(contract.is_active())

    def test_days_remaining_method(self):
        """Test days_remaining method."""
        from django.utils import timezone

        contract = LeaseContract.objects.create(
            organization=self.organization,
            lessee_name=f"Test Lessee {self.unique_suffix}",
            start_date="2026-01-01",
            end_date="2099-12-31",
            actual_end_date=timezone.now().date() + timezone.timedelta(days=30),
            total_rent=12000,
            created_by=self.user
        )
        self.assertGreaterEqual(contract.days_remaining(), 0)
```

**Step 2: Run test to verify it fails**
```bash
pytest backend/apps/leasing/tests/test_models.py::LeaseContractModelTest::test_contract_no_auto_generation -v
```
Expected: `ImportError: cannot import name 'LeaseContract'`

**Step 3: Write minimal implementation**

```python
# backend/apps/leasing/models.py
"""Leasing management models."""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from apps.common.models import BaseModel


class LeaseContract(BaseModel):
    """
    Lease Contract Model

    Manages asset leasing contracts with customers/lessees.
    Inherits from BaseModel for organization isolation and soft delete.
    """

    class Meta:
        db_table = 'lease_contracts'
        verbose_name = 'Lease Contract'
        verbose_name_plural = 'Lease Contracts'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'contract_no']),
            models.Index(fields=['organization', 'lessee_name']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'start_date', 'end_date']),
        ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('completed', 'Completed'),
        ('terminated', 'Terminated'),
        ('overdue', 'Overdue'),
    ]

    PAYMENT_TYPE_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('one_time', 'One Time'),
    ]

    # Contract Information
    contract_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Contract number (auto-generated: ZL+YYYYMM+NNNN)'
    )
    contract_name = models.CharField(
        max_length=200,
        blank=True,
        help_text='Contract name/description'
    )

    # Lessee Information
    lessee_name = models.CharField(
        max_length=200,
        db_index=True,
        help_text='Lessee (customer) name'
    )
    lessee_type = models.CharField(
        max_length=50,
        choices=[('individual', 'Individual'), ('company', 'Company')],
        default='company',
        help_text='Lessee type'
    )
    lessee_contact = models.CharField(
        max_length=100,
        blank=True,
        help_text='Primary contact person'
    )
    lessee_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Contact phone'
    )
    lessee_email = models.EmailField(
        blank=True,
        help_text='Contact email'
    )
    lessee_address = models.TextField(
        blank=True,
        help_text='Lessee address'
    )
    lessee_id_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='ID number or business license'
    )

    # Lease Period
    start_date = models.DateField(help_text='Lease start date')
    end_date = models.DateField(help_text='Lease end date')
    actual_start_date = models.DateField(
        null=True,
        blank=True,
        help_text='Actual start date (when assets are delivered)'
    )
    actual_end_date = models.DateField(
        null=True,
        blank=True,
        help_text='Actual end date (when assets are returned)'
    )

    # Financial Terms
    payment_type = models.CharField(
        max_length=50,
        choices=PAYMENT_TYPE_CHOICES,
        default='monthly',
        help_text='Payment frequency'
    )
    total_rent = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Total rent amount'
    )
    deposit_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Security deposit amount'
    )
    deposit_paid = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text='Deposit amount actually paid'
    )

    # Status
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='draft',
        db_index=True,
        help_text='Contract status'
    )

    # Approval
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leases',
        help_text='Contract approver'
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Approval timestamp'
    )

    # Terms
    terms = models.TextField(
        blank=True,
        help_text='Lease terms and conditions'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes'
    )

    def __str__(self):
        return f"{self.contract_no} - {self.lessee_name}"

    def save(self, *args, **kwargs):
        if not self.contract_no:
            self.contract_no = self._generate_contract_no()
        super().save(*args, **kwargs)

    def _generate_contract_no(self):
        """Generate contract number."""
        prefix = timezone.now().strftime('%Y%m')
        last_contract = LeaseContract.all_objects.filter(
            contract_no__startswith=f"ZL{prefix}"
        ).order_by('-contract_no').first()
        if last_contract:
            seq = int(last_contract.contract_no[-4:]) + 1
        else:
            seq = 1
        return f"ZL{prefix}{seq:04d}"

    def is_active(self):
        """Check if contract is currently active."""
        today = timezone.now().date()
        return (self.status == 'active' and
                self.actual_start_date and
                self.actual_start_date <= today and
                (not self.actual_end_date or self.actual_end_date >= today))

    def days_remaining(self):
        """Get days remaining in lease."""
        today = timezone.now().date()
        if self.actual_end_date:
            delta = self.actual_end_date - today
            return max(0, delta.days)
        elif self.end_date:
            delta = self.end_date - today
            return max(0, delta.days)
        return None

    def total_days(self):
        """Get total lease period in days."""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return None

    def unpaid_amount(self):
        """Get total unpaid rent amount."""
        from django.db.models import Sum
        return self.payments.filter(
            status__in=['pending', 'partial']
        ).aggregate(
            unpaid=Sum(models.F('amount') - models.F('paid_amount'))
        )['unpaid'] or 0
```

**Step 4: Run test to verify it passes**
```bash
pytest backend/apps/leasing/tests/test_models.py::LeaseContractModelTest -v
```
Expected: All tests pass

**Step 5: Commit**
```bash
git add backend/apps/leasing/models.py backend/apps/leasing/tests/test_models.py
git commit -m "feat(leasing): Add LeaseContract model with auto-generated contract number"
```

---

### Task 3: Implement LeaseItem Model

**Files:**
- Modify: `backend/apps/leasing/models.py` (add LeaseItem)
- Test: `backend/apps/leasing/tests/test_models.py` (add tests)

**Step 1: Write the failing test**

```python
# Add to backend/apps/leasing/tests/test_models.py

class LeaseItemModelTest(TestCase):
    """LeaseItem Model Tests."""

    def setUp(self):
        """Set up test data with unique codes."""
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.organization = Organization.objects.create(
            name=f"Test Organization {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_{self.unique_suffix}",
            email=f"test{self.unique_suffix}@example.com",
            organization=self.organization
        )
        self.contract = LeaseContract.objects.create(
            organization=self.organization,
            lessee_name=f"Test Lessee {self.unique_suffix}",
            start_date="2026-01-01",
            end_date="2026-12-31",
            total_rent=12000,
            created_by=self.user
        )
        # Create asset
        from apps.assets.models import Asset, AssetCategory, Location
        self.category = AssetCategory.objects.create(
            name=f"Test Category {self.unique_suffix}",
            code=f"CAT_{self.unique_suffix}",
            organization=self.organization
        )
        self.location = Location.objects.create(
            name=f"Test Location {self.unique_suffix}",
            path=f"Test Location {self.unique_suffix}",
            organization=self.organization
        )
        self.asset = Asset.objects.create(
            asset_code=f"ASSET_{self.unique_suffix}",
            asset_name=f"Test Asset {self.unique_suffix}",
            asset_category=self.category,
            location=self.location,
            purchase_price=1000,
            purchase_date="2026-01-01",
            organization=self.organization,
            created_by=self.user
        )

    def test_lease_item_creation(self):
        """Test lease item creation."""
        from apps.leasing.models import LeaseItem

        item = LeaseItem.objects.create(
            organization=self.organization,
            contract=self.contract,
            asset=self.asset,
            daily_rate=50.00,
            start_condition="good",
            created_by=self.user
        )
        self.assertEqual(item.daily_rate, 50.00)
        self.assertEqual(item.asset, self.asset)

    def test_days_leased_property(self):
        """Test days_leased property."""
        from apps.leasing.models import LeaseItem

        item = LeaseItem.objects.create(
            organization=self.organization,
            contract=self.contract,
            asset=self.asset,
            daily_rate=50.00,
            actual_start_date="2026-01-01",
            actual_end_date="2026-01-31",
            start_condition="good",
            created_by=self.user
        )
        self.assertEqual(item.days_leased, 31)

    def test_total_rent_property(self):
        """Test total_rent property."""
        from apps.leasing.models import LeaseItem

        item = LeaseItem.objects.create(
            organization=self.organization,
            contract=self.contract,
            asset=self.asset,
            daily_rate=50.00,
            actual_start_date="2026-01-01",
            actual_end_date="2026-01-10",
            start_condition="good",
            created_by=self.user
        )
        self.assertEqual(item.total_rent, 500.00)  # 50 * 10 days
```

**Step 2: Run test to verify it fails**
```bash
pytest backend/apps/leasing/tests/test_models.py::LeaseItemModelTest -v
```
Expected: `ImportError: cannot import name 'LeaseItem'`

**Step 3: Write minimal implementation**

```python
# Add to backend/apps/leasing/models.py

class LeaseItem(BaseModel):
    """
    Lease Item Model

    Individual assets included in a lease contract.
    """

    class Meta:
        db_table = 'lease_items'
        verbose_name = 'Lease Item'
        verbose_name_plural = 'Lease Items'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'contract']),
            models.Index(fields=['organization', 'asset']),
        ]

    CONDITION_CHOICES = [
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
    ]

    contract = models.ForeignKey(
        LeaseContract,
        on_delete=models.CASCADE,
        related_name='items',
        help_text='Parent lease contract'
    )
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.PROTECT,
        related_name='lease_items',
        help_text='Leased asset'
    )

    # Pricing
    daily_rate = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Daily rental rate'
    )
    insured_value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Insured value for this asset'
    )

    # Dates
    actual_start_date = models.DateField(
        null=True,
        blank=True,
        help_text='Actual delivery date'
    )
    actual_end_date = models.DateField(
        null=True,
        blank=True,
        help_text='Actual return date'
    )

    # Condition tracking
    start_condition = models.CharField(
        max_length=50,
        choices=CONDITION_CHOICES,
        default='good',
        help_text='Asset condition at start'
    )
    return_condition = models.CharField(
        max_length=50,
        choices=CONDITION_CHOICES,
        blank=True,
        help_text='Asset condition at return'
    )
    damage_description = models.TextField(
        blank=True,
        help_text='Description of any damage'
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text='Item notes'
    )

    def __str__(self):
        return f"{self.contract.contract_no} - {self.asset.asset_name}"

    @property
    def days_leased(self):
        """Calculate actual days leased."""
        if self.actual_start_date and self.actual_end_date:
            return (self.actual_end_date - self.actual_start_date).days + 1
        return 0

    @property
    def total_rent(self):
        """Calculate total rent for this item."""
        return float(self.daily_rate) * self.days_leased
```

**Step 4: Run test to verify it passes**
```bash
pytest backend/apps/leasing/tests/test_models.py::LeaseItemModelTest -v
```
Expected: All tests pass

**Step 5: Commit**
```bash
git add backend/apps/leasing/models.py backend/apps/leasing/tests/test_models.py
git commit -m "feat(leasing): Add LeaseItem model with condition tracking"
```

---

### Task 4: Implement RentPayment Model

**Files:**
- Modify: `backend/apps/leasing/models.py` (add RentPayment)
- Test: `backend/apps/leasing/tests/test_models.py` (add tests)

**Step 1: Write the failing test**

```python
# Add to backend/apps/leasing/tests/test_models.py

class RentPaymentModelTest(TestCase):
    """RentPayment Model Tests."""

    def setUp(self):
        """Set up test data with unique codes."""
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.organization = Organization.objects.create(
            name=f"Test Organization {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_{self.unique_suffix}",
            email=f"test{self.unique_suffix}@example.com",
            organization=self.organization
        )
        self.contract = LeaseContract.objects.create(
            organization=self.organization,
            lessee_name=f"Test Lessee {self.unique_suffix}",
            start_date="2026-01-01",
            end_date="2026-12-31",
            total_rent=12000,
            created_by=self.user
        )

    def test_payment_no_auto_generation(self):
        """Test payment number is auto-generated."""
        from apps.leasing.models import RentPayment

        payment = RentPayment.objects.create(
            organization=self.organization,
            contract=self.contract,
            due_date="2026-01-31",
            amount=1000.00,
            created_by=self.user
        )
        self.assertIsNotNone(payment.payment_no)
        self.assertTrue(payment.payment_no.startswith('PAY'))

    def test_outstanding_amount_property(self):
        """Test outstanding_amount property."""
        from apps.leasing.models import RentPayment

        payment = RentPayment.objects.create(
            organization=self.organization,
            contract=self.contract,
            due_date="2026-01-31",
            amount=1000.00,
            paid_amount=300.00,
            status="partial",
            created_by=self.user
        )
        self.assertEqual(payment.outstanding_amount, 700.00)

    def test_is_overdue_property(self):
        """Test is_overdue property."""
        from apps.leasing.models import RentPayment
        from django.utils import timezone

        past_date = timezone.now().date() - timezone.timedelta(days=10)
        payment = RentPayment.objects.create(
            organization=self.organization,
            contract=self.contract,
            due_date=past_date,
            amount=1000.00,
            status="pending",
            created_by=self.user
        )
        self.assertTrue(payment.is_overdue)
```

**Step 2: Run test to verify it fails**
```bash
pytest backend/apps/leasing/tests/test_models.py::RentPaymentModelTest -v
```
Expected: `ImportError: cannot import name 'RentPayment'`

**Step 3: Write minimal implementation**

```python
# Add to backend/apps/leasing/models.py

class RentPayment(BaseModel):
    """
    Rent Payment Model

    Tracks scheduled and actual rent payments for a lease.
    """

    class Meta:
        db_table = 'rent_payments'
        verbose_name = 'Rent Payment'
        verbose_name_plural = 'Rent Payments'
        ordering = ['due_date']
        indexes = [
            models.Index(fields=['organization', 'contract']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'due_date']),
        ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('waived', 'Waived'),
    ]

    contract = models.ForeignKey(
        LeaseContract,
        on_delete=models.CASCADE,
        related_name='payments',
        help_text='Related lease contract'
    )

    # Payment Details
    payment_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Payment number (auto-generated)'
    )
    due_date = models.DateField(
        db_index=True,
        help_text='Payment due date'
    )
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Payment amount due'
    )
    paid_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text='Amount actually paid'
    )

    # Status
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Payment status'
    )

    # Payment Details
    paid_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date payment was received'
    )
    payment_method = models.CharField(
        max_length=50,
        blank=True,
        help_text='Payment method (cash, transfer, etc.)'
    )
    payment_reference = models.CharField(
        max_length=200,
        blank=True,
        help_text='Payment reference/check number'
    )

    # Invoice
    invoice_no = models.CharField(
        max_length=100,
        blank=True,
        help_text='Invoice number'
    )
    invoice_date = models.DateField(
        null=True,
        blank=True,
        help_text='Invoice date'
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text='Payment notes'
    )

    def __str__(self):
        return f"{self.payment_no} - {self.contract.lessee_name}"

    def save(self, *args, **kwargs):
        if not self.payment_no:
            import uuid
            self.payment_no = f"PAY{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)

    @property
    def outstanding_amount(self):
        """Get outstanding (unpaid) amount."""
        return float(self.amount) - float(self.paid_amount)

    @property
    def is_overdue(self):
        """Check if payment is overdue."""
        return (self.status in ['pending', 'partial'] and
                self.due_date < timezone.now().date())
```

**Step 4: Run test to verify it passes**
```bash
pytest backend/apps/leasing/tests/test_models.py::RentPaymentModelTest -v
```
Expected: All tests pass

**Step 5: Commit**
```bash
git add backend/apps/leasing/models.py backend/apps/leasing/tests/test_models.py
git commit -m "feat(leasing): Add RentPayment model with auto-generated payment number"
```

---

### Task 5: Implement LeaseReturn Model

**Files:**
- Modify: `backend/apps/leasing/models.py` (add LeaseReturn)
- Test: `backend/apps/leasing/tests/test_models.py` (add tests)

**Step 1: Write the failing test**

```python
# Add to backend/apps/leasing/tests/test_models.py

class LeaseReturnModelTest(TestCase):
    """LeaseReturn Model Tests."""

    def setUp(self):
        """Set up test data with unique codes."""
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.organization = Organization.objects.create(
            name=f"Test Organization {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_{self.unique_suffix}",
            email=f"test{self.unique_suffix}@example.com",
            organization=self.organization
        )
        self.contract = LeaseContract.objects.create(
            organization=self.organization,
            lessee_name=f"Test Lessee {self.unique_suffix}",
            start_date="2026-01-01",
            end_date="2026-12-31",
            total_rent=12000,
            created_by=self.user
        )
        # Create asset
        from apps.assets.models import Asset, AssetCategory, Location
        self.category = AssetCategory.objects.create(
            name=f"Test Category {self.unique_suffix}",
            code=f"CAT_{self.unique_suffix}",
            organization=self.organization
        )
        self.location = Location.objects.create(
            name=f"Test Location {self.unique_suffix}",
            path=f"Test Location {self.unique_suffix}",
            organization=self.organization
        )
        self.asset = Asset.objects.create(
            asset_code=f"ASSET_{self.unique_suffix}",
            asset_name=f"Test Asset {self.unique_suffix}",
            asset_category=self.category,
            location=self.location,
            purchase_price=1000,
            purchase_date="2026-01-01",
            organization=self.organization,
            created_by=self.user
        )

    def test_return_no_auto_generation(self):
        """Test return number is auto-generated."""
        from apps.leasing.models import LeaseReturn

        return_obj = LeaseReturn.objects.create(
            organization=self.organization,
            contract=self.contract,
            asset=self.asset,
            return_date="2026-12-31",
            condition="good",
            created_by=self.user
        )
        self.assertIsNotNone(return_obj.return_no)
        self.assertTrue(return_obj.return_no.startswith('LR'))
```

**Step 2: Run test to verify it fails**
```bash
pytest backend/apps/leasing/tests/test_models.py::LeaseReturnModelTest -v
```
Expected: `ImportError: cannot import name 'LeaseReturn'`

**Step 3: Write minimal implementation**

```python
# Add to backend/apps/leasing/models.py

class LeaseReturn(BaseModel):
    """
    Lease Return Model

    Records asset return information and condition assessment.
    """

    class Meta:
        db_table = 'lease_returns'
        verbose_name = 'Lease Return'
        verbose_name_plural = 'Lease Returns'
        ordering = ['-return_date']
        indexes = [
            models.Index(fields=['organization', 'contract']),
            models.Index(fields=['organization', 'return_date']),
        ]

    CONDITION_CHOICES = [
        ('excellent', 'Excellent - Like New'),
        ('good', 'Good - Normal Wear'),
        ('fair', 'Fair - Minor Damage'),
        ('poor', 'Poor - Major Damage'),
        ('broken', 'Broken - Needs Repair'),
        ('lost', 'Lost - Not Returnable'),
    ]

    contract = models.ForeignKey(
        LeaseContract,
        on_delete=models.CASCADE,
        related_name='returns',
        help_text='Related lease contract'
    )
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.PROTECT,
        related_name='lease_returns',
        help_text='Returned asset'
    )

    # Return Information
    return_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Return number (auto-generated)'
    )
    return_date = models.DateField(help_text='Return date')
    received_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_returns',
        help_text='Person who received the return'
    )

    # Condition Assessment
    condition = models.CharField(
        max_length=50,
        choices=CONDITION_CHOICES,
        help_text='Asset return condition'
    )
    damage_description = models.TextField(
        blank=True,
        help_text='Description of any damage'
    )

    # Financial
    damage_fee = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Fee charged for damage'
    )
    deposit_deduction = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Amount deducted from deposit'
    )
    refund_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Refund amount due to lessee'
    )

    # Photos/Documentation
    photos = models.JSONField(
        default=list,
        blank=True,
        help_text='Photos of returned asset'
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text='Return notes'
    )

    def __str__(self):
        return f"{self.return_no} - {self.asset.asset_name}"

    def save(self, *args, **kwargs):
        if not self.return_no:
            prefix = timezone.now().strftime('%Y%m')
            self.return_no = f"LR{prefix}{timezone.now().strftime('%H%M%S')}"
        super().save(*args, **kwargs)
```

**Step 4: Run test to verify it passes**
```bash
pytest backend/apps/leasing/tests/test_models.py::LeaseReturnModelTest -v
```
Expected: All tests pass

**Step 5: Commit**
```bash
git add backend/apps/leasing/models.py backend/apps/leasing/tests/test_models.py
git commit -m "feat(leasing): Add LeaseReturn model with condition tracking"
```

---

### Task 6: Implement LeaseExtension Model

**Files:**
- Modify: `backend/apps/leasing/models.py` (add LeaseExtension)
- Test: `backend/apps/leasing/tests/test_models.py` (add tests)

**Step 1: Write the failing test**

```python
# Add to backend/apps/leasing/tests/test_models.py

class LeaseExtensionModelTest(TestCase):
    """LeaseExtension Model Tests."""

    def setUp(self):
        """Set up test data with unique codes."""
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.organization = Organization.objects.create(
            name=f"Test Organization {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_{self.unique_suffix}",
            email=f"test{self.unique_suffix}@example.com",
            organization=self.organization
        )
        self.contract = LeaseContract.objects.create(
            organization=self.organization,
            lessee_name=f"Test Lessee {self.unique_suffix}",
            start_date="2026-01-01",
            end_date="2026-12-31",
            total_rent=12000,
            created_by=self.user
        )

    def test_extension_no_auto_generation(self):
        """Test extension number is auto-generated."""
        from apps.leasing.models import LeaseExtension

        extension = LeaseExtension.objects.create(
            organization=self.organization,
            contract=self.contract,
            original_end_date="2026-12-31",
            new_end_date="2027-03-31",
            additional_rent=3000,
            created_by=self.user
        )
        self.assertIsNotNone(extension.extension_no)
        self.assertTrue(extension.extension_no.startswith('EXT'))

    def test_additional_days_property(self):
        """Test additional_days property."""
        from apps.leasing.models import LeaseExtension

        extension = LeaseExtension.objects.create(
            organization=self.organization,
            contract=self.contract,
            original_end_date="2026-12-31",
            new_end_date="2027-01-31",
            additional_rent=1000,
            created_by=self.user
        )
        self.assertEqual(extension.additional_days, 31)
```

**Step 2: Run test to verify it fails**
```bash
pytest backend/apps/leasing/tests/test_models.py::LeaseExtensionModelTest -v
```
Expected: `ImportError: cannot import name 'LeaseExtension'`

**Step 3: Write minimal implementation**

```python
# Add to backend/apps/leasing/models.py

class LeaseExtension(BaseModel):
    """
    Lease Extension Model

    Records lease contract extensions and renewals.
    """

    class Meta:
        db_table = 'lease_extensions'
        verbose_name = 'Lease Extension'
        verbose_name_plural = 'Lease Extensions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'contract']),
        ]

    contract = models.ForeignKey(
        LeaseContract,
        on_delete=models.CASCADE,
        related_name='extensions',
        help_text='Original contract being extended'
    )

    # Extension Details
    extension_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Extension number'
    )
    original_end_date = models.DateField(help_text='Original end date before extension')
    new_end_date = models.DateField(help_text='New end date after extension')

    # Financial
    additional_rent = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
        help_text='Additional rent for extension period'
    )

    # Reason
    reason = models.TextField(blank=True, help_text='Reason for extension')
    notes = models.TextField(blank=True, help_text='Additional notes')

    # Approval
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_extensions',
        help_text='Extension approver'
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Approval timestamp'
    )

    def __str__(self):
        return f"{self.extension_no} - {self.contract.contract_no}"

    def save(self, *args, **kwargs):
        if not self.extension_no:
            import uuid
            self.extension_no = f"EXT{uuid.uuid4().hex[:10].upper()}"
        super().save(*args, **kwargs)

    @property
    def additional_days(self):
        """Get number of days added."""
        if self.original_end_date and self.new_end_date:
            return (self.new_end_date - self.original_end_date).days
        return 0
```

**Step 4: Run test to verify it passes**
```bash
pytest backend/apps/leasing/tests/test_models.py::LeaseExtensionModelTest -v
```
Expected: All tests pass

**Step 5: Commit**
```bash
git add backend/apps/leasing/models.py backend/apps/leasing/tests/test_models.py
git commit -m "feat(leasing): Add LeaseExtension model with days calculation"
```

---

### Task 7: Create Serializers

**Files:**
- Create: `backend/apps/leasing/serializers.py`
- Test: `backend/apps/leasing/tests/test_serializers.py`

**Step 1: Write the failing test**

```python
# backend/apps/leasing/tests/test_serializers.py
"""Tests for Leasing serializers."""
import uuid
from django.test import TestCase
from apps.leasing.serializers import (
    LeaseContractSerializer, LeaseItemSerializer,
    RentPaymentSerializer, LeaseReturnSerializer, LeaseExtensionSerializer
)
from apps.leasing.models import LeaseContract, LeaseItem, RentPayment
from apps.assets.models import Asset, AssetCategory, Location
from apps.organizations.models import Organization
from apps.accounts.models import User


class LeaseContractSerializerTest(TestCase):
    """LeaseContract Serializer Tests."""

    def setUp(self):
        """Set up test data with unique codes."""
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.organization = Organization.objects.create(
            name=f"Test Organization {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_{self.unique_suffix}",
            email=f"test{self.unique_suffix}@example.com",
            organization=self.organization
        )

    def test_serializer_validates_dates(self):
        """Test serializer validates end_date after start_date."""
        serializer = LeaseContractSerializer(data={
            'lessee_name': f'Test Lessee {self.unique_suffix}',
            'start_date': '2026-12-31',
            'end_date': '2026-01-01',  # End before start
            'total_rent': 12000
        })
        self.assertFalse(serializer.is_valid())
        self.assertIn('end_date', serializer.errors)

    def test_serializer_creates_contract(self):
        """Test serializer creates contract successfully."""
        data = {
            'lessee_name': f'Test Lessee {self.unique_suffix}',
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'total_rent': 12000,
            'deposit_amount': 2000
        }
        serializer = LeaseContractSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        contract = serializer.save(
            organization=self.organization,
            created_by=self.user
        )
        self.assertIsNotNone(contract.contract_no)
        self.assertEqual(contract.lessee_name, data['lessee_name'])
```

**Step 2: Run test to verify it fails**
```bash
pytest backend/apps/leasing/tests/test_serializers.py -v
```
Expected: `ImportError: cannot import name 'LeaseContractSerializer'`

**Step 3: Write minimal implementation**

```python
# backend/apps/leasing/serializers.py
"""Leasing management serializers."""

from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer
from .models import (
    LeaseContract, LeaseItem, RentPayment,
    LeaseReturn, LeaseExtension
)


class LeaseItemSerializer(BaseModelSerializer):
    """Lease Item Serializer."""
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    days_leased = serializers.ReadOnlyField()
    total_rent = serializers.ReadOnlyField()

    class Meta(BaseModelSerializer.Meta):
        model = LeaseItem
        fields = BaseModelSerializer.Meta.fields + [
            'contract', 'asset', 'asset_name', 'asset_code',
            'daily_rate', 'insured_value',
            'actual_start_date', 'actual_end_date',
            'start_condition', 'return_condition', 'damage_description',
            'days_leased', 'total_rent', 'notes',
        ]


class RentPaymentSerializer(BaseModelSerializer):
    """Rent Payment Serializer."""
    contract_no = serializers.CharField(source='contract.contract_no', read_only=True)
    lessee_name = serializers.CharField(source='contract.lessee_name', read_only=True)
    outstanding_amount = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()

    class Meta(BaseModelSerializer.Meta):
        model = RentPayment
        fields = BaseModelSerializer.Meta.fields + [
            'contract', 'contract_no', 'lessee_name',
            'payment_no', 'due_date', 'amount', 'paid_amount',
            'outstanding_amount', 'is_overdue',
            'status', 'paid_date', 'payment_method', 'payment_reference',
            'invoice_no', 'invoice_date', 'notes',
        ]


class LeaseContractSerializer(BaseModelSerializer):
    """Lease Contract Serializer."""
    lessee_name = serializers.CharField(required=True)
    items = LeaseItemSerializer(many=True, read_only=True)
    payments = RentPaymentSerializer(many=True, read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    total_days = serializers.IntegerField(read_only=True)
    unpaid_amount = serializers.DecimalField(
        max_digits=14, decimal_places=2, read_only=True
    )
    approved_by_name = serializers.CharField(
        source='approved_by.username', read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = LeaseContract
        fields = BaseModelSerializer.Meta.fields + [
            # Contract
            'contract_no', 'contract_name',
            # Lessee
            'lessee_name', 'lessee_type', 'lessee_contact',
            'lessee_phone', 'lessee_email', 'lessee_address', 'lessee_id_number',
            # Dates
            'start_date', 'end_date', 'actual_start_date', 'actual_end_date',
            # Financial
            'payment_type', 'total_rent', 'deposit_amount', 'deposit_paid',
            # Status
            'status', 'is_active', 'days_remaining', 'total_days',
            # Approval
            'approved_by', 'approved_by_name', 'approved_at',
            # Relations
            'items', 'payments', 'unpaid_amount',
            # Terms
            'terms', 'notes',
        ]

    def validate(self, data):
        """Validate contract dates."""
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date and end_date <= start_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date'
            })

        return data


class LeaseReturnSerializer(BaseModelSerializer):
    """Lease Return Serializer."""
    contract_no = serializers.CharField(source='contract.contract_no', read_only=True)
    lessee_name = serializers.CharField(source='contract.lessee_name', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    received_by_name = serializers.CharField(
        source='received_by.username', read_only=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = LeaseReturn
        fields = BaseModelSerializer.Meta.fields + [
            'contract', 'contract_no', 'lessee_name',
            'asset', 'asset_name', 'asset_code',
            'return_no', 'return_date', 'received_by', 'received_by_name',
            'condition', 'damage_description',
            'damage_fee', 'deposit_deduction', 'refund_amount',
            'photos', 'notes',
        ]


class LeaseExtensionSerializer(BaseModelSerializer):
    """Lease Extension Serializer."""
    contract_no = serializers.CharField(source='contract.contract_no', read_only=True)
    lessee_name = serializers.CharField(source='contract.lessee_name', read_only=True)
    approved_by_name = serializers.CharField(
        source='approved_by.username', read_only=True
    )
    additional_days = serializers.ReadOnlyField()

    class Meta(BaseModelSerializer.Meta):
        model = LeaseExtension
        fields = BaseModelSerializer.Meta.fields + [
            'contract', 'contract_no', 'lessee_name',
            'extension_no', 'original_end_date', 'new_end_date', 'additional_days',
            'additional_rent', 'reason', 'notes',
            'approved_by', 'approved_by_name', 'approved_at',
        ]
```

**Step 4: Run test to verify it passes**
```bash
pytest backend/apps/leasing/tests/test_serializers.py -v
```
Expected: All tests pass

**Step 5: Commit**
```bash
git add backend/apps/leasing/serializers.py backend/apps/leasing/tests/test_serializers.py
git commit -m "feat(leasing): Add serializers for all leasing models"
```

---

### Task 8: Create Filters

**Files:**
- Create: `backend/apps/leasing/filters.py`
- Test: `backend/apps/leasing/tests/test_filters.py`

**Step 1: Write the failing test**

```python
# backend/apps/leasing/tests/test_filters.py
"""Tests for Leasing filters."""
import uuid
from django.test import TestCase
from apps.leasing.filters import LeaseContractFilter, RentPaymentFilter
from apps.leasing.models import LeaseContract, RentPayment
from apps.organizations.models import Organization
from apps.accounts.models import User


class LeaseContractFilterTest(TestCase):
    """LeaseContract Filter Tests."""

    def setUp(self):
        """Set up test data with unique codes."""
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.organization = Organization.objects.create(
            name=f"Test Organization {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_{self.unique_suffix}",
            email=f"test{self.unique_suffix}@example.com",
            organization=self.organization
        )

        # Create contracts with different statuses
        LeaseContract.objects.create(
            organization=self.organization,
            contract_no=f"ZL202601{self.unique_suffix[:2]}01",
            lessee_name=f'Active Lessee {self.unique_suffix}',
            start_date='2026-01-01',
            end_date='2026-12-31',
            status='active',
            total_rent=12000,
            created_by=self.user
        )
        LeaseContract.objects.create(
            organization=self.organization,
            contract_no=f"ZL202601{self.unique_suffix[:2]}02",
            lessee_name=f'Draft Lessee {self.unique_suffix}',
            start_date='2026-01-01',
            end_date='2026-12-31',
            status='draft',
            total_rent=6000,
            created_by=self.user
        )

    def test_filter_by_status(self):
        """Test filtering by status."""
        from django_filters import FilterSet

        filter_qs = LeaseContractFilter(
            {'status': 'active'},
            queryset=LeaseContract.objects.filter(organization=self.organization)
        )
        results = list(filter_qs.qs)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, 'active')
```

**Step 2: Run test to verify it fails**
```bash
pytest backend/apps/leasing/tests/test_filters.py -v
```
Expected: `ImportError: cannot import name 'LeaseContractFilter'`

**Step 3: Write minimal implementation**

```python
# backend/apps/leasing/filters.py
"""Leasing management filters."""

from django_filters import rest_framework as filters
from apps.common.filters.base import BaseModelFilter
from .models import LeaseContract, RentPayment, LeaseReturn


class LeaseContractFilter(BaseModelFilter):
    """Lease Contract Filter."""

    status = filters.CharFilter()
    lessee_name = filters.CharFilter(lookup_expr='icontains')
    date_from = filters.DateFilter(field_name='start_date', lookup_expr='gte')
    date_to = filters.DateFilter(field_name='end_date', lookup_expr='lte')
    expires_soon = filters.BooleanFilter(method='filter_expires_soon')

    def filter_expires_soon(self, queryset, name, value):
        """Filter contracts expiring within 30 days."""
        if value:
            from django.utils import timezone
            delta = timezone.now().date() + timezone.timedelta(days=30)
            return queryset.filter(
                end_date__lte=delta,
                status='active'
            )
        return queryset

    class Meta(BaseModelFilter.Meta):
        model = LeaseContract
        fields = BaseModelFilter.Meta.fields + [
            'status', 'lessee_name', 'start_date', 'end_date',
        ]


class RentPaymentFilter(BaseModelFilter):
    """Rent Payment Filter."""

    status = filters.CharFilter()
    due_from = filters.DateFilter(field_name='due_date', lookup_expr='gte')
    due_to = filters.DateFilter(field_name='due_date', lookup_expr='lte')
    overdue_only = filters.BooleanFilter(method='filter_overdue')

    def filter_overdue(self, queryset, name, value):
        """Filter only overdue payments."""
        if value:
            from django.utils import timezone
            return queryset.filter(
                due_date__lt=timezone.now().date(),
                status__in=['pending', 'partial']
            )
        return queryset

    class Meta(BaseModelFilter.Meta):
        model = RentPayment
        fields = BaseModelFilter.Meta.fields + [
            'status', 'due_date',
        ]


class LeaseReturnFilter(BaseModelFilter):
    """Lease Return Filter."""

    condition = filters.CharFilter()
    date_from = filters.DateFilter(field_name='return_date', lookup_expr='gte')
    date_to = filters.DateFilter(field_name='return_date', lookup_expr='lte')

    class Meta(BaseModelFilter.Meta):
        model = LeaseReturn
        fields = BaseModelFilter.Meta.fields + [
            'condition', 'return_date',
        ]
```

**Step 4: Run test to verify it passes**
```bash
pytest backend/apps/leasing/tests/test_filters.py -v
```
Expected: All tests pass

**Step 5: Commit**
```bash
git add backend/apps/leasing/filters.py backend/apps/leasing/tests/test_filters.py
git commit -m "feat(leasing): Add filters for contracts, payments, and returns"
```

---

### Task 9: Create ViewSets

**Files:**
- Create: `backend/apps/leasing/viewsets.py`
- Test: `backend/apps/leasing/tests/test_api.py`

**Step 1: Write the failing test**

```python
# backend/apps/leasing/tests/test_api.py
"""Tests for Leasing API endpoints."""
import uuid
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from apps.leasing.models import LeaseContract, LeaseItem, RentPayment
from apps.assets.models import Asset, AssetCategory, Location
from apps.organizations.models import Organization
from apps.accounts.models import User


class LeaseContractAPITest(APITestCase):
    """LeaseContract API Tests."""

    def setUp(self):
        """Set up test data with unique codes."""
        self.client = APIClient()
        self.unique_suffix = uuid.uuid4().hex[:8]

        self.organization = Organization.objects.create(
            name=f"Test Organization {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_{self.unique_suffix}",
            email=f"test{self.unique_suffix}@example.com",
            organization=self.organization
        )
        self.client.force_authenticate(user=self.user)

    def test_list_contracts(self):
        """Test listing lease contracts."""
        # Create test contracts
        for i in range(3):
            LeaseContract.objects.create(
                organization=self.organization,
                contract_no=f"ZL202601{self.unique_suffix[:2]}{i:02d}",
                lessee_name=f'Test Lessee {i}',
                start_date='2026-01-01',
                end_date='2026-12-31',
                total_rent=12000 + i * 1000,
                created_by=self.user
            )

        url = '/api/lease-contracts/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['data']['count'], 3)

    def test_create_contract(self):
        """Test creating a lease contract."""
        url = '/api/lease-contracts/'
        data = {
            'contract_name': 'Test Lease',
            'lessee_name': f'Test Lessee {self.unique_suffix}',
            'lessee_type': 'company',
            'lessee_phone': '13800138000',
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'payment_type': 'monthly',
            'total_rent': 12000,
            'deposit_amount': 2000
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['lessee_name'], data['lessee_name'])

    def test_activate_contract(self):
        """Test activating a draft contract."""
        contract = LeaseContract.objects.create(
            organization=self.organization,
            lessee_name=f'Test Lessee {self.unique_suffix}',
            start_date='2026-01-01',
            end_date='2026-12-31',
            status='draft',
            total_rent=12000,
            created_by=self.user
        )

        url = f'/api/lease-contracts/{contract.id}/activate/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        contract.refresh_from_db()
        self.assertEqual(contract.status, 'active')
```

**Step 2: Run test to verify it fails**
```bash
pytest backend/apps/leasing/tests/test_api.py::LeaseContractAPITest -v
```
Expected: `404 Not Found` or route not registered

**Step 3: Write minimal implementation**

```python
# backend/apps/leasing/viewsets.py
"""Leasing management viewsets."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.db.models import Exists, OuterRef
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from .models import (
    LeaseContract, LeaseItem, RentPayment,
    LeaseReturn, LeaseExtension
)
from .serializers import (
    LeaseContractSerializer, LeaseItemSerializer, RentPaymentSerializer,
    LeaseReturnSerializer, LeaseExtensionSerializer
)
from .filters import (
    LeaseContractFilter, RentPaymentFilter, LeaseReturnFilter
)


class LeaseContractViewSet(BaseModelViewSetWithBatch):
    """Lease Contract ViewSet."""
    queryset = LeaseContract.objects.all()
    serializer_class = LeaseContractSerializer
    filterset_class = LeaseContractFilter

    def perform_create(self, serializer):
        """Set organization and created_by."""
        serializer.save(
            organization_id=self.request.user.organization_id,
            created_by=self.request.user
        )

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a draft contract."""
        contract = self.get_object()

        if contract.status != 'draft':
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'INVALID_STATUS',
                        'message': 'Only draft contracts can be activated'
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        contract.status = 'active'
        contract.actual_start_date = timezone.now().date()
        contract.approved_by = request.user
        contract.approved_at = timezone.now()
        contract.save()

        # Generate payment schedule
        self._generate_payment_schedule(contract)

        serializer = self.get_serializer(contract)
        return Response({
            'success': True,
            'message': 'Contract activated successfully',
            'data': serializer.data
        })

    def _generate_payment_schedule(self, contract):
        """Generate rent payment schedule based on payment type."""
        if contract.payment_type == 'one_time':
            RentPayment.objects.create(
                organization_id=contract.organization_id,
                contract=contract,
                due_date=contract.start_date,
                amount=contract.total_rent,
                created_by=contract.created_by
            )
            return

        # Calculate payment intervals
        intervals = {
            'daily': timedelta(days=1),
            'weekly': timedelta(weeks=1),
            'monthly': timedelta(days=30),
            'quarterly': timedelta(days=90),
        }

        interval = intervals.get(contract.payment_type, timedelta(days=30))
        payment_count = max(1, int(contract.total_days() / interval.days))
        payment_amount = contract.total_rent / payment_count

        current_date = contract.start_date
        for i in range(payment_count):
            RentPayment.objects.create(
                organization_id=contract.organization_id,
                contract=contract,
                due_date=current_date,
                amount=round(payment_amount, 2),
                created_by=contract.created_by
            )
            current_date += interval

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete/Close a contract."""
        contract = self.get_object()

        if contract.status not in ['active', 'suspended']:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'INVALID_STATUS',
                        'message': 'Only active or suspended contracts can be completed'
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        contract.status = 'completed'
        contract.actual_end_date = timezone.now().date()
        contract.save()

        serializer = self.get_serializer(contract)
        return Response({
            'success': True,
            'message': 'Contract completed',
            'data': serializer.data
        })

    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get contracts expiring within 30 days."""
        delta = timezone.now().date() + timedelta(days=30)

        contracts = self.queryset.filter(
            end_date__lte=delta,
            status='active'
        )

        page = self.paginate_queryset(contracts)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get contracts with overdue payments."""
        overdue_payments = RentPayment.objects.filter(
            contract=OuterRef('pk'),
            due_date__lt=timezone.now().date(),
            status__in=['pending', 'partial']
        )

        contracts = self.queryset.filter(
            status='active'
        ).filter(Exists(overdue_payments))

        page = self.paginate_queryset(contracts)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class LeaseItemViewSet(BaseModelViewSetWithBatch):
    """Lease Item ViewSet."""
    queryset = LeaseItem.objects.all()
    serializer_class = LeaseItemSerializer
    filterset_class = BaseModelFilter


class RentPaymentViewSet(BaseModelViewSetWithBatch):
    """Rent Payment ViewSet."""
    queryset = RentPayment.objects.all()
    serializer_class = RentPaymentSerializer
    filterset_class = RentPaymentFilter

    @action(detail=True, methods=['post'])
    def record_payment(self, request, pk=None):
        """Record a payment."""
        payment = self.get_object()

        amount = request.data.get('amount', 0)
        if amount <= 0:
            return Response(
                {
                    'success': False,
                    'error': {'code': 'INVALID_AMOUNT', 'message': 'Amount must be positive'}
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        payment.paid_amount += float(amount)
        payment.paid_date = timezone.now().date()
        payment.payment_method = request.data.get('payment_method', '')

        if payment.paid_amount >= payment.amount:
            payment.status = 'paid'
        else:
            payment.status = 'partial'

        payment.save()

        serializer = self.get_serializer(payment)
        return Response({
            'success': True,
            'message': 'Payment recorded',
            'data': serializer.data
        })


class LeaseReturnViewSet(BaseModelViewSetWithBatch):
    """Lease Return ViewSet."""
    queryset = LeaseReturn.objects.all()
    serializer_class = LeaseReturnSerializer
    filterset_class = LeaseReturnFilter

    def perform_create(self, serializer):
        """Set received_by and update contract."""
        return_obj = serializer.save(
            received_by=self.request.user,
            created_by=self.request.user
        )

        # Update lease item return condition
        contract = return_obj.contract
        try:
            lease_item = LeaseItem.objects.get(
                contract=contract,
                asset=return_obj.asset
            )
            lease_item.return_condition = return_obj.condition
            lease_item.damage_description = return_obj.damage_description
            lease_item.actual_end_date = return_obj.return_date
            lease_item.save()
        except LeaseItem.DoesNotExist:
            pass


class LeaseExtensionViewSet(BaseModelViewSetWithBatch):
    """Lease Extension ViewSet."""
    queryset = LeaseExtension.objects.all()
    serializer_class = LeaseExtensionSerializer
    filterset_class = BaseModelFilter

    def perform_create(self, serializer):
        """Process extension and update contract."""
        extension = serializer.save(
            created_by=self.request.user
        )

        # Update contract end date
        contract = extension.contract
        contract.end_date = extension.new_end_date
        contract.total_rent += extension.additional_rent
        contract.save()
```

**Step 4: Run test to verify it passes (after URL routing)**
```bash
pytest backend/apps/leasing/tests/test_api.py::LeaseContractAPITest -v
```
Expected: All tests pass (after URLs configured in Task 10)

**Step 5: Commit**
```bash
git add backend/apps/leasing/viewsets.py backend/apps/leasing/tests/test_api.py
git commit -m "feat(leasing): Add ViewSets with activate, complete, and payment recording actions"
```

---

### Task 10: Configure URL Routing

**Files:**
- Create: `backend/apps/leasing/urls.py`
- Modify: `backend/config/urls.py` (include leasing URLs)

**Step 1: Create leasing URLs**

```python
# backend/apps/leasing/urls.py
"""Leasing management URL configuration."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import (
    LeaseContractViewSet, LeaseItemViewSet,
    RentPaymentViewSet, LeaseReturnViewSet, LeaseExtensionViewSet
)

app_name = 'leasing'

router = DefaultRouter()
router.register(r'lease-contracts', LeaseContractViewSet, basename='leasecontract')
router.register(r'lease-items', LeaseItemViewSet, basename='leaseitem')
router.register(r'rent-payments', RentPaymentViewSet, basename='rentpayment')
router.register(r'lease-returns', LeaseReturnViewSet, basename='leasereturn')
router.register(r'lease-extensions', LeaseExtensionViewSet, basename='leaseextension')

urlpatterns = [
    path('', include(router.urls)),
]
```

**Step 2: Include in main URL config**

```python
# Add to backend/config/urls.py

urlpatterns = [
    # ... existing patterns ...
    path('api/', include('apps.leasing.urls', namespace='leasing')),
]
```

**Step 3: Verify URLs**
```bash
python manage.py show_urls | grep lease
```

**Step 4: Commit**
```bash
git add backend/apps/leasing/urls.py backend/config/urls.py
git commit -m "feat(leasing): Configure URL routing for all leasing endpoints"
```

---

### Task 11: Create Database Migration

**Files:**
- Create: `backend/apps/leasing/migrations/0001_initial.py`

**Step 1: Generate migration**
```bash
python manage.py makemigrations leasing
```

**Step 2: Review migration file**
```bash
cat backend/apps/leasing/migrations/0001_initial.py
```

**Step 3: Run migration**
```bash
python manage.py migrate leasing
```

**Step 4: Verify tables**
```bash
python manage.py dbshell
\dt lease_
\q
```

**Step 5: Commit**
```bash
git add backend/apps/leasing/migrations/
git commit -m "feat(leasing): Add initial database migration"
```

---

### Task 12: Add to Django Admin

**Files:**
- Create: `backend/apps/leasing/admin.py`

**Step 1: Create admin configuration**

```python
# backend/apps/leasing/admin.py
"""Leasing management admin configuration."""

from django.contrib import admin
from .models import (
    LeaseContract, LeaseItem, RentPayment,
    LeaseReturn, LeaseExtension
)


@admin.register(LeaseContract)
class LeaseContractAdmin(admin.ModelAdmin):
    """Lease Contract Admin."""
    list_display = [
        'contract_no', 'lessee_name', 'start_date', 'end_date',
        'status', 'total_rent', 'organization'
    ]
    list_filter = ['status', 'payment_type', 'lessee_type', 'created_at']
    search_fields = ['contract_no', 'lessee_name', 'lessee_contact']
    readonly_fields = ['contract_no', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'


@admin.register(LeaseItem)
class LeaseItemAdmin(admin.ModelAdmin):
    """Lease Item Admin."""
    list_display = ['contract', 'asset', 'daily_rate', 'start_condition', 'return_condition']
    list_filter = ['start_condition', 'return_condition', 'created_at']
    search_fields = ['contract__contract_no', 'asset__asset_name']


@admin.register(RentPayment)
class RentPaymentAdmin(admin.ModelAdmin):
    """Rent Payment Admin."""
    list_display = ['payment_no', 'contract', 'due_date', 'amount', 'paid_amount', 'status']
    list_filter = ['status', 'due_date', 'paid_date']
    search_fields = ['payment_no', 'contract__contract_no', 'contract__lessee_name']
    readonly_fields = ['payment_no']


@admin.register(LeaseReturn)
class LeaseReturnAdmin(admin.ModelAdmin):
    """Lease Return Admin."""
    list_display = ['return_no', 'contract', 'asset', 'return_date', 'condition', 'damage_fee']
    list_filter = ['condition', 'return_date']
    search_fields = ['return_no', 'contract__contract_no', 'asset__asset_name']


@admin.register(LeaseExtension)
class LeaseExtensionAdmin(admin.ModelAdmin):
    """Lease Extension Admin."""
    list_display = ['extension_no', 'contract', 'original_end_date', 'new_end_date', 'additional_rent']
    list_filter = ['created_at']
    search_fields = ['extension_no', 'contract__contract_no']
```

**Step 2: Verify admin access**
```bash
python manage.py check
```

**Step 3: Commit**
```bash
git add backend/apps/leasing/admin.py
git commit -m "feat(leasing): Add Django admin configuration"
```

---

### Task 13: Create Frontend API Layer

**Files:**
- Create: `frontend/src/api/leasing.js`

**Step 1: Create API client**

```javascript
// frontend/src/api/leasing.js
/**
 * Leasing management API client
 */

import request from '@/utils/request'

export const leaseApi = {
  // Contracts
  listContracts(params) {
    return request({
      url: '/api/lease-contracts/',
      method: 'get',
      params
    })
  },

  getContract(id) {
    return request({
      url: `/api/lease-contracts/${id}/`,
      method: 'get'
    })
  },

  createContract(data) {
    return request({
      url: '/api/lease-contracts/',
      method: 'post',
      data
    })
  },

  updateContract(id, data) {
    return request({
      url: `/api/lease-contracts/${id}/`,
      method: 'put',
      data
    })
  },

  activate(id) {
    return request({
      url: `/api/lease-contracts/${id}/activate/`,
      method: 'post'
    })
  },

  complete(id) {
    return request({
      url: `/api/lease-contracts/${id}/complete/`,
      method: 'post'
    })
  },

  getExpiringSoon(params) {
    return request({
      url: '/api/lease-contracts/expiring-soon/',
      method: 'get',
      params
    })
  },

  getOverdue(params) {
    return request({
      url: '/api/lease-contracts/overdue/',
      method: 'get',
      params
    })
  },

  // Lease Items
  listItems(params) {
    return request({
      url: '/api/lease-items/',
      method: 'get',
      params
    })
  },

  createItem(data) {
    return request({
      url: '/api/lease-items/',
      method: 'post',
      data
    })
  },

  // Payments
  listPayments(params) {
    return request({
      url: '/api/rent-payments/',
      method: 'get',
      params
    })
  },

  recordPayment(id, data) {
    return request({
      url: `/api/rent-payments/${id}/record-payment/`,
      method: 'post',
      data
    })
  },

  // Returns
  createReturn(data) {
    return request({
      url: '/api/lease-returns/',
      method: 'post',
      data
    })
  },

  // Extensions
  createExtension(data) {
    return request({
      url: '/api/lease-extensions/',
      method: 'post',
      data
    })
  }
}
```

**Step 2: Commit**
```bash
git add frontend/src/api/leasing.js
git commit -m "feat(leasing): Add frontend API client for leasing module"
```

---

### Task 14: Create Lease Contract List Page

**Files:**
- Create: `frontend/src/views/leasing/LeaseContractList.vue`

**Step 1: Create list page component**

```vue
<!-- frontend/src/views/leasing/LeaseContractList.vue -->
<template>
  <BaseListPage
    title="Lease Contracts"
    :fetch-method="fetchData"
    :columns="columns"
    :search-fields="searchFields"
    :filter-fields="filterFields"
    :custom-slots="['lessee', 'period', 'status', 'actions']"
    @row-click="handleRowClick"
    @create="handleCreate"
  >
    <template #lessee="{ row }">
      <div class="lessee-info">
        <div class="name">{{ row.lessee_name }}</div>
        <div class="contact">{{ row.lessee_phone || '-' }}</div>
      </div>
    </template>

    <template #period="{ row }">
      <div class="period-info">
        <div>{{ formatDate(row.start_date) }} ~ {{ formatDate(row.end_date) }}</div>
        <el-tag v-if="row.days_remaining !== null" size="small" type="info">
          {{ row.days_remaining }} days left
        </el-tag>
      </div>
    </template>

    <template #status="{ row }">
      <el-tag :type="getStatusType(row.status)">
        {{ getStatusLabel(row.status) }}
      </el-tag>
    </template>

    <template #actions="{ row }">
      <el-button link type="primary" @click.stop="handleView(row)">
        View
      </el-button>
      <el-button
        v-if="row.status === 'draft'"
        link
        type="success"
        @click.stop="handleActivate(row)"
      >
        Activate
      </el-button>
      <el-dropdown @command="(cmd) => handleMore(cmd, row)">
        <el-button link type="primary">
          More<el-icon><arrow-down /></el-icon>
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="items">Items</el-dropdown-item>
            <el-dropdown-item command="payments">Payments</el-dropdown-item>
            <el-dropdown-item command="extend">Extend</el-dropdown-item>
            <el-dropdown-item command="return">Return</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </template>
  </BaseListPage>
</template>

<script setup>
import { useRouter } from 'vue-router'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { leaseApi } from '@/api/leasing'
import { ElMessage } from 'element-plus'

const router = useRouter()

const columns = [
  { prop: 'contract_no', label: 'Contract No', width: 140 },
  { prop: 'lessee', label: 'Lessee', minWidth: 180, slot: true },
  { prop: 'period', label: 'Period', width: 240, slot: true },
  { prop: 'total_rent', label: 'Total Rent', width: 120 },
  { prop: 'deposit_amount', label: 'Deposit', width: 100 },
  { prop: 'status', label: 'Status', width: 100, slot: true },
  { prop: 'actions', label: 'Actions', width: 200, slot: true, fixed: 'right' }
]

const searchFields = [
  { prop: 'keyword', label: 'Search', placeholder: 'Contract No / Lessee' }
]

const filterFields = [
  {
    prop: 'status',
    label: 'Status',
    options: [
      { label: 'Draft', value: 'draft' },
      { label: 'Active', value: 'active' },
      { label: 'Completed', value: 'completed' },
      { label: 'Overdue', value: 'overdue' }
    ]
  }
]

const fetchData = (params) => leaseApi.listContracts(params)

const formatDate = (date) => {
  return date ? new Date(date).toLocaleDateString() : '-'
}

const getStatusType = (status) => {
  const types = {
    draft: 'info',
    active: 'success',
    suspended: 'warning',
    completed: '',
    terminated: 'danger',
    overdue: 'danger'
  }
  return types[status] || ''
}

const getStatusLabel = (status) => {
  const labels = {
    draft: 'Draft',
    active: 'Active',
    suspended: 'Suspended',
    completed: 'Completed',
    terminated: 'Terminated',
    overdue: 'Overdue'
  }
  return labels[status] || status
}

const handleRowClick = (row) => {
  router.push(`/leasing/${row.id}`)
}

const handleCreate = () => {
  router.push('/leasing/create')
}

const handleView = (row) => {
  router.push(`/leasing/${row.id}`)
}

const handleActivate = async (row) => {
  try {
    await leaseApi.activate(row.id)
    ElMessage.success('Contract activated successfully')
    location.reload()
  } catch (error) {
    ElMessage.error(error.message || 'Failed to activate contract')
  }
}

const handleMore = (command, row) => {
  const routes = {
    items: `/leasing/${row.id}/items`,
    payments: `/leasing/${row.id}/payments`,
    extend: `/leasing/${row.id}/extend`,
    return: `/leasing/${row.id}/return`
  }
  if (routes[command]) {
    router.push(routes[command])
  }
}
</script>

<style scoped>
.lessee-info .name {
  font-weight: 500;
}
.lessee-info .contact {
  font-size: 12px;
  color: #999;
}
.period-info > div {
  margin-bottom: 4px;
}
</style>
```

**Step 2: Commit**
```bash
git add frontend/src/views/leasing/LeaseContractList.vue
git commit -m "feat(leasing): Add lease contract list page"
```

---

### Task 15: Add Router Configuration

**Files:**
- Modify: `frontend/src/router/index.js`

**Step 1: Add leasing routes**

```javascript
// Add to frontend/src/router/index.js

{
  path: '/leasing',
  component: Layout,
  meta: { title: 'Leasing', icon: 'key' },
  children: [
    {
      path: '',
      name: 'LeaseContractList',
      component: () => import('@/views/leasing/LeaseContractList.vue'),
      meta: { title: 'Lease Contracts' }
    }
  ]
}
```

**Step 2: Commit**
```bash
git add frontend/src/router/index.js
git commit -m "feat(leasing): Add leasing routes to router"
```

---

### Task 16: Run Full Test Suite

**Step 1: Run all leasing tests**
```bash
pytest backend/apps/leasing/tests/ -v --tb=short
```

**Step 2: Verify all tests pass**
Expected: All tests pass

**Step 3: Run full backend test suite**
```bash
pytest backend/apps/ -v --tb=short
```

**Step 4: Check test coverage**
```bash
pytest backend/apps/leasing/ --cov=apps.leasing --cov-report=term
```

---

### Task 17: Verify End-to-End

**Step 1: Start backend server**
```bash
python manage.py runserver
```

**Step 2: Test API endpoints**
```bash
# List contracts
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/lease-contracts/

# Create contract
curl -X POST -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"lessee_name":"Test Company","start_date":"2026-01-01","end_date":"2026-12-31","total_rent":12000}' \
  http://localhost:8000/api/lease-contracts/

# Activate contract
curl -X POST -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/lease-contracts/{id}/activate/
```

**Step 3: Verify frontend**
```bash
npm run dev
```
Navigate to `http://localhost:5173/leasing` and verify:
- List page loads
- Create button works
- Status filters work

**Step 4: Final commit**
```bash
git add -A
git commit -m "feat(leasing): Complete leasing management module implementation"
```

---

## Summary

### Files Created (21 files)
1. `backend/apps/leasing/__init__.py`
2. `backend/apps/leasing/models.py` (5 models)
3. `backend/apps/leasing/serializers.py` (5 serializers)
4. `backend/apps/leasing/filters.py` (3 filters)
5. `backend/apps/leasing/viewsets.py` (5 viewsets)
6. `backend/apps/leasing/urls.py`
7. `backend/apps/leasing/admin.py`
8. `backend/apps/leasing/tests/__init__.py`
9. `backend/apps/leasing/tests/test_models.py`
10. `backend/apps/leasing/tests/test_serializers.py`
11. `backend/apps/leasing/tests/test_filters.py`
12. `backend/apps/leasing/tests/test_api.py`
13. `frontend/src/api/leasing.js`
14. `frontend/src/views/leasing/LeaseContractList.vue`
15. `backend/apps/leasing/migrations/0001_initial.py`

### Files Modified (2 files)
1. `backend/config/urls.py` (include leasing URLs)
2. `frontend/src/router/index.js` (add leasing routes)

### Total Estimated Time: 5-6 hours

---

## Next Steps

After completing this implementation:
1. Create comprehensive E2E tests
2. Add reporting/analytics features
3. Implement notification system for expiring contracts
4. Add document upload for contracts
