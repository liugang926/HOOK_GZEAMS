# Insurance Management Implementation Plan

> Implementation plan for Asset Insurance Management module following TDD approach

## Document Information
| Field | Value |
|-------|-------|
| **Module** | Insurance Management |
| **PRD Reference** | `docs/plans/insurance_management/INSURANCE_MANAGEMENT_PRD.md` |
| **Created** | 2026-01-21 |
| **Estimated Time** | 4-5 hours |

---

## Goal

Implement a complete asset insurance management system with:
- Insurance company catalog management
- Insurance policy management with expiry tracking
- Asset-to-policy mapping with insured amounts
- Premium payment tracking
- Claims management and approval workflow
- Policy renewal tracking
- Organization-based data isolation
- Soft delete support

---

## Architecture

```
backend/apps/insurance/
├── __init__.py
├── models.py              # 6 Models: InsuranceCompany, InsurancePolicy, InsuredAsset, PremiumPayment, ClaimRecord, PolicyRenewal
├── serializers.py         # 6 Serializers inheriting BaseModelSerializer
├── viewsets.py            # 3 ViewSets inheriting BaseModelViewSetWithBatch
├── filters.py             # 3 FilterSets inheriting BaseModelFilter
├── urls.py                # URL routing
├── admin.py               # Django admin configuration
└── tests/
    ├── __init__.py
    └── test_api.py        # API tests

frontend/src/
├── api/insurance.js       # API client
└── views/insurance/
    └── InsurancePolicyList.vue  # Policy list page
```

---

## Tech Stack

- **Backend**: Django 5.0, DRF, PostgreSQL (JSONB)
- **Frontend**: Vue 3 (Composition API), Element Plus
- **Base Classes**: BaseModel, BaseModelSerializer, BaseModelViewSetWithBatch, BaseModelFilter

---

## Pre-Implementation Checklist

- [ ] Read PRD: `docs/plans/insurance_management/INSURANCE_MANAGEMENT_PRD.md`
- [ ] Verify BaseModel exists at `apps/common/models.py`
- [ ] Verify BaseModelSerializer exists at `apps/common/serializers/base.py`
- [ ] Verify BaseModelViewSetWithBatch exists at `apps/common/viewsets/base.py`
- [ ] Verify BaseModelFilter exists at `apps/common/filters/base.py`
- [ ] Create feature branch: `git checkout -b feature/insurance-management`

---

## Implementation Tasks (TDD Approach)

### Task 1: Create insurance module structure

**Files:**
- Create: `backend/apps/insurance/__init__.py`
- Create: `backend/apps/insurance/tests/__init__.py`

**Step 1: Create the module directory structure**
```bash
mkdir -p backend/apps/insurance/tests
```

**Step 2: Create __init__.py files**
```bash
# backend/apps/insurance/__init__.py
touch backend/apps/insurance/__init__.py
echo """Insurance management module.""" > backend/apps/insurance/__init__.py

# backend/apps/insurance/tests/__init__.py
touch backend/apps/insurance/tests/__init__.py
```

**Step 3: Verify structure**
```bash
ls -la backend/apps/insurance/
```

---

### Task 2: Implement InsuranceCompany Model

**Files:**
- Create: `backend/apps/insurance/models.py` (InsuranceCompany class)
- Test: `backend/apps/insurance/tests/test_models.py`

**Step 1: Write the failing test**

```python
# backend/apps/insurance/tests/test_models.py
"""Tests for Insurance models."""
import uuid
from django.test import TestCase
from apps.insurance.models import InsuranceCompany
from apps.organizations.models import Organization
from apps.accounts.models import User


class InsuranceCompanyModelTest(TestCase):
    """InsuranceCompany Model Tests."""

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

    def test_company_creation(self):
        """Test insurance company creation."""
        company = InsuranceCompany.objects.create(
            organization=self.organization,
            code=f"PICC_{self.unique_suffix}",
            name=f"People Insurance Co {self.unique_suffix}",
            contact_person="John Doe",
            contact_phone="1234567890",
            created_by=self.user
        )
        self.assertEqual(company.code, f"PICC_{self.unique_suffix}")
        self.assertTrue(company.is_active)

    def test_company_str(self):
        """Test company string representation."""
        company = InsuranceCompany.objects.create(
            organization=self.organization,
            code=f"PICC_{self.unique_suffix}",
            name=f"People Insurance Co {self.unique_suffix}",
            short_name="PICC",
            created_by=self.user
        )
        str_repr = str(company)
        self.assertIn("PICC", str_repr)
```

**Step 2: Run test to verify it fails**
```bash
pytest backend/apps/insurance/tests/test_models.py::InsuranceCompanyModelTest -v
```
Expected: `ImportError: cannot import name 'InsuranceCompany'`

**Step 3: Write minimal implementation**

```python
# backend/apps/insurance/models.py
"""Insurance management models."""

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from apps.common.models import BaseModel


class InsuranceCompany(BaseModel):
    """
    Insurance Company Model

    Maintains catalog of insurance companies for reference.
    """

    class Meta:
        db_table = 'insurance_companies'
        verbose_name = 'Insurance Company'
        verbose_name_plural = 'Insurance Companies'
        ordering = ['name']
        indexes = [
            models.Index(fields=['organization', 'code']),
        ]

    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Company code'
    )
    name = models.CharField(
        max_length=200,
        help_text='Insurance company name'
    )
    short_name = models.CharField(
        max_length=50,
        blank=True,
        help_text='Short name/abbreviation'
    )
    company_type = models.CharField(
        max_length=50,
        blank=True,
        help_text='Company type (property, casualty, life, etc.)'
    )

    # Contact Information
    contact_person = models.CharField(
        max_length=100,
        blank=True,
        help_text='Primary contact person'
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Contact phone'
    )
    contact_email = models.EmailField(
        blank=True,
        help_text='Contact email'
    )
    website = models.URLField(
        blank=True,
        help_text='Company website'
    )
    address = models.TextField(
        blank=True,
        help_text='Company address'
    )

    # Service
    claims_phone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Claims reporting hotline'
    )
    claims_email = models.EmailField(
        blank=True,
        help_text='Claims email'
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text='Additional notes'
    )

    is_active = models.BooleanField(
        default=True,
        help_text='Whether this company is actively used'
    )

    def __str__(self):
        return f"{self.name} ({self.short_name or self.code})"
```

**Step 4: Run test to verify it passes**
```bash
pytest backend/apps/insurance/tests/test_models.py::InsuranceCompanyModelTest -v
```
Expected: All tests pass

**Step 5: Commit**
```bash
git add backend/apps/insurance/models.py backend/apps/insurance/tests/test_models.py
git commit -m "feat(insurance): Add InsuranceCompany model"
```

---

### Task 3: Implement InsurancePolicy Model

**Files:**
- Modify: `backend/apps/insurance/models.py` (add InsurancePolicy)
- Test: `backend/apps/insurance/tests/test_models.py` (add tests)

**Step 1: Write the failing test**

```python
# Add to backend/apps/insurance/tests/test_models.py

class InsurancePolicyModelTest(TestCase):
    """InsurancePolicy Model Tests."""

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
        self.company = InsuranceCompany.objects.create(
            organization=self.organization,
            code=f"PICC_{self.unique_suffix}",
            name=f"People Insurance Co {self.unique_suffix}",
            created_by=self.user
        )

    def test_policy_creation(self):
        """Test insurance policy creation."""
        from apps.insurance.models import InsurancePolicy

        policy = InsurancePolicy.objects.create(
            organization=self.organization,
            policy_no=f"POL-{self.unique_suffix}",
            company=self.company,
            insurance_type="property",
            start_date="2026-01-01",
            end_date="2026-12-31",
            total_insured_amount=1000000,
            total_premium=5000,
            created_by=self.user
        )
        self.assertEqual(policy.policy_no, f"POL-{self.unique_suffix}")
        self.assertTrue(policy.is_active)

    def test_days_until_expiry(self):
        """Test days_until_expiry property."""
        from apps.insurance.models import InsurancePolicy
        from django.utils import timezone

        future_date = timezone.now().date() + timezone.timedelta(days=30)
        policy = InsurancePolicy.objects.create(
            organization=self.organization,
            policy_no=f"POL2-{self.unique_suffix}",
            company=self.company,
            insurance_type="equipment",
            start_date="2026-01-01",
            end_date=future_date,
            total_premium=3000,
            created_by=self.user
        )
        self.assertEqual(policy.days_until_expiry, 30)

    def test_is_expiring_soon(self):
        """Test is_expiring_soon property."""
        from apps.insurance.models import InsurancePolicy
        from django.utils import timezone

        near_date = timezone.now().date() + timezone.timedelta(days=15)
        policy = InsurancePolicy.objects.create(
            organization=self.organization,
            policy_no=f"POL3-{self.unique_suffix}",
            company=self.company,
            insurance_type="vehicle",
            start_date="2026-01-01",
            end_date=near_date,
            total_premium=2000,
            created_by=self.user
        )
        self.assertTrue(policy.is_expiring_soon)
```

**Step 2: Run test to verify it fails**
```bash
pytest backend/apps/insurance/tests/test_models.py::InsurancePolicyModelTest -v
```
Expected: `ImportError: cannot import name 'InsurancePolicy'`

**Step 3: Write minimal implementation**

```python
# Add to backend/apps/insurance/models.py

class InsurancePolicy(BaseModel):
    """
    Insurance Policy Model

    Manages insurance policies/policies for assets.
    """

    class Meta:
        db_table = 'insurance_policies'
        verbose_name = 'Insurance Policy'
        verbose_name_plural = 'Insurance Policies'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'policy_no']),
            models.Index(fields=['organization', 'company']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'start_date', 'end_date']),
        ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('terminated', 'Terminated'),
        ('renewed', 'Renewed'),
    ]

    PAYMENT_FREQUENCY_CHOICES = [
        ('one_time', 'One Time'),
        ('annual', 'Annual'),
        ('semi_annual', 'Semi-Annual'),
        ('quarterly', 'Quarterly'),
        ('monthly', 'Monthly'),
    ]

    # Policy Information
    policy_no = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text='Policy number from insurer'
    )
    policy_name = models.CharField(
        max_length=200,
        blank=True,
        help_text='Policy name/alias'
    )

    company = models.ForeignKey(
        InsuranceCompany,
        on_delete=models.PROTECT,
        related_name='policies',
        help_text='Insurance company'
    )

    # Insurance Type
    insurance_type = models.CharField(
        max_length=50,
        help_text='Type of insurance (property, equipment, vehicle, etc.)'
    )
    coverage_type = models.CharField(
        max_length=100,
        blank=True,
        help_text='Coverage type (all-risk, named-peril, etc.)'
    )

    # Period
    start_date = models.DateField(help_text='Policy start date')
    end_date = models.DateField(help_text='Policy end date')
    renewal_date = models.DateField(
        null=True,
        blank=True,
        help_text='Next renewal date'
    )

    # Financial
    total_insured_amount = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Total insured amount'
    )
    total_premium = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Total premium amount'
    )
    payment_frequency = models.CharField(
        max_length=50,
        choices=PAYMENT_FREQUENCY_CHOICES,
        default='annual',
        help_text='Payment frequency'
    )

    # Deductible
    deductible_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text='Deductible amount per claim'
    )
    deductible_type = models.CharField(
        max_length=50,
        blank=True,
        help_text='Deductible type (fixed, percentage, per-claim)'
    )

    # Status
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='draft',
        help_text='Policy status'
    )

    # Documents
    policy_document = models.FileField(
        upload_to='insurance/policies/%Y/%m/',
        null=True,
        blank=True,
        help_text='Policy document PDF'
    )

    # Notes
    coverage_description = models.TextField(
        blank=True,
        help_text='Description of coverage'
    )
    exclusion_clause = models.TextField(
        blank=True,
        help_text='Exclusion clauses'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes'
    )

    def __str__(self):
        return f"{self.policy_no} - {self.company.name}"

    @property
    def is_active(self):
        """Check if policy is currently active."""
        today = timezone.now().date()
        return (self.status == 'active' and
                self.start_date <= today <= self.end_date)

    @property
    def days_until_expiry(self):
        """Get days until policy expires."""
        today = timezone.now().date()
        if self.end_date:
            delta = self.end_date - today
            return delta.days
        return None

    @property
    def is_expiring_soon(self):
        """Check if policy expires within 30 days."""
        days = self.days_until_expiry
        return days is not None and 0 <= days <= 30

    @property
    def unpaid_premium(self):
        """Get total unpaid premium amount."""
        from django.db.models import Sum
        return self.payments.filter(
            status__in=['pending', 'partial']
        ).aggregate(
            unpaid=Sum(models.F('amount') - models.F('paid_amount'))
        )['unpaid'] or 0
```

**Step 4: Run test to verify it passes**
```bash
pytest backend/apps/insurance/tests/test_models.py::InsurancePolicyModelTest -v
```
Expected: All tests pass

**Step 5: Commit**
```bash
git add backend/apps/insurance/models.py backend/apps/insurance/tests/test_models.py
git commit -m "feat(insurance): Add InsurancePolicy model with expiry tracking"
```

---

### Task 4: Implement InsuredAsset, PremiumPayment, ClaimRecord Models

**Files:**
- Modify: `backend/apps/insurance/models.py` (add 3 models)
- Test: `backend/apps/insurance/tests/test_models.py` (add tests)

**Step 1: Write the failing test**

```python
# Add to backend/apps/insurance/tests/test_models.py

class InsuredAssetModelTest(TestCase):
    """InsuredAsset Model Tests."""

    def setUp(self):
        """Set up test data with unique codes."""
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.organization = Organization.objects.create(
            name=f"Test Org {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_{self.unique_suffix}",
            organization=self.organization
        )
        self.company = InsuranceCompany.objects.create(
            organization=self.organization,
            code=f"PICC_{self.unique_suffix}",
            name=f"Insurance Co {self.unique_suffix}",
            created_by=self.user
        )
        from apps.insurance.models import InsurancePolicy
        self.policy = InsurancePolicy.objects.create(
            organization=self.organization,
            policy_no=f"POL-{self.unique_suffix}",
            company=self.company,
            insurance_type="property",
            start_date="2026-01-01",
            end_date="2026-12-31",
            total_premium=5000,
            created_by=self.user
        )
        # Create asset
        from apps.assets.models import Asset, AssetCategory, Location
        self.category = AssetCategory.objects.create(
            name=f"Category {self.unique_suffix}",
            code=f"CAT_{self.unique_suffix}",
            organization=self.organization
        )
        self.location = Location.objects.create(
            name=f"Location {self.unique_suffix}",
            path=f"Location {self.unique_suffix}",
            organization=self.organization
        )
        self.asset = Asset.objects.create(
            asset_code=f"ASSET_{self.unique_suffix}",
            asset_name=f"Test Asset {self.unique_suffix}",
            asset_category=self.category,
            location=self.location,
            purchase_price=10000,
            purchase_date="2026-01-01",
            organization=self.organization,
            created_by=self.user
        )

    def test_insured_asset_creation(self):
        """Test insured asset creation."""
        from apps.insurance.models import InsuredAsset

        insured = InsuredAsset.objects.create(
            organization=self.organization,
            policy=self.policy,
            asset=self.asset,
            insured_amount=50000,
            premium_amount=250,
            created_by=self.user
        )
        self.assertEqual(insured.insured_amount, 50000)


class PremiumPaymentModelTest(TestCase):
    """PremiumPayment Model Tests."""

    def setUp(self):
        """Set up test data."""
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.organization = Organization.objects.create(
            name=f"Test Org {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_{self.unique_suffix}",
            organization=self.organization
        )
        self.company = InsuranceCompany.objects.create(
            organization=self.organization,
            code=f"PICC_{self.unique_suffix}",
            name=f"Insurance Co {self.unique_suffix}",
            created_by=self.user
        )
        from apps.insurance.models import InsurancePolicy
        self.policy = InsurancePolicy.objects.create(
            organization=self.organization,
            policy_no=f"POL-{self.unique_suffix}",
            company=self.company,
            insurance_type="property",
            start_date="2026-01-01",
            end_date="2026-12-31",
            total_premium=5000,
            created_by=self.user
        )

    def test_outstanding_amount(self):
        """Test outstanding_amount property."""
        from apps.insurance.models import PremiumPayment

        payment = PremiumPayment.objects.create(
            organization=self.organization,
            policy=self.policy,
            payment_no=f"PAY-{self.unique_suffix}",
            due_date="2026-01-31",
            amount=1000,
            paid_amount=300,
            status="partial",
            created_by=self.user
        )
        self.assertEqual(payment.outstanding_amount, 700)


class ClaimRecordModelTest(TestCase):
    """ClaimRecord Model Tests."""

    def setUp(self):
        """Set up test data."""
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.organization = Organization.objects.create(
            name=f"Test Org {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_{self.unique_suffix}",
            organization=self.organization
        )
        self.company = InsuranceCompany.objects.create(
            organization=self.organization,
            code=f"PICC_{self.unique_suffix}",
            name=f"Insurance Co {self.unique_suffix}",
            created_by=self.user
        )
        from apps.insurance.models import InsurancePolicy
        self.policy = InsurancePolicy.objects.create(
            organization=self.organization,
            policy_no=f"POL-{self.unique_suffix}",
            company=self.company,
            insurance_type="property",
            start_date="2026-01-01",
            end_date="2026-12-31",
            total_premium=5000,
            created_by=self.user
        )

    def test_payout_ratio(self):
        """Test payout_ratio property."""
        from apps.insurance.models import ClaimRecord

        claim = ClaimRecord.objects.create(
            organization=self.organization,
            policy=self.policy,
            incident_date="2026-06-15",
            incident_type="damage",
            incident_description="Test damage",
            claimed_amount=10000,
            approved_amount=8000,
            paid_amount=8000,
            created_by=self.user
        )
        self.assertEqual(claim.payout_ratio, 80.0)
```

**Step 2: Run test to verify it fails**
```bash
pytest backend/apps/insurance/tests/test_models.py -v -k "InsuredAsset or PremiumPayment or ClaimRecord"
```
Expected: `ImportError: cannot import name`

**Step 3: Write minimal implementation**

```python
# Add to backend/apps/insurance/models.py

class InsuredAsset(BaseModel):
    """
    Insured Asset Model

    Links assets to insurance policies with coverage details.
    """

    class Meta:
        db_table = 'insured_assets'
        verbose_name = 'Insured Asset'
        verbose_name_plural = 'Insured Assets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'policy']),
            models.Index(fields=['organization', 'asset']),
            models.Index(fields=['organization', 'policy', 'asset']),
        ]
        unique_together = [['organization', 'policy', 'asset']]

    policy = models.ForeignKey(
        InsurancePolicy,
        on_delete=models.CASCADE,
        related_name='insured_assets',
        help_text='Parent insurance policy'
    )
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.CASCADE,
        related_name='insurance_coverages',
        help_text='Insured asset'
    )

    # Coverage Details
    insured_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Insured amount for this asset'
    )
    premium_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
        help_text='Premium allocation for this asset'
    )

    # Location/Usage
    asset_location = models.CharField(
        max_length=200,
        blank=True,
        help_text='Asset location at policy time'
    )
    asset_usage = models.CharField(
        max_length=100,
        blank=True,
        help_text='Asset usage type'
    )

    # Valuation
    valuation_method = models.CharField(
        max_length=50,
        blank=True,
        help_text='Valuation method (replacement, actual cash value)'
    )
    valuation_date = models.DateField(
        null=True,
        blank=True,
        help_text='Valuation date'
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text='Coverage notes'
    )

    def __str__(self):
        return f"{self.asset.asset_name} - {self.policy.policy_no}"


class PremiumPayment(BaseModel):
    """
    Premium Payment Model

    Tracks premium payment schedule and actual payments.
    """

    class Meta:
        db_table = 'premium_payments'
        verbose_name = 'Premium Payment'
        verbose_name_plural = 'Premium Payments'
        ordering = ['due_date']
        indexes = [
            models.Index(fields=['organization', 'policy']),
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

    policy = models.ForeignKey(
        InsurancePolicy,
        on_delete=models.CASCADE,
        related_name='payments',
        help_text='Related insurance policy'
    )

    # Payment Details
    payment_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Payment reference number'
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
        help_text='Date payment was made'
    )
    payment_method = models.CharField(
        max_length=50,
        blank=True,
        help_text='Payment method'
    )
    payment_reference = models.CharField(
        max_length=200,
        blank=True,
        help_text='Payment reference/receipt number'
    )
    invoice_no = models.CharField(
        max_length=100,
        blank=True,
        help_text='Invoice number from insurer'
    )

    # Receipt
    receipt_document = models.FileField(
        upload_to='insurance/receipts/%Y/%m/',
        null=True,
        blank=True,
        help_text='Payment receipt document'
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text='Payment notes'
    )

    def __str__(self):
        return f"{self.payment_no} - {self.policy.policy_no}"

    @property
    def outstanding_amount(self):
        """Get outstanding amount."""
        return float(self.amount) - float(self.paid_amount)

    @property
    def is_overdue(self):
        """Check if payment is overdue."""
        return (self.status in ['pending', 'partial'] and
                self.due_date < timezone.now().date())


class ClaimRecord(BaseModel):
    """
    Insurance Claim Model

    Records insurance claims and their resolution.
    """

    class Meta:
        db_table = 'claim_records'
        verbose_name = 'Claim Record'
        verbose_name_plural = 'Claim Records'
        ordering = ['-incident_date', '-created_at']
        indexes = [
            models.Index(fields=['organization', 'policy']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'incident_date']),
        ]

    STATUS_CHOICES = [
        ('reported', 'Reported'),
        ('investigating', 'Investigating'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
        ('closed', 'Closed'),
    ]

    TYPE_CHOICES = [
        ('damage', 'Damage'),
        ('loss', 'Loss'),
        ('theft', 'Theft'),
        ('liability', 'Liability'),
        ('other', 'Other'),
    ]

    policy = models.ForeignKey(
        InsurancePolicy,
        on_delete=models.CASCADE,
        related_name='claims',
        help_text='Related insurance policy'
    )
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='insurance_claims',
        help_text='Affected asset (if applicable)'
    )

    # Claim Information
    claim_no = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text='Claim number assigned by insurer'
    )

    # Incident Details
    incident_date = models.DateField(
        db_index=True,
        help_text='Date of incident'
    )
    incident_type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        help_text='Type of incident'
    )
    incident_description = models.TextField(
        help_text='Description of the incident'
    )
    incident_location = models.CharField(
        max_length=200,
        blank=True,
        help_text='Location of incident'
    )

    # Claim Details
    claim_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date claim was filed'
    )
    claimed_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Amount claimed'
    )

    # Resolution
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='reported',
        help_text='Claim status'
    )
    approved_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Amount approved by insurer'
    )
    paid_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text='Amount actually paid'
    )
    paid_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date payment was received'
    )

    # Adjuster
    adjuster_name = models.CharField(
        max_length=100,
        blank=True,
        help_text='Insurance adjuster name'
    )
    adjuster_contact = models.CharField(
        max_length=100,
        blank=True,
        help_text='Adjuster contact information'
    )

    # Documents
    photos = models.JSONField(
        default=list,
        blank=True,
        help_text='Photos of damage/loss'
    )
    supporting_documents = models.JSONField(
        default=list,
        blank=True,
        help_text='Supporting documents'
    )

    # Settlement
    settlement_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date claim was settled'
    )
    settlement_notes = models.TextField(
        blank=True,
        help_text='Settlement notes and details'
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text='Additional notes'
    )

    def __str__(self):
        return f"Claim {self.claim_no or 'Pending'} - {self.incident_type}"

    @property
    def payout_ratio(self):
        """Calculate payout ratio (approved/claimed)."""
        if self.claimed_amount and self.claimed_amount > 0:
            if self.approved_amount:
                return (float(self.approved_amount) / float(self.claimed_amount)) * 100
            elif self.paid_amount:
                return (float(self.paid_amount) / float(self.claimed_amount)) * 100
        return 0


class PolicyRenewal(BaseModel):
    """
    Policy Renewal Model

    Records policy renewals and history.
    """

    class Meta:
        db_table = 'policy_renewals'
        verbose_name = 'Policy Renewal'
        verbose_name_plural = 'Policy Renewals'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'original_policy']),
            models.Index(fields=['organization', 'renewed_policy']),
        ]

    original_policy = models.ForeignKey(
        InsurancePolicy,
        on_delete=models.CASCADE,
        related_name='renewals_from',
        help_text='Original policy being renewed'
    )
    renewed_policy = models.ForeignKey(
        InsurancePolicy,
        on_delete=models.CASCADE,
        related_name='renewals_to',
        help_text='New renewed policy'
    )

    # Renewal Details
    renewal_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Renewal reference number'
    )
    original_end_date = models.DateField(help_text='Original policy end date')
    new_start_date = models.DateField(help_text='New policy start date')
    new_end_date = models.DateField(help_text='New policy end date')

    # Premium Comparison
    original_premium = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text='Original annual premium'
    )
    new_premium = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text='New annual premium'
    )

    # Change Summary
    coverage_changes = models.TextField(
        blank=True,
        help_text='Summary of coverage changes'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes'
    )

    def __str__(self):
        return f"Renewal {self.renewal_no}"

    @property
    def premium_change(self):
        """Calculate premium change amount."""
        return float(self.new_premium) - float(self.original_premium)

    @property
    def premium_change_percent(self):
        """Calculate premium change percentage."""
        if self.original_premium and self.original_premium > 0:
            return ((float(self.new_premium) - float(self.original_premium)) /
                    float(self.original_premium)) * 100
        return 0
```

**Step 4: Run test to verify it passes**
```bash
pytest backend/apps/insurance/tests/test_models.py -v -k "InsuredAsset or PremiumPayment or ClaimRecord"
```
Expected: All tests pass

**Step 5: Commit**
```bash
git add backend/apps/insurance/models.py backend/apps/insurance/tests/test_models.py
git commit -m "feat(insurance): Add InsuredAsset, PremiumPayment, ClaimRecord, PolicyRenewal models"
```

---

### Task 5: Create Serializers

**Files:**
- Create: `backend/apps/insurance/serializers.py`
- Test: `backend/apps/insurance/tests/test_serializers.py`

**Step 1: Write the failing test**

```python
# backend/apps/insurance/tests/test_serializers.py
"""Tests for Insurance serializers."""
import uuid
from django.test import TestCase
from apps.insurance.serializers import InsurancePolicySerializer, ClaimRecordSerializer
from apps.insurance.models import InsurancePolicy, InsuranceCompany
from apps.organizations.models import Organization
from apps.accounts.models import User


class InsurancePolicySerializerTest(TestCase):
    """InsurancePolicy Serializer Tests."""

    def setUp(self):
        """Set up test data."""
        self.unique_suffix = uuid.uuid4().hex[:8]
        self.organization = Organization.objects.create(
            name=f"Test Org {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_{self.unique_suffix}",
            organization=self.organization
        )
        self.company = InsuranceCompany.objects.create(
            organization=self.organization,
            code=f"PICC_{self.unique_suffix}",
            name=f"Insurance Co {self.unique_suffix}",
            created_by=self.user
        )

    def test_serializer_creates_policy(self):
        """Test serializer creates policy successfully."""
        data = {
            'policy_no': f'POL-{self.unique_suffix}',
            'company': self.company.id,
            'insurance_type': 'property',
            'start_date': '2026-01-01',
            'end_date': '2026-12-31',
            'total_insured_amount': 1000000,
            'total_premium': 5000
        }
        serializer = InsurancePolicySerializer(data=data)
        self.assertTrue(serializer.is_valid())
        policy = serializer.save(
            organization=self.organization,
            created_by=self.user
        )
        self.assertEqual(policy.insurance_type, 'property')
```

**Step 2: Run test to verify it fails**
```bash
pytest backend/apps/insurance/tests/test_serializers.py -v
```
Expected: `ImportError: cannot import name 'InsurancePolicySerializer'`

**Step 3: Write minimal implementation**

```python
# backend/apps/insurance/serializers.py
"""Insurance management serializers."""

from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer
from .models import (
    InsuranceCompany, InsurancePolicy, InsuredAsset,
    PremiumPayment, ClaimRecord, PolicyRenewal
)


class InsuranceCompanySerializer(BaseModelSerializer):
    """Insurance Company Serializer."""

    class Meta(BaseModelSerializer.Meta):
        model = InsuranceCompany
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'short_name', 'company_type',
            'contact_person', 'contact_phone', 'contact_email', 'website', 'address',
            'claims_phone', 'claims_email',
            'notes', 'is_active',
        ]


class InsuredAssetSerializer(BaseModelSerializer):
    """Insured Asset Serializer."""
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = InsuredAsset
        fields = BaseModelSerializer.Meta.fields + [
            'policy', 'asset', 'asset_name', 'asset_code',
            'insured_amount', 'premium_amount',
            'asset_location', 'asset_usage',
            'valuation_method', 'valuation_date',
            'notes',
        ]


class PremiumPaymentSerializer(BaseModelSerializer):
    """Premium Payment Serializer."""
    policy_no = serializers.CharField(source='policy.policy_no', read_only=True)
    company_name = serializers.CharField(source='policy.company.name', read_only=True)
    outstanding_amount = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()

    class Meta(BaseModelSerializer.Meta):
        model = PremiumPayment
        fields = BaseModelSerializer.Meta.fields + [
            'policy', 'policy_no', 'company_name',
            'payment_no', 'due_date', 'amount', 'paid_amount',
            'outstanding_amount', 'is_overdue',
            'status', 'paid_date', 'payment_method', 'payment_reference',
            'invoice_no', 'receipt_document', 'notes',
        ]


class InsurancePolicySerializer(BaseModelSerializer):
    """Insurance Policy Serializer."""
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_short_name = serializers.CharField(source='company.short_name', read_only=True)
    insured_assets = InsuredAssetSerializer(many=True, read_only=True)
    payments = PremiumPaymentSerializer(many=True, read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True)
    is_expiring_soon = serializers.BooleanField(read_only=True)
    unpaid_premium = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    # Statistics
    total_insured_assets = serializers.IntegerField(read_only=True)
    total_claims = serializers.IntegerField(read_only=True)
    total_claim_amount = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = InsurancePolicy
        fields = BaseModelSerializer.Meta.fields + [
            # Policy
            'policy_no', 'policy_name', 'company', 'company_name', 'company_short_name',
            # Type
            'insurance_type', 'coverage_type',
            # Period
            'start_date', 'end_date', 'renewal_date',
            # Financial
            'total_insured_amount', 'total_premium', 'payment_frequency',
            'deductible_amount', 'deductible_type',
            # Status
            'status', 'is_active', 'days_until_expiry', 'is_expiring_soon',
            # Relations & Stats
            'insured_assets', 'payments', 'unpaid_premium',
            'total_insured_assets', 'total_claims', 'total_claim_amount',
            # Documents
            'policy_document',
            # Terms
            'coverage_description', 'exclusion_clause', 'notes',
        ]


class ClaimRecordSerializer(BaseModelSerializer):
    """Claim Record Serializer."""
    policy_no = serializers.CharField(source='policy.policy_no', read_only=True)
    company_name = serializers.CharField(source='policy.company.name', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    payout_ratio = serializers.FloatField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = ClaimRecord
        fields = BaseModelSerializer.Meta.fields + [
            'policy', 'policy_no', 'company_name',
            'asset', 'asset_name', 'asset_code',
            'claim_no', 'incident_date', 'incident_type', 'incident_description',
            'incident_location', 'claim_date', 'claimed_amount',
            'status', 'approved_amount', 'paid_amount', 'paid_date', 'payout_ratio',
            'adjuster_name', 'adjuster_contact',
            'photos', 'supporting_documents',
            'settlement_date', 'settlement_notes',
            'notes',
        ]


class PolicyRenewalSerializer(BaseModelSerializer):
    """Policy Renewal Serializer."""
    original_policy_no = serializers.CharField(source='original_policy.policy_no', read_only=True)
    renewed_policy_no = serializers.CharField(source='renewed_policy.policy_no', read_only=True)
    premium_change = serializers.ReadOnlyField()
    premium_change_percent = serializers.FloatField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = PolicyRenewal
        fields = BaseModelSerializer.Meta.fields + [
            'original_policy', 'original_policy_no',
            'renewed_policy', 'renewed_policy_no',
            'renewal_no', 'original_end_date', 'new_start_date', 'new_end_date',
            'original_premium', 'new_premium', 'premium_change', 'premium_change_percent',
            'coverage_changes', 'notes',
        ]
```

**Step 4: Run test to verify it passes**
```bash
pytest backend/apps/insurance/tests/test_serializers.py -v
```
Expected: All tests pass

**Step 5: Commit**
```bash
git add backend/apps/insurance/serializers.py backend/apps/insurance/tests/test_serializers.py
git commit -m "feat(insurance): Add serializers for all insurance models"
```

---

### Task 6: Create Filters and ViewSets

**Files:**
- Create: `backend/apps/insurance/filters.py`
- Create: `backend/apps/insurance/viewsets.py`
- Test: `backend/apps/insurance/tests/test_api.py`

**Step 1: Write the failing test**

```python
# backend/apps/insurance/tests/test_api.py
"""Tests for Insurance API endpoints."""
import uuid
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from apps.insurance.models import InsurancePolicy, InsuranceCompany
from apps.organizations.models import Organization
from apps.accounts.models import User


class InsurancePolicyAPITest(APITestCase):
    """InsurancePolicy API Tests."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.unique_suffix = uuid.uuid4().hex[:8]

        self.organization = Organization.objects.create(
            name=f"Test Org {self.unique_suffix}",
            code=f"TESTORG_{self.unique_suffix}"
        )
        self.user = User.objects.create_user(
            username=f"testuser_{self.unique_suffix}",
            email=f"test{self.unique_suffix}@example.com",
            organization=self.organization
        )
        self.client.force_authenticate(user=self.user)
        self.company = InsuranceCompany.objects.create(
            organization=self.organization,
            code=f"PICC_{self.unique_suffix}",
            name=f"Insurance Co {self.unique_suffix}",
            created_by=self.user
        )

    def test_list_policies(self):
        """Test listing insurance policies."""
        for i in range(3):
            InsurancePolicy.objects.create(
                organization=self.organization,
                policy_no=f"POL-{self.unique_suffix}-{i}",
                company=self.company,
                insurance_type="property",
                start_date="2026-01-01",
                end_date="2026-12-31",
                total_premium=5000 + i * 1000,
                created_by=self.user
            )

        url = '/api/insurance-policies/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['data']['count'], 3)

    def test_activate_policy(self):
        """Test activating a draft policy."""
        policy = InsurancePolicy.objects.create(
            organization=self.organization,
            policy_no=f"POL-ACT-{self.unique_suffix}",
            company=self.company,
            insurance_type="equipment",
            start_date="2026-01-01",
            end_date="2026-12-31",
            status="draft",
            total_premium=3000,
            created_by=self.user
        )

        url = f'/api/insurance-policies/{policy.id}/activate/'
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        policy.refresh_from_db()
        self.assertEqual(policy.status, 'active')
```

**Step 2: Run test to verify it fails**
```bash
pytest backend/apps/insurance/tests/test_api.py::InsurancePolicyAPITest -v
```
Expected: `404 Not Found` or route not registered

**Step 3: Write minimal implementation**

```python
# backend/apps/insurance/filters.py
"""Insurance management filters."""

from django_filters import rest_framework as filters
from apps.common.filters.base import BaseModelFilter
from .models import InsurancePolicy, PremiumPayment, ClaimRecord


class InsurancePolicyFilter(BaseModelFilter):
    """Insurance Policy Filter."""

    status = filters.CharFilter()
    insurance_type = filters.CharFilter()
    company = filters.UUIDFilter()
    expires_soon = filters.BooleanFilter(method='filter_expires_soon')

    def filter_expires_soon(self, queryset, name, value):
        """Filter policies expiring within 30 days."""
        if value:
            from django.utils import timezone
            delta = timezone.now().date() + timezone.timedelta(days=30)
            return queryset.filter(
                end_date__lte=delta,
                status='active'
            )
        return queryset

    class Meta(BaseModelFilter.Meta):
        model = InsurancePolicy
        fields = BaseModelFilter.Meta.fields + [
            'status', 'insurance_type', 'company', 'start_date', 'end_date',
        ]


class PremiumPaymentFilter(BaseModelFilter):
    """Premium Payment Filter."""

    status = filters.CharFilter()
    policy = filters.UUIDFilter()
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
        model = PremiumPayment
        fields = BaseModelFilter.Meta.fields + [
            'status', 'policy', 'due_date',
        ]


class ClaimRecordFilter(BaseModelFilter):
    """Claim Record Filter."""

    status = filters.CharFilter()
    policy = filters.UUIDFilter()
    incident_type = filters.CharFilter()
    incident_from = filters.DateFilter(field_name='incident_date', lookup_expr='gte')
    incident_to = filters.DateFilter(field_name='incident_date', lookup_expr='lte')

    class Meta(BaseModelFilter.Meta):
        model = ClaimRecord
        fields = BaseModelFilter.Meta.fields + [
            'status', 'policy', 'incident_type', 'incident_date',
        ]
```

```python
# backend/apps/insurance/viewsets.py
"""Insurance management viewsets."""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Sum, F
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.filters.base import BaseModelFilter
from .models import (
    InsuranceCompany, InsurancePolicy, InsuredAsset,
    PremiumPayment, ClaimRecord, PolicyRenewal
)
from .serializers import (
    InsuranceCompanySerializer, InsurancePolicySerializer, InsuredAssetSerializer,
    PremiumPaymentSerializer, ClaimRecordSerializer, PolicyRenewalSerializer
)
from .filters import InsurancePolicyFilter, PremiumPaymentFilter, ClaimRecordFilter


class InsuranceCompanyViewSet(BaseModelViewSetWithBatch):
    """Insurance Company ViewSet."""
    queryset = InsuranceCompany.objects.all()
    serializer_class = InsuranceCompanySerializer
    filterset_class = BaseModelFilter


class InsurancePolicyViewSet(BaseModelViewSetWithBatch):
    """Insurance Policy ViewSet."""
    queryset = InsurancePolicy.objects.all()
    serializer_class = InsurancePolicySerializer
    filterset_class = InsurancePolicyFilter

    def get_queryset(self):
        """Optimize queryset with annotations."""
        queryset = super().get_queryset()
        return queryset.annotate(
            total_insured_assets=Count('insured_assets'),
            total_claims=Count('claims'),
            total_claim_amount=Sum('claims__paid_amount')
        )

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a draft policy."""
        policy = self.get_object()

        if policy.status != 'draft':
            return Response(
                {'success': False, 'error': {'code': 'INVALID_STATUS'}},
                status=status.HTTP_400_BAD_REQUEST
            )

        policy.status = 'active'
        policy.save()

        # Generate payment schedule
        self._generate_payment_schedule(policy)

        serializer = self.get_serializer(policy)
        return Response({
            'success': True,
            'message': 'Policy activated',
            'data': serializer.data
        })

    def _generate_payment_schedule(self, policy):
        """Generate premium payment schedule."""
        if policy.payment_frequency == 'one_time':
            PremiumPayment.objects.create(
                organization_id=policy.organization_id,
                policy=policy,
                payment_no=f"PRE-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                due_date=policy.start_date,
                amount=policy.total_premium,
                created_by=policy.created_by
            )
            return

        intervals = {
            'monthly': timedelta(days=30),
            'quarterly': timedelta(days=90),
            'semi_annual': timedelta(days=180),
            'annual': timedelta(days=365),
        }

        interval = intervals.get(policy.payment_frequency, timedelta(days=365))
        payment_count = max(1, int((policy.end_date - policy.start_date).days / interval.days))
        payment_amount = policy.total_premium / payment_count

        current_date = policy.start_date
        for i in range(payment_count):
            PremiumPayment.objects.create(
                organization_id=policy.organization_id,
                policy=policy,
                payment_no=f"PRE-{timezone.now().strftime('%Y%m%d%H%M%S')}-{i}",
                due_date=current_date,
                amount=round(payment_amount, 2),
                created_by=policy.created_by
            )
            current_date += interval

    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get policies expiring within N days."""
        days = int(request.query_params.get('days', 30))
        delta = timezone.now().date() + timedelta(days=days)

        policies = self.queryset.filter(
            end_date__lte=delta,
            status='active'
        )

        page = self.paginate_queryset(policies)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        """Get insurance dashboard statistics."""
        org_id = request.user.organization_id

        # Policy stats
        total_policies = InsurancePolicy.objects.filter(
            organization_id=org_id
        ).count()
        active_policies = InsurancePolicy.objects.filter(
            organization_id=org_id,
            status='active'
        ).count()
        expiring_policies = InsurancePolicy.objects.filter(
            organization_id=org_id,
            status='active',
            end_date__lte=timezone.now().date() + timedelta(days=30)
        ).count()

        # Premium stats
        total_annual_premium = InsurancePolicy.objects.filter(
            organization_id=org_id,
            status='active'
        ).aggregate(total=Sum('total_premium'))['total'] or 0

        unpaid_premium = PremiumPayment.objects.filter(
            organization_id=org_id,
            status__in=['pending', 'partial']
        ).aggregate(
            unpaid=Sum(F('amount') - F('paid_amount'))
        )['unpaid'] or 0

        # Claim stats
        pending_claims = ClaimRecord.objects.filter(
            organization_id=org_id,
            status__in=['reported', 'investigating', 'approved']
        ).count()
        total_paid_claims = ClaimRecord.objects.filter(
            organization_id=org_id,
            status='paid'
        ).aggregate(total=Sum('paid_amount'))['total'] or 0

        return Response({
            'success': True,
            'data': {
                'policies': {
                    'total': total_policies,
                    'active': active_policies,
                    'expiring_soon': expiring_policies
                },
                'premium': {
                    'annual_total': float(total_annual_premium),
                    'unpaid': float(unpaid_premium)
                },
                'claims': {
                    'pending': pending_claims,
                    'total_paid': float(total_paid_claims)
                }
            }
        })


class InsuredAssetViewSet(BaseModelViewSetWithBatch):
    """Insured Asset ViewSet."""
    queryset = InsuredAsset.objects.all()
    serializer_class = InsuredAssetSerializer
    filterset_class = BaseModelFilter


class PremiumPaymentViewSet(BaseModelViewSetWithBatch):
    """Premium Payment ViewSet."""
    queryset = PremiumPayment.objects.all()
    serializer_class = PremiumPaymentSerializer
    filterset_class = PremiumPaymentFilter


class ClaimRecordViewSet(BaseModelViewSetWithBatch):
    """Claim Record ViewSet."""
    queryset = ClaimRecord.objects.all()
    serializer_class = ClaimRecordSerializer
    filterset_class = ClaimRecordFilter

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a claim with amount."""
        claim = self.get_object()

        if claim.status not in ['reported', 'investigating']:
            return Response(
                {'success': False, 'error': {'code': 'INVALID_STATUS'}},
                status=status.HTTP_400_BAD_REQUEST
            )

        claim.status = 'approved'
        claim.approved_amount = request.data.get('approved_amount', 0)
        claim.save()

        serializer = self.get_serializer(claim)
        return Response({
            'success': True,
            'message': 'Claim approved',
            'data': serializer.data
        })

    @action(detail=True, methods=['post'])
    def record_payment(self, request, pk=None):
        """Record claim payment."""
        claim = self.get_object()

        amount = request.data.get('amount', 0)
        claim.paid_amount += float(amount)
        claim.paid_date = timezone.now().date()

        if claim.paid_amount >= (claim.approved_amount or claim.claimed_amount):
            claim.status = 'paid'
            claim.settlement_date = timezone.now().date()

        claim.save()

        serializer = self.get_serializer(claim)
        return Response({
            'success': True,
            'message': 'Payment recorded',
            'data': serializer.data
        })


class PolicyRenewalViewSet(BaseModelViewSetWithBatch):
    """Policy Renewal ViewSet."""
    queryset = PolicyRenewal.objects.all()
    serializer_class = PolicyRenewalSerializer
    filterset_class = BaseModelFilter
```

**Step 4: Run test to verify it passes (after URL routing)**
```bash
pytest backend/apps/insurance/tests/test_api.py::InsurancePolicyAPITest -v
```
Expected: All tests pass (after URLs configured in Task 7)

**Step 5: Commit**
```bash
git add backend/apps/insurance/filters.py backend/apps/insurance/viewsets.py backend/apps/insurance/tests/test_api.py
git commit -m "feat(insurance): Add filters and ViewSets with activate, dashboard stats actions"
```

---

### Task 7: Configure URL Routing

**Files:**
- Create: `backend/apps/insurance/urls.py`
- Modify: `backend/config/urls.py` (include insurance URLs)

**Step 1: Create insurance URLs**

```python
# backend/apps/insurance/urls.py
"""Insurance management URL configuration."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import (
    InsuranceCompanyViewSet, InsurancePolicyViewSet,
    InsuredAssetViewSet, PremiumPaymentViewSet,
    ClaimRecordViewSet, PolicyRenewalViewSet
)

app_name = 'insurance'

router = DefaultRouter()
router.register(r'insurance-companies', InsuranceCompanyViewSet, basename='insurancecompany')
router.register(r'insurance-policies', InsurancePolicyViewSet, basename='insurancepolicy')
router.register(r'insured-assets', InsuredAssetViewSet, basename='insuredasset')
router.register(r'premium-payments', PremiumPaymentViewSet, basename='premiumpayment')
router.register(r'claim-records', ClaimRecordViewSet, basename='claimrecord')
router.register(r'policy-renewals', PolicyRenewalViewSet, basename='policyrenewal')

urlpatterns = [
    path('', include(router.urls)),
]
```

**Step 2: Include in main URL config**

```python
# Add to backend/config/urls.py

urlpatterns = [
    # ... existing patterns ...
    path('api/', include('apps.insurance.urls', namespace='insurance')),
]
```

**Step 3: Verify URLs**
```bash
python manage.py show_urls 2>&1 | grep insurance
```

**Step 4: Commit**
```bash
git add backend/apps/insurance/urls.py backend/config/urls.py
git commit -m "feat(insurance): Configure URL routing for all insurance endpoints"
```

---

### Task 8: Create Database Migration

**Files:**
- Create: `backend/apps/insurance/migrations/0001_initial.py`

**Step 1: Generate migration**
```bash
python manage.py makemigrations insurance
```

**Step 2: Review migration file**
```bash
cat backend/apps/insurance/migrations/0001_initial.py
```

**Step 3: Run migration**
```bash
python manage.py migrate insurance
```

**Step 4: Verify tables**
```bash
python manage.py dbshell
\dt | grep insurance
\q
```

**Step 5: Commit**
```bash
git add backend/apps/insurance/migrations/
git commit -m "feat(insurance): Add initial database migration"
```

---

### Task 9: Add to Django Admin

**Files:**
- Create: `backend/apps/insurance/admin.py`

**Step 1: Create admin configuration**

```python
# backend/apps/insurance/admin.py
"""Insurance management admin configuration."""

from django.contrib import admin
from .models import (
    InsuranceCompany, InsurancePolicy, InsuredAsset,
    PremiumPayment, ClaimRecord, PolicyRenewal
)


@admin.register(InsuranceCompany)
class InsuranceCompanyAdmin(admin.ModelAdmin):
    """Insurance Company Admin."""
    list_display = ['code', 'name', 'short_name', 'contact_person', 'is_active']
    list_filter = ['is_active', 'company_type', 'created_at']
    search_fields = ['code', 'name', 'short_name', 'contact_person']


@admin.register(InsurancePolicy)
class InsurancePolicyAdmin(admin.ModelAdmin):
    """Insurance Policy Admin."""
    list_display = ['policy_no', 'company', 'insurance_type', 'start_date', 'end_date', 'status', 'total_premium']
    list_filter = ['status', 'insurance_type', 'payment_frequency', 'created_at']
    search_fields = ['policy_no', 'policy_name', 'company__name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'start_date'


@admin.register(InsuredAsset)
class InsuredAssetAdmin(admin.ModelAdmin):
    """Insured Asset Admin."""
    list_display = ['policy', 'asset', 'insured_amount', 'premium_amount']
    list_filter = ['created_at']
    search_fields = ['policy__policy_no', 'asset__asset_name']


@admin.register(PremiumPayment)
class PremiumPaymentAdmin(admin.ModelAdmin):
    """Premium Payment Admin."""
    list_display = ['payment_no', 'policy', 'due_date', 'amount', 'paid_amount', 'status']
    list_filter = ['status', 'due_date', 'paid_date']
    search_fields = ['payment_no', 'policy__policy_no']


@admin.register(ClaimRecord)
class ClaimRecordAdmin(admin.ModelAdmin):
    """Claim Record Admin."""
    list_display = ['claim_no', 'policy', 'incident_date', 'incident_type', 'status', 'claimed_amount', 'paid_amount']
    list_filter = ['status', 'incident_type', 'incident_date']
    search_fields = ['claim_no', 'policy__policy_no']


@admin.register(PolicyRenewal)
class PolicyRenewalAdmin(admin.ModelAdmin):
    """Policy Renewal Admin."""
    list_display = ['renewal_no', 'original_policy', 'renewed_policy', 'original_premium', 'new_premium']
    list_filter = ['created_at']
    search_fields = ['renewal_no', 'original_policy__policy_no', 'renewed_policy__policy_no']
```

**Step 2: Verify admin access**
```bash
python manage.py check
```

**Step 3: Commit**
```bash
git add backend/apps/insurance/admin.py
git commit -m "feat(insurance): Add Django admin configuration"
```

---

### Task 10: Create Frontend API Layer

**Files:**
- Create: `frontend/src/api/insurance.js`

**Step 1: Create API client**

```javascript
// frontend/src/api/insurance.js
/**
 * Insurance management API client
 */

import request from '@/utils/request'

export const insuranceApi = {
  // Companies
  listCompanies(params) {
    return request({
      url: '/api/insurance-companies/',
      method: 'get',
      params
    })
  },

  createCompany(data) {
    return request({
      url: '/api/insurance-companies/',
      method: 'post',
      data
    })
  },

  // Policies
  listPolicies(params) {
    return request({
      url: '/api/insurance-policies/',
      method: 'get',
      params
    })
  },

  getPolicy(id) {
    return request({
      url: `/api/insurance-policies/${id}/`,
      method: 'get'
    })
  },

  createPolicy(data) {
    return request({
      url: '/api/insurance-policies/',
      method: 'post',
      data
    })
  },

  updatePolicy(id, data) {
    return request({
      url: `/api/insurance-policies/${id}/`,
      method: 'put',
      data
    })
  },

  activatePolicy(id) {
    return request({
      url: `/api/insurance-policies/${id}/activate/`,
      method: 'post'
    })
  },

  getExpiringPolicies(params) {
    return request({
      url: '/api/insurance-policies/expiring-soon/',
      method: 'get',
      params
    })
  },

  getDashboardStats() {
    return request({
      url: '/api/insurance-policies/dashboard-stats/',
      method: 'get'
    })
  },

  // Insured Assets
  listInsuredAssets(params) {
    return request({
      url: '/api/insured-assets/',
      method: 'get',
      params
    })
  },

  createInsuredAsset(data) {
    return request({
      url: '/api/insured-assets/',
      method: 'post',
      data
    })
  },

  // Premium Payments
  listPremiumPayments(params) {
    return request({
      url: '/api/premium-payments/',
      method: 'get',
      params
    })
  },

  // Claims
  listClaims(params) {
    return request({
      url: '/api/claim-records/',
      method: 'get',
      params
    })
  },

  createClaim(data) {
    return request({
      url: '/api/claim-records/',
      method: 'post',
      data
    })
  },

  approveClaim(id, data) {
    return request({
      url: `/api/claim-records/${id}/approve/`,
      method: 'post',
      data
    })
  },

  recordClaimPayment(id, data) {
    return request({
      url: `/api/claim-records/${id}/record-payment/`,
      method: 'post',
      data
    })
  }
}
```

**Step 2: Commit**
```bash
git add frontend/src/api/insurance.js
git commit -m "feat(insurance): Add frontend API client for insurance module"
```

---

### Task 11: Create Insurance Policy List Page

**Files:**
- Create: `frontend/src/views/insurance/InsurancePolicyList.vue`

**Step 1: Create list page component**

```vue
<!-- frontend/src/views/insurance/InsurancePolicyList.vue -->
<template>
  <BaseListPage
    title="Insurance Policies"
    :fetch-method="fetchData"
    :columns="columns"
    :search-fields="searchFields"
    :filter-fields="filterFields"
    :custom-slots="['company', 'period', 'status', 'actions']"
    @row-click="handleRowClick"
    @create="handleCreate"
  >
    <template #company="{ row }">
      <div class="company-info">
        <div class="name">{{ row.company_name }}</div>
        <div class="type">{{ row.insurance_type }}</div>
      </div>
    </template>

    <template #period="{ row }">
      <div class="period-info">
        <div>{{ formatDate(row.start_date) }} ~ {{ formatDate(row.end_date) }}</div>
        <el-tag
          v-if="row.days_until_expiry !== null && row.days_until_expiry <= 30"
          size="small"
          type="warning"
        >
          {{ row.days_until_expiry }} days left
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
            <el-dropdown-item command="assets">Insured Assets</el-dropdown-item>
            <el-dropdown-item command="payments">Premium Payments</el-dropdown-item>
            <el-dropdown-item command="claims">Claims</el-dropdown-item>
            <el-dropdown-item command="renew">Renew</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </template>
  </BaseListPage>
</template>

<script setup>
import { useRouter } from 'vue-router'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { insuranceApi } from '@/api/insurance'
import { ElMessage } from 'element-plus'

const router = useRouter()

const columns = [
  { prop: 'policy_no', label: 'Policy No', width: 140 },
  { prop: 'company', label: 'Company', minWidth: 180, slot: true },
  { prop: 'period', label: 'Period', width: 240, slot: true },
  { prop: 'total_insured_amount', label: 'Insured Amount', width: 120 },
  { prop: 'total_premium', label: 'Premium', width: 100 },
  { prop: 'status', label: 'Status', width: 100, slot: true },
  { prop: 'actions', label: 'Actions', width: 200, slot: true, fixed: 'right' }
]

const searchFields = [
  { prop: 'keyword', label: 'Search', placeholder: 'Policy No / Company' }
]

const filterFields = [
  {
    prop: 'status',
    label: 'Status',
    options: [
      { label: 'Draft', value: 'draft' },
      { label: 'Active', value: 'active' },
      { label: 'Expired', value: 'expired' },
      { label: 'Cancelled', value: 'cancelled' }
    ]
  },
  {
    prop: 'expires_soon',
    label: 'Expiring Soon',
    options: [
      { label: 'Yes', value: true },
      { label: 'No', value: false }
    ]
  }
]

const fetchData = (params) => insuranceApi.listPolicies(params)

const formatDate = (date) => {
  return date ? new Date(date).toLocaleDateString() : '-'
}

const getStatusType = (status) => {
  const types = {
    draft: 'info',
    active: 'success',
    expired: 'danger',
    cancelled: 'warning',
    terminated: 'danger',
    renewed: ''
  }
  return types[status] || ''
}

const getStatusLabel = (status) => {
  const labels = {
    draft: 'Draft',
    active: 'Active',
    expired: 'Expired',
    cancelled: 'Cancelled',
    terminated: 'Terminated',
    renewed: 'Renewed'
  }
  return labels[status] || status
}

const handleRowClick = (row) => {
  router.push(`/insurance/${row.id}`)
}

const handleCreate = () => {
  router.push('/insurance/create')
}

const handleView = (row) => {
  router.push(`/insurance/${row.id}`)
}

const handleActivate = async (row) => {
  try {
    await insuranceApi.activatePolicy(row.id)
    ElMessage.success('Policy activated successfully')
    location.reload()
  } catch (error) {
    ElMessage.error(error.message || 'Failed to activate policy')
  }
}

const handleMore = (command, row) => {
  const routes = {
    assets: `/insurance/${row.id}/assets`,
    payments: `/insurance/${row.id}/payments`,
    claims: `/insurance/${row.id}/claims`,
    renew: `/insurance/${row.id}/renew`
  }
  if (routes[command]) {
    router.push(routes[command])
  }
}
</script>

<style scoped>
.company-info .name {
  font-weight: 500;
}
.company-info .type {
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
git add frontend/src/views/insurance/InsurancePolicyList.vue
git commit -m "feat(insurance): Add insurance policy list page"
```

---

### Task 12: Add Router Configuration

**Files:**
- Modify: `frontend/src/router/index.js`

**Step 1: Add insurance routes**

```javascript
// Add to frontend/src/router/index.js

{
  path: '/insurance',
  component: Layout,
  meta: { title: 'Insurance', icon: 'shield' },
  children: [
    {
      path: '',
      name: 'InsurancePolicyList',
      component: () => import('@/views/insurance/InsurancePolicyList.vue'),
      meta: { title: 'Insurance Policies' }
    }
  ]
}
```

**Step 2: Commit**
```bash
git add frontend/src/router/index.js
git commit -m "feat(insurance): Add insurance routes to router"
```

---

### Task 13: Run Full Test Suite

**Step 1: Run all insurance tests**
```bash
pytest backend/apps/insurance/tests/ -v --tb=short
```

**Step 2: Verify all tests pass**
Expected: All tests pass

**Step 3: Run full backend test suite**
```bash
pytest backend/apps/ -v --tb=short
```

**Step 4: Check test coverage**
```bash
pytest backend/apps/insurance/ --cov=apps.insurance --cov-report=term
```

---

### Task 14: Verify End-to-End

**Step 1: Start backend server**
```bash
python manage.py runserver
```

**Step 2: Test API endpoints**
```bash
# List policies
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/insurance-policies/

# Create policy
curl -X POST -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"policy_no":"POL-TEST-001","company":"<company-id>","insurance_type":"property","start_date":"2026-01-01","end_date":"2026-12-31","total_insured_amount":1000000,"total_premium":5000}' \
  http://localhost:8000/api/insurance-policies/

# Get dashboard stats
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/insurance-policies/dashboard-stats/
```

**Step 3: Verify frontend**
```bash
npm run dev
```
Navigate to `http://localhost:5173/insurance` and verify

**Step 4: Final commit**
```bash
git add -A
git commit -m "feat(insurance): Complete insurance management module implementation"
```

---

## Summary

### Files Created (19 files)
1. `backend/apps/insurance/__init__.py`
2. `backend/apps/insurance/models.py` (6 models)
3. `backend/apps/insurance/serializers.py` (6 serializers)
4. `backend/apps/insurance/filters.py` (3 filters)
5. `backend/apps/insurance/viewsets.py` (6 viewsets)
6. `backend/apps/insurance/urls.py`
7. `backend/apps/insurance/admin.py`
8. `backend/apps/insurance/tests/__init__.py`
9. `backend/apps/insurance/tests/test_models.py`
10. `backend/apps/insurance/tests/test_serializers.py`
11. `backend/apps/insurance/tests/test_api.py`
12. `frontend/src/api/insurance.js`
13. `frontend/src/views/insurance/InsurancePolicyList.vue`
14. `backend/apps/insurance/migrations/0001_initial.py`

### Files Modified (2 files)
1. `backend/config/urls.py` (include insurance URLs)
2. `frontend/src/router/index.js` (add insurance routes)

### Total Estimated Time: 4-5 hours

---

## Next Steps

After completing this implementation:
1. Create comprehensive E2E tests
2. Add notification system for expiry alerts
3. Implement document upload for policies
4. Add reporting/analytics dashboard
