# IT Asset Management Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend the GZEAMS asset management system with IT-specific features including hardware configuration tracking, software license management, IT maintenance records, and automatic configuration change logging.

**Architecture:** Create new `apps/it_assets` module with models extending base Asset via OneToOne relationships, signals for automatic change logging, and RESTful ViewSets following GZEAMS base class patterns.

**Tech Stack:** Django 5.0, Django REST Framework, PostgreSQL (JSONB), pytest

---

## Pre-Implementation Checklist

- [ ] Read PRD: `docs/plans/it_asset_management/IT_ASSET_MANAGEMENT_PRD.md`
- [ ] Review base models: `apps/common/models.py` (BaseModel)
- [ ] Review base ViewSet: `apps/common/viewsets/base.py` (BaseModelViewSetWithBatch)
- [ ] Review Asset model: `apps/assets/models.py` (Asset)

---

## Task 1: Create it_assets Module Structure

**Files:**
- Create: `backend/apps/it_assets/__init__.py`
- Create: `backend/apps/it_assets/models.py`
- Create: `backend/apps/it_assets/apps.py`

**Step 1: Create module __init__.py**

```python
# backend/apps/it_assets/__init__.py
default_app_config = 'apps.it_assets.apps.ITAssetsConfig'
```

**Step 2: Create apps.py configuration**

```python
# backend/apps/it_assets/apps.py
from django.apps import AppConfig


class ITAssetsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.it_assets'
    verbose_name = 'IT Asset Management'
```

**Step 3: Create models.py with imports**

```python
# backend/apps/it_assets/models.py
"""
IT Asset models for GZEAMS.
"""
from django.db import models
from django.core.validators import MinValueValidator
from apps.common.models import BaseModel
```

**Step 4: Commit**

```bash
cd backend
git add apps/it_assets/
git commit -m "feat(it_assets): create module structure for IT asset management"
```

---

## Task 2: Implement ITAssetInfo Model

**Files:**
- Modify: `backend/apps/it_assets/models.py`

**Step 1: Write the failing test for ITAssetInfo**

```python
# backend/apps/it_assets/tests/test_models.py
import pytest
from django.test import TestCase
from apps.it_assets.models import ITAssetInfo
from apps.assets.models import Asset, AssetCategory
from apps.organizations.models import Organization
from apps.accounts.models import User


class ITAssetInfoModelTest(TestCase):
    def setUp(self):
        self.unique_suffix = "test1234"
        self.org = Organization.objects.create(
            name=f'Test Org {self.unique_suffix}',
            code=f'TESTORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            organization=self.org
        )
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='COMPUTER',
            name='Computer Equipment',
            created_by=self.user
        )
        self.asset = Asset.objects.create(
            organization=self.org,
            asset_code=f'ASSET{self.unique_suffix}',
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=10000,
            purchase_date='2026-01-01',
            created_by=self.user
        )

    def test_create_it_asset_info(self):
        """Test creating IT asset info with hardware specs"""
        it_info = ITAssetInfo.objects.create(
            organization=self.org,
            asset=self.asset,
            cpu_model='Intel Core i7-12700K',
            cpu_cores=12,
            ram_capacity=32,
            ram_type='DDR5',
            disk_type='NVMe',
            disk_capacity=1024,
            mac_address='00:1A:2B:3C:4D:5E',
            ip_address='192.168.1.100',
            os_name='Windows 11 Pro',
            os_version='22H2',
            created_by=self.user
        )

        assert it_info.asset == self.asset
        assert it_info.cpu_model == 'Intel Core i7-12700K'
        assert it_info.ram_capacity == 32
        assert it_info.mac_address == '00:1A:2B:3C:4D:5E'

    def test_get_full_config(self):
        """Test full configuration summary"""
        it_info = ITAssetInfo.objects.create(
            organization=self.org,
            asset=self.asset,
            cpu_model='Intel Core i7',
            ram_capacity=32,
            ram_type='DDR5',
            disk_capacity=1024,
            created_by=self.user
        )

        config = it_info.get_full_config()
        assert 'Intel Core i7' in config
        assert '32GB' in config
        assert '1024GB' in config
```

**Step 2: Run test to verify it fails**

```bash
cd backend
./venv/Scripts/python.exe -m pytest apps/it_assets/tests/test_models.py::ITAssetInfoModelTest::test_create_it_asset_info -v
```

Expected: `ImportError: cannot import name 'ITAssetInfo'`

**Step 3: Implement ITAssetInfo model**

Add to `backend/apps/it_assets/models.py`:

```python
class ITAssetInfo(BaseModel):
    """
    IT Asset Information Extension Model

    Extends the base Asset model with IT-specific hardware and software information.
    """
    class Meta:
        db_table = 'it_asset_info'
        verbose_name = 'IT Asset Information'
        verbose_name_plural = 'IT Asset Information'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'asset']),
            models.Index(fields=['organization', 'mac_address']),
        ]

    asset = models.OneToOneField(
        'assets.Asset',
        on_delete=models.CASCADE,
        related_name='it_info',
        help_text='Related asset'
    )

    # Hardware Configuration
    cpu_model = models.CharField(max_length=200, blank=True)
    cpu_cores = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    cpu_threads = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    ram_capacity = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    ram_type = models.CharField(max_length=50, blank=True)
    ram_slots = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    disk_type = models.CharField(max_length=50, blank=True)
    disk_capacity = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1)])
    disk_count = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    gpu_model = models.CharField(max_length=200, blank=True)
    gpu_memory = models.IntegerField(null=True, blank=True)

    # Network Information
    mac_address = models.CharField(max_length=17, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    hostname = models.CharField(max_length=100, blank=True)

    # Operating System
    os_name = models.CharField(max_length=100, blank=True)
    os_version = models.CharField(max_length=100, blank=True)
    os_architecture = models.CharField(max_length=50, blank=True)
    os_license_key = models.CharField(max_length=200, blank=True)

    # Security
    disk_encrypted = models.BooleanField(default=False)
    antivirus_software = models.CharField(max_length=100, blank=True)
    antivirus_enabled = models.BooleanField(default=True)

    # AD Domain
    ad_domain = models.CharField(max_length=100, blank=True)
    ad_computer_name = models.CharField(max_length=100, blank=True)

    # Notes
    it_notes = models.TextField(blank=True)

    def __str__(self):
        return f"IT Info - {self.asset.asset_name}"

    def get_full_config(self):
        """Get full hardware configuration summary."""
        config = []
        if self.cpu_model:
            config.append(f"CPU: {self.cpu_model}")
        if self.ram_capacity:
            config.append(f"RAM: {self.ram_capacity}GB {self.ram_type}")
        if self.disk_capacity:
            config.append(f"Disk: {self.disk_type} {self.disk_capacity}GB")
        return " | ".join(config)
```

**Step 4: Run test to verify it passes**

```bash
cd backend
./venv/Scripts/python.exe -m pytest apps/it_assets/tests/test_models.py::ITAssetInfoModelTest -v
```

Expected: `PASSED`

**Step 5: Commit**

```bash
git add apps/it_assets/models.py
git commit -m "feat(it_assets): implement ITAssetInfo model with hardware specs"
```

---

## Task 3: Implement Software and SoftwareLicense Models

**Files:**
- Modify: `backend/apps/it_assets/models.py`
- Create: `backend/apps/it_assets/tests/test_software_models.py`

**Step 1: Write the failing test**

```python
# backend/apps/it_assets/tests/test_software_models.py
from django.test import TestCase
from apps.it_assets.models import Software, SoftwareLicense
from apps.organizations.models import Organization
from apps.accounts.models import User


class SoftwareModelTest(TestCase):
    def setUp(self):
        self.unique_suffix = "soft1234"
        self.org = Organization.objects.create(
            name=f'Test Org {self.unique_suffix}',
            code=f'TESTORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            organization=self.org
        )

    def test_software_creation(self):
        """Test creating software catalog entry"""
        software = Software.objects.create(
            organization=self.org,
            code='OFF365',
            name='Microsoft Office 365',
            version='2021',
            vendor='Microsoft',
            software_type='office',
            created_by=self.user
        )

        assert software.code == 'OFF365'
        assert software.name == 'Microsoft Office 365'

    def test_license_utilization_rate(self):
        """Test license utilization calculation"""
        software = Software.objects.create(
            organization=self.org,
            code='WIN11',
            name='Windows 11',
            created_by=self.user
        )

        license = SoftwareLicense.objects.create(
            organization=self.org,
            license_no='LIC-001',
            software=software,
            total_units=10,
            used_units=7,
            purchase_date='2026-01-01',
            created_by=self.user
        )

        assert license.utilization_rate() == 70.0
        assert license.available_units() == 3
```

**Step 2: Run test to verify it fails**

```bash
./venv/Scripts/python.exe -m pytest apps/it_assets/tests/test_software_models.py -v
```

Expected: `ImportError: cannot import name 'Software'`

**Step 3: Implement Software and SoftwareLicense models**

Add to `backend/apps/it_assets/models.py`:

```python
class Software(BaseModel):
    """Software Catalog Model"""
    class Meta:
        db_table = 'software_catalog'
        verbose_name = 'Software'
        verbose_name_plural = 'Software Catalog'
        ordering = ['name']
        indexes = [
            models.Index(fields=['organization', 'code']),
        ]

    SOFTWARE_TYPE_CHOICES = [
        ('os', 'Operating System'),
        ('office', 'Office Suite'),
        ('professional', 'Professional Software'),
        ('development', 'Development Tool'),
        ('security', 'Security Software'),
        ('other', 'Other'),
    ]

    code = models.CharField(max_length=50, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=50, blank=True)
    vendor = models.CharField(max_length=200, blank=True)
    software_type = models.CharField(max_length=50, choices=SOFTWARE_TYPE_CHOICES, default='other')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} {self.version}".strip()


class SoftwareLicense(BaseModel):
    """Software License Model"""
    class Meta:
        db_table = 'software_licenses'
        verbose_name = 'Software License'
        verbose_name_plural = 'Software Licenses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'software']),
            models.Index(fields=['organization', 'expiry_date']),
        ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    ]

    license_no = models.CharField(max_length=100, unique=True, db_index=True)
    software = models.ForeignKey(Software, on_delete=models.CASCADE, related_name='licenses')
    license_key = models.CharField(max_length=500, blank=True)

    total_units = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    used_units = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    purchase_date = models.DateField()
    expiry_date = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='active')

    def is_expired(self):
        from django.utils import timezone
        if self.expiry_date is None:
            return False
        return timezone.now().date() > self.expiry_date

    def available_units(self):
        return self.total_units - self.used_units

    def utilization_rate(self):
        if self.total_units == 0:
            return 0
        return (self.used_units / self.total_units) * 100
```

**Step 4: Run tests**

```bash
./venv/Scripts/python.exe -m pytest apps/it_assets/tests/test_software_models.py -v
```

**Step 5: Commit**

```bash
git add apps/it_assets/models.py apps/it_assets/tests/
git commit -m "feat(it_assets): implement Software and SoftwareLicense models"
```

---

## Task 4: Implement LicenseAllocation Model

**Files:**
- Modify: `backend/apps/it_assets/models.py`
- Create: `backend/apps/it_assets/tests/test_license_allocation.py`

**Step 1: Write the failing test**

```python
# backend/apps/it_assets/tests/test_license_allocation.py
from django.test import TestCase
from apps.it_assets.models import Software, SoftwareLicense, LicenseAllocation
from apps.assets.models import Asset, AssetCategory
from apps.organizations.models import Organization
from apps.accounts.models import User


class LicenseAllocationTest(TestCase):
    def setUp(self):
        self.unique_suffix = "alloc1234"
        self.org = Organization.objects.create(
            name=f'Test Org {self.unique_suffix}',
            code=f'TESTORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            organization=self.org
        )
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='COMPUTER',
            name='Computer Equipment',
            created_by=self.user
        )
        self.asset = Asset.objects.create(
            organization=self.org,
            asset_code=f'ASSET{self.unique_suffix}',
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=10000,
            purchase_date='2026-01-01',
            created_by=self.user
        )
        self.software = Software.objects.create(
            organization=self.org,
            code='OFF365',
            name='Office 365',
            created_by=self.user
        )
        self.license = SoftwareLicense.objects.create(
            organization=self.org,
            license_no='LIC-001',
            software=self.software,
            total_units=5,
            purchase_date='2026-01-01',
            created_by=self.user
        )

    def test_license_allocation(self):
        """Test allocating license to asset"""
        from django.utils import timezone

        allocation = LicenseAllocation.objects.create(
            organization=self.org,
            license=self.license,
            asset=self.asset,
            allocated_date=timezone.now().date(),
            allocated_by=self.user,
            created_by=self.user
        )

        assert allocation.license == self.license
        assert allocation.asset == self.asset

        # Verify license usage updated
        self.license.refresh_from_db()
        assert self.license.used_units == 1
```

**Step 2: Run test to verify it fails**

```bash
./venv/Scripts/python.exe -m pytest apps/it_assets/tests/test_license_allocation.py -v
```

**Step 3: Implement LicenseAllocation model**

Add to `backend/apps/it_assets/models.py`:

```python
class LicenseAllocation(BaseModel):
    """Software License Allocation Model"""
    class Meta:
        db_table = 'license_allocations'
        verbose_name = 'License Allocation'
        verbose_name_plural = 'License Allocations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'license']),
            models.Index(fields=['organization', 'asset']),
        ]
        unique_together = [['organization', 'license', 'asset']]

    license = models.ForeignKey(SoftwareLicense, on_delete=models.CASCADE, related_name='allocations')
    asset = models.ForeignKey('assets.Asset', on_delete=models.CASCADE, related_name='software_allocations')

    allocated_date = models.DateField()
    allocated_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='license_allocations')
    allocation_key = models.CharField(max_length=500, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new and self.is_active:
            self.license.used_units += 1
            self.license.save()

    def __str__(self):
        return f"{self.license.software.name} -> {self.asset.asset_name}"
```

**Step 4: Run tests**

```bash
./venv/Scripts/python.exe -m pytest apps/it_assets/tests/test_license_allocation.py -v
```

**Step 5: Commit**

```bash
git add apps/it_assets/models.py apps/it_assets/tests/
git commit -m "feat(it_assets): implement LicenseAllocation model with usage tracking"
```

---

## Task 5: Implement ITMaintenanceRecord Model

**Files:**
- Modify: `backend/apps/it_assets/models.py`
- Create: `backend/apps/it_assets/tests/test_maintenance.py`

**Step 1: Write the failing test**

```python
# backend/apps/it_assets/tests/test_maintenance.py
from django.test import TestCase
from apps.it_assets.models import ITMaintenanceRecord
from apps.assets.models import Asset, AssetCategory
from apps.organizations.models import Organization
from apps.accounts.models import User


class ITMaintenanceRecordTest(TestCase):
    def setUp(self):
        self.unique_suffix = "maint1234"
        self.org = Organization.objects.create(
            name=f'Test Org {self.unique_suffix}',
            code=f'TESTORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            organization=self.org
        )
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='COMPUTER',
            name='Computer Equipment',
            created_by=self.user
        )
        self.asset = Asset.objects.create(
            organization=self.org,
            asset_code=f'ASSET{self.unique_suffix}',
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=10000,
            purchase_date='2026-01-01',
            created_by=self.user
        )

    def test_maintenance_record_creation(self):
        """Test creating maintenance record"""
        record = ITMaintenanceRecord.objects.create(
            organization=self.org,
            asset=self.asset,
            maintenance_type='repair',
            maintenance_date='2026-01-21',
            problem_description='Computer not starting',
            labor_cost=200,
            parts_cost=150,
            created_by=self.user
        )

        assert record.maintenance_no.startswith('MT')
        assert record.total_cost == 350

    def test_downtime_hours(self):
        """Test downtime calculation"""
        from django.utils import timezone
        import datetime

        record = ITMaintenanceRecord.objects.create(
            organization=self.org,
            asset=self.asset,
            maintenance_type='repair',
            maintenance_date='2026-01-21',
            downtime_start=timezone.now(),
            downtime_end=timezone.now() + timezone.timedelta(hours=4),
            created_by=self.user
        )

        assert record.downtime_hours() == 4.0
```

**Step 2: Run test to verify it fails**

```bash
./venv/Scripts/python.exe -m pytest apps/it_assets/tests/test_maintenance.py -v
```

**Step 3: Implement ITMaintenanceRecord model**

Add to `backend/apps/it_assets/models.py`:

```python
class ITMaintenanceRecord(BaseModel):
    """IT Maintenance Record Model"""
    class Meta:
        db_table = 'it_maintenance_records'
        verbose_name = 'IT Maintenance Record'
        verbose_name_plural = 'IT Maintenance Records'
        ordering = ['-maintenance_date', '-created_at']
        indexes = [
            models.Index(fields=['organization', 'maintenance_no']),
            models.Index(fields=['organization', 'asset']),
            models.Index(fields=['organization', 'status']),
        ]

    MAINTENANCE_TYPE_CHOICES = [
        ('repair', 'Repair'),
        ('upgrade', 'Upgrade'),
        ('replacement', 'Component Replacement'),
        ('routine', 'Routine Maintenance'),
        ('cleaning', 'Cleaning'),
        ('diagnostic', 'Diagnostic'),
        ('installation', 'Software Installation'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    maintenance_no = models.CharField(max_length=50, unique=True, db_index=True)
    asset = models.ForeignKey('assets.Asset', on_delete=models.CASCADE, related_name='maintenance_records')

    maintenance_type = models.CharField(max_length=50, choices=MAINTENANCE_TYPE_CHOICES)
    maintenance_date = models.DateField()

    problem_description = models.TextField(blank=True)
    symptoms = models.TextField(blank=True)
    resolution = models.TextField(blank=True)
    resolution_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')

    technician = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='maintenance_tasks')

    labor_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    parts_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    downtime_start = models.DateTimeField(null=True, blank=True)
    downtime_end = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.maintenance_no:
            self.maintenance_no = self._generate_maintenance_no()
        self.total_cost = (self.labor_cost or 0) + (self.parts_cost or 0)
        super().save(*args, **kwargs)

    def _generate_maintenance_no(self):
        from apps.system.services import SequenceService
        try:
            return SequenceService.get_next_value(
                'MAINTENANCE_NO',
                organization_id=self.organization_id
            )
        except:
            from django.utils import timezone
            prefix = timezone.now().strftime('%Y%m')
            return f"MT{prefix}{timezone.now().strftime('%H%M%S')}"

    def downtime_hours(self):
        if self.downtime_start and self.downtime_end:
            delta = self.downtime_end - self.downtime_start
            return delta.total_seconds() / 3600
        return 0

    def __str__(self):
        return f"{self.maintenance_no} - {self.asset.asset_name}"
```

**Step 4: Run tests**

```bash
./venv/Scripts/python.exe -m pytest apps/it_assets/tests/test_maintenance.py -v
```

**Step 5: Commit**

```bash
git add apps/it_assets/models.py apps/it_assets/tests/
git commit -m "feat(it_assets): implement ITMaintenanceRecord model"
```

---

## Task 6: Implement ConfigurationChange Model

**Files:**
- Modify: `backend/apps/it_assets/models.py`
- Create: `backend/apps/it_assets/tests/test_config_change.py`

**Step 1: Write the failing test**

```python
# backend/apps/it_assets/tests/test_config_change.py
from django.test import TestCase
from apps.it_assets.models import ConfigurationChange, ITAssetInfo
from apps.assets.models import Asset, AssetCategory
from apps.organizations.models import Organization
from apps.accounts.models import User


class ConfigurationChangeTest(TestCase):
    def setUp(self):
        self.unique_suffix = "config1234"
        self.org = Organization.objects.create(
            name=f'Test Org {self.unique_suffix}',
            code=f'TESTORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            organization=self.org
        )
        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='COMPUTER',
            name='Computer Equipment',
            created_by=self.user
        )
        self.asset = Asset.objects.create(
            organization=self.org,
            asset_code=f'ASSET{self.unique_suffix}',
            asset_name='Test Laptop',
            asset_category=self.category,
            purchase_price=10000,
            purchase_date='2026-01-01',
            created_by=self.user
        )

    def test_log_change(self):
        """Test logging a configuration change"""
        change = ConfigurationChange.log_change(
            asset=self.asset,
            field_name='ram_capacity',
            old_value='16',
            new_value='32',
            changed_by=self.user,
            change_reason='Memory upgrade',
            change_type='hardware'
        )

        # Verify change was logged
        changes = ConfigurationChange.objects.filter(asset=self.asset, field_name='ram_capacity')
        assert changes.count() == 1
        assert changes.first().old_value == '16'
        assert changes.first().new_value == '32'
```

**Step 2: Run test to verify it fails**

```bash
./venv/Scripts/python.exe -m pytest apps/it_assets/tests/test_config_change.py -v
```

**Step 3: Implement ConfigurationChange model**

Add to `backend/apps/it_assets/models.py`:

```python
class ConfigurationChange(BaseModel):
    """Configuration Change History Model"""
    class Meta:
        db_table = 'configuration_changes'
        verbose_name = 'Configuration Change'
        verbose_name_plural = 'Configuration Changes'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'asset']),
            models.Index(fields=['organization', 'field_name']),
        ]

    CHANGE_TYPE_CHOICES = [
        ('hardware', 'Hardware Change'),
        ('software', 'Software Change'),
        ('network', 'Network Change'),
        ('security', 'Security Change'),
        ('other', 'Other Change'),
    ]

    asset = models.ForeignKey('assets.Asset', on_delete=models.CASCADE, related_name='configuration_changes')
    field_name = models.CharField(max_length=100)
    field_display_name = models.CharField(max_length=200)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    change_type = models.CharField(max_length=50, choices=CHANGE_TYPE_CHOICES, default='other')
    change_reason = models.TextField(blank=True)
    changed_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.asset.asset_name}: {self.field_display_name} changed"

    @classmethod
    def log_change(cls, asset, field_name, old_value, new_value,
                   changed_by=None, change_reason='', change_type='other', ip_address=None):
        """Create a configuration change log entry"""
        display_names = {
            'cpu_model': 'CPU Model',
            'ram_capacity': 'RAM Capacity',
            'disk_capacity': 'Disk Capacity',
            'mac_address': 'MAC Address',
            'ip_address': 'IP Address',
            'os_name': 'Operating System',
        }

        cls.objects.create(
            organization_id=asset.organization_id,
            asset=asset,
            field_name=field_name,
            field_display_name=display_names.get(field_name, field_name),
            old_value=str(old_value) if old_value else '',
            new_value=str(new_value) if new_value else '',
            change_type=change_type,
            change_reason=change_reason,
            changed_by=changed_by,
            created_by=changed_by or asset.created_by,
            ip_address=ip_address
        )
```

**Step 4: Run tests**

```bash
./venv/Scripts/python.exe -m pytest apps/it_assets/tests/test_config_change.py -v
```

**Step 5: Commit**

```bash
git add apps/it_assets/models.py apps/it_assets/tests/
git commit -m "feat(it_assets): implement ConfigurationChange model for audit trail"
```

---

## Task 7: Create Serializers

**Files:**
- Create: `backend/apps/it_assets/serializers.py`
- Create: `backend/apps/it_assets/tests/test_serializers.py`

**Step 1: Write the failing test**

```python
# backend/apps/it_assets/tests/test_serializers.py
from django.test import TestCase
from apps.it_assets.serializers import ITAssetInfoSerializer
from apps.it_assets.models import ITAssetInfo


class ITAssetInfoSerializerTest(TestCase):
    def test_serializer_contains_required_fields(self):
        """Test serializer includes all required fields"""
        fields = ITAssetInfoSerializer().fields
        required_fields = ['asset', 'cpu_model', 'ram_capacity', 'mac_address']

        for field in required_fields:
            assert field in fields
```

**Step 2: Run test to verify it fails**

```bash
./venv/Scripts/python.exe -m pytest apps/it_assets/tests/test_serializers.py -v
```

**Step 3: Implement serializers**

```python
# backend/apps/it_assets/serializers.py
from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer
from .models import (
    ITAssetInfo, Software, SoftwareLicense, LicenseAllocation,
    ITMaintenanceRecord, ConfigurationChange
)


class ITAssetInfoSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = ITAssetInfo
        fields = BaseModelSerializer.Meta.fields + [
            'asset', 'cpu_model', 'cpu_cores', 'cpu_threads',
            'ram_capacity', 'ram_type', 'ram_slots',
            'disk_type', 'disk_capacity', 'disk_count',
            'gpu_model', 'gpu_memory',
            'mac_address', 'ip_address', 'hostname',
            'os_name', 'os_version', 'os_architecture',
            'disk_encrypted', 'antivirus_software',
            'ad_domain', 'ad_computer_name',
            'it_notes',
        ]
        extra_kwargs = {
            'os_license_key': {'write_only': True},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if data.get('os_license_key'):
            data['os_license_key'] = '***MASKED***'
        return data


class SoftwareSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = Software
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'version', 'vendor', 'software_type', 'is_active',
        ]


class SoftwareLicenseSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = SoftwareLicense
        fields = BaseModelSerializer.Meta.fields + [
            'license_no', 'software', 'license_key',
            'total_units', 'used_units', 'available_units',
            'utilization_rate', 'is_expired',
            'purchase_date', 'expiry_date', 'purchase_price',
            'status',
        ]
        extra_kwargs = {
            'license_key': {'write_only': True},
        ]


class ITMaintenanceRecordSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = ITMaintenanceRecord
        fields = BaseModelSerializer.Meta.fields + [
            'maintenance_no', 'asset',
            'maintenance_type', 'maintenance_date',
            'problem_description', 'symptoms', 'resolution',
            'status', 'technician',
            'labor_cost', 'parts_cost', 'total_cost',
            'downtime_hours', 'notes',
        ]
```

**Step 4: Run tests**

```bash
./venv/Scripts/python.exe -m pytest apps/it_assets/tests/test_serializers.py -v
```

**Step 5: Commit**

```bash
git add apps/it_assets/serializers.py apps/it_assets/tests/
git commit -m "feat(it_assets): implement serializers for IT asset models"
```

---

## Task 8: Create Filters

**Files:**
- Create: `backend/apps/it_assets/filters.py`

**Step 1: Create filters module**

```python
# backend/apps/it_assets/filters.py
from django_filters import rest_framework as filters
from apps.common.filters.base import BaseModelFilter
from .models import (
    ITAssetInfo, Software, SoftwareLicense, ITMaintenanceRecord
)


class ITAssetInfoFilter(BaseModelFilter):
    class Meta(BaseModelFilter.Meta):
        model = ITAssetInfo
        fields = BaseModelFilter.Meta.fields + [
            'cpu_model', 'ram_capacity', 'disk_type', 'os_name',
        ]


class SoftwareLicenseFilter(BaseModelFilter):
    status = filters.CharFilter()
    expiring_soon = filters.BooleanFilter(method='filter_expiring_soon')

    def filter_expiring_soon(self, queryset, name, value):
        if value:
            from django.utils import timezone
            delta = timezone.now().date() + timezone.timedelta(days=30)
            return queryset.filter(expiry_date__lte=delta, status='active')
        return queryset

    class Meta(BaseModelFilter.Meta):
        model = SoftwareLicense
        fields = BaseModelFilter.Meta.fields + ['software', 'status']
```

**Step 2: Commit**

```bash
git add apps/it_assets/filters.py
git commit -m "feat(it_assets): implement filters for IT asset queries"
```

---

## Task 9: Create ViewSets

**Files:**
- Create: `backend/apps/it_assets/viewsets.py`
- Create: `backend/apps/it_assets/tests/test_viewsets.py`

**Step 1: Write the failing test**

```python
# backend/apps/it_assets/tests/test_viewsets.py
from django.test import TestCase
from rest_framework.test import APIClient
from apps.it_assets.viewsets import ITAssetInfoViewSet
from apps.it_assets.models import ITAssetInfo
from apps.assets.models import Asset, AssetCategory
from apps.organizations.models import Organization
from apps.accounts.models import User


class ITAssetInfoViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.unique_suffix = "view1234"
        self.org = Organization.objects.create(
            name=f'Test Org {self.unique_suffix}',
            code=f'TESTORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

    def test_list_it_assets(self):
        """Test listing IT assets"""
        url = '/api/it-assets/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('data', response.data)

    def test_create_it_asset_info(self):
        """Test creating IT asset info"""
        # First create an asset
        category = AssetCategory.objects.create(
            organization=self.org,
            code='PC',
            name='PC',
            created_by=self.user
        )
        asset = Asset.objects.create(
            organization=self.org,
            asset_code='TEST001',
            asset_name='Test PC',
            asset_category=category,
            purchase_price=5000,
            purchase_date='2026-01-01',
            created_by=self.user
        )

        url = '/api/it-assets/'
        data = {
            'asset': str(asset.id),
            'cpu_model': 'Intel i7',
            'ram_capacity': 16,
            'mac_address': '00:11:22:33:44:55'
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['cpu_model'], 'Intel i7')
```

**Step 2: Run test to verify it fails**

```bash
./venv/Scripts/python.exe -m pytest apps/it_assets/tests/test_viewsets.py::ITAssetInfoViewSetTest::test_list_it_assets -v
```

**Step 3: Implement ViewSets**

```python
# backend/apps/it_assets/viewsets.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from .models import (
    ITAssetInfo, Software, SoftwareLicense, LicenseAllocation,
    ITMaintenanceRecord, ConfigurationChange
)
from .serializers import (
    ITAssetInfoSerializer, SoftwareSerializer, SoftwareLicenseSerializer,
    ITMaintenanceRecordSerializer
)
from .filters import (
    ITAssetInfoFilter, SoftwareLicenseFilter
)


class ITAssetInfoViewSet(BaseModelViewSetWithBatch):
    queryset = ITAssetInfo.objects.all()
    serializer_class = ITAssetInfoSerializer
    filterset_class = ITAssetInfoFilter

    def perform_update(self, serializer):
        """Log configuration changes on update"""
        instance = self.get_object()
        tracked_fields = ['cpu_model', 'ram_capacity', 'disk_capacity', 'mac_address', 'ip_address']

        for field in tracked_fields:
            old_val = getattr(instance, field, None)
            new_val = serializer.validated_data.get(field)
            if new_val is not None and old_val != new_val:
                ConfigurationChange.log_change(
                    asset=instance.asset,
                    field_name=field,
                    old_value=old_val,
                    new_value=new_val,
                    changed_by=self.request.user,
                    change_type='hardware' if field in ['cpu_model', 'ram_capacity'] else 'other'
                )

        serializer.save(updated_by=self.request.user)


class SoftwareViewSet(BaseModelViewSetWithBatch):
    queryset = Software.objects.all()
    serializer_class = SoftwareSerializer


class SoftwareLicenseViewSet(BaseModelViewSetWithBatch):
    queryset = SoftwareLicense.objects.all()
    serializer_class = SoftwareLicenseSerializer
    filterset_class = SoftwareLicenseFilter

    @action(detail=False, methods=['get'])
    def expiring(self, request):
        """Get licenses expiring within 30 days"""
        from django.utils import timezone
        delta = timezone.now().date() + timezone.timedelta(days=30)
        licenses = self.queryset.filter(expiry_date__lte=delta, status='active')

        page = self.paginate_queryset(licenses)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class ITMaintenanceRecordViewSet(BaseModelViewSetWithBatch):
    queryset = ITMaintenanceRecord.objects.all()
    serializer_class = ITMaintenanceRecordSerializer

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark maintenance as completed"""
        record = self.get_object()
        record.status = 'completed'
        record.resolution_date = timezone.now().date()
        record.technician = request.user
        record.save()

        serializer = self.get_serializer(record)
        return Response({'success': True, 'data': serializer.data})
```

**Step 4: Run tests**

```bash
./venv/Scripts/python.exe -m pytest apps/it_assets/tests/test_viewsets.py -v
```

**Step 5: Commit**

```bash
git add apps/it_assets/viewsets.py apps/it_assets/tests/
git commit -m "feat(it_assets): implement ViewSets with auto-change-logging"
```

---

## Task 10: Configure URL Routing

**Files:**
- Create: `backend/apps/it_assets/urls.py`
- Modify: `backend/config/urls.py`

**Step 1: Create it_assets URLs**

```python
# backend/apps/it_assets/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .viewsets import (
    ITAssetInfoViewSet, SoftwareViewSet, SoftwareLicenseViewSet,
    ITMaintenanceRecordViewSet
)

router = DefaultRouter()
router.register(r'it-assets', ITAssetInfoViewSet, basename='it-asset')
router.register(r'software', SoftwareViewSet, basename='software')
router.register(r'software-licenses', SoftwareLicenseViewSet, basename='software-license')
router.register(r'maintenance-records', ITMaintenanceRecordViewSet, basename='maintenance-record')

urlpatterns = [
    path('', include(router.urls)),
]
```

**Step 2: Add to main URL config**

```python
# In backend/config/urls.py, add to urlpatterns:
path('api/it/', include('apps.it_assets.urls')),
```

**Step 3: Commit**

```bash
git add apps/it_assets/urls.py config/urls.py
git commit -m "feat(it_assets): configure URL routing for IT asset APIs"
```

---

## Task 11: Create Database Migration

**Files:**
- Create: `backend/apps/it_assets/migrations/0001_initial.py`

**Step 1: Create migration**

```bash
cd backend
./venv/Scripts/python.exe manage.py makemigrations it_assets
```

**Step 2: Review generated migration**

Check `apps/it_assets/migrations/0001_initial.py` to ensure all models are included.

**Step 3: Run migration**

```bash
./venv/Scripts/python.exe manage.py migrate it_assets
```

**Step 4: Commit**

```bash
git add apps/it_assets/migrations/
git commit -m "feat(it_assets): create initial database migration"
```

---

## Task 12: Add to Django Admin

**Files:**
- Create: `backend/apps/it_assets/admin.py`

**Step 1: Create admin configuration**

```python
# backend/apps/it_assets/admin.py
from django.contrib import admin
from .models import (
    ITAssetInfo, Software, SoftwareLicense, LicenseAllocation,
    ITMaintenanceRecord, ConfigurationChange
)


@admin.register(ITAssetInfo)
class ITAssetInfoAdmin(admin.ModelAdmin):
    list_display = ['asset', 'cpu_model', 'ram_capacity', 'mac_address', 'os_name']
    search_fields = ['asset__asset_code', 'asset__asset_name', 'mac_address']
    list_filter = ['ram_type', 'disk_type', 'os_name']


@admin.register(Software)
class SoftwareAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'version', 'vendor', 'software_type']
    search_fields = ['code', 'name', 'vendor']


@admin.register(SoftwareLicense)
class SoftwareLicenseAdmin(admin.ModelAdmin):
    list_display = ['license_no', 'software', 'total_units', 'used_units', 'status', 'expiry_date']
    list_filter = ['status', 'software']
    readonly_fields = ['utilization_rate', 'available_units', 'is_expired']


@admin.register(ITMaintenanceRecord)
class ITMaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ['maintenance_no', 'asset', 'maintenance_type', 'maintenance_date', 'status', 'total_cost']
    list_filter = ['maintenance_type', 'status']
```

**Step 2: Commit**

```bash
git add apps/it_assets/admin.py
git commit -m "feat(it_assets): add Django admin configuration"
```

---

## Task 13: Create Frontend API Layer

**Files:**
- Create: `frontend/src/api/it_assets.js`

**Step 1: Create API module**

```javascript
// frontend/src/api/it_assets.js
import request from '@/utils/request'

export const itAssetApi = {
    list(params) {
        return request({
            url: '/api/it/it-assets/',
            method: 'get',
            params
        })
    },

    get(id) {
        return request({
            url: `/api/it/it-assets/${id}/`,
            method: 'get'
        })
    },

    create(data) {
        return request({
            url: '/api/it/it-assets/',
            method: 'post',
            data
        })
    },

    update(id, data) {
        return request({
            url: `/api/it/it-assets/${id}/`,
            method: 'put',
            data
        })
    },

    delete(id) {
        return request({
            url: `/api/it/it-assets/${id}/`,
            method: 'delete'
        })
    }
}

export const softwareLicenseApi = {
    list(params) {
        return request({
            url: '/api/it/software-licenses/',
            method: 'get',
            params
        })
    },

    expiring(params) {
        return request({
            url: '/api/it/software-licenses/expiring/',
            method: 'get',
            params
        })
    },

    complianceReport() {
        return request({
            url: '/api/it/software-licenses/compliance-report/',
            method: 'get'
        })
    }
}

export const maintenanceApi = {
    list(params) {
        return request({
            url: '/api/it/maintenance-records/',
            method: 'get',
            params
        })
    },

    create(data) {
        return request({
            url: '/api/it/maintenance-records/',
            method: 'post',
            data
        })
    },

    complete(id) {
        return request({
            url: `/api/it/maintenance-records/${id}/complete/`,
            method: 'post'
        })
    }
}
```

**Step 2: Commit**

```bash
cd frontend
git add src/api/it_assets.js
git commit -m "feat: add IT assets API layer"
```

---

## Task 14: Create IT Asset List Page

**Files:**
- Create: `frontend/src/views/it_assets/ITAssetList.vue`

**Step 1: Create list page component**

```vue
<!-- frontend/src/views/it_assets/ITAssetList.vue -->
<template>
    <BaseListPage
        title="IT资产管理"
        :fetch-method="fetchData"
        :columns="columns"
        :search-fields="searchFields"
        :custom-slots="['configuration', 'status', 'actions']"
    >
        <template #configuration="{ row }">
            <div v-if="row.it_info" class="config">
                <span v-if="row.it_info.cpu_model">{{ row.it_info.cpu_model }}</span>
                <span v-if="row.it_info.ram_capacity"> / {{ row.it_info.ram_capacity }}GB RAM</span>
            </div>
        </template>

        <template #actions="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="primary" @click="handleMaintenance(row)">维护</el-button>
        </template>
    </BaseListPage>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { itAssetApi } from '@/api/it_assets'

const router = useRouter()

const columns = [
    { prop: 'asset_code', label: '资产编码', width: 150 },
    { prop: 'asset_name', label: '资产名称', minWidth: 200 },
    { prop: 'configuration', label: '硬件配置', minWidth: 300, slot: true },
    { prop: 'it_info.ip_address', label: 'IP地址', width: 130 },
    { prop: 'actions', label: '操作', width: 150, slot: true }
]

const fetchData = (params) => itAssetApi.list(params)

const handleEdit = (row) => {
    router.push(`/it-assets/${row.id}/edit`)
}

const handleMaintenance = (row) => {
    router.push({ path: '/it-assets/maintenance/create', query: { asset_id: row.id } })
}
</script>
```

**Step 2: Commit**

```bash
git add src/views/it_assets/ITAssetList.vue
git commit -m "feat: add IT asset list page"
```

---

## Task 15: Create Software License Management Page

**Files:**
- Create: `frontend/src/views/it_assets/SoftwareLicenseList.vue`

**Step 1: Create license management page**

```vue
<template>
    <div class="software-license-page">
        <el-row :gutter="20">
            <el-col :span="16">
                <BaseListPage
                    title="软件许可证"
                    :fetch-method="fetchLicenses"
                    :columns="licenseColumns"
                    :custom-slots="['utilization', 'expiry']"
                >
                    <template #utilization="{ row }">
                        <el-progress
                            :percentage="row.utilization_rate"
                            :status="row.utilization_rate > 90 ? 'exception' : 'success'"
                        />
                    </template>
                </BaseListPage>
            </el-col>
            <el-col :span="8">
                <el-card>
                    <template #header>合规概览</template>
                    <el-statistic title="许可证总数" :value="stats.total_licenses" />
                    <el-divider />
                    <el-statistic title="即将过期" :value="stats.expiring_licenses" />
                </el-card>
            </el-col>
        </el-row>
    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { softwareLicenseApi } from '@/api/it_assets'

const stats = ref({ total_licenses: 0, expiring_licenses: 0 })

const licenseColumns = [
    { prop: 'license_no', label: '许可证编号', width: 150 },
    { prop: 'software_name', label: '软件名称', minWidth: 150 },
    { prop: 'utilization', label: '使用率', width: 150, slot: true },
    { prop: 'total_units', label: '总数量', width: 100 }
]

const fetchLicenses = (params) => softwareLicenseApi.list(params)

onMounted(async () => {
    const response = await softwareLicenseApi.complianceReport()
    stats.value = response.data.data
})
</script>
```

**Step 2: Commit**

```bash
git add src/views/it_assets/SoftwareLicenseList.vue
git commit -m "feat: add software license management page"
```

---

## Task 16: Add Router Configuration

**Files:**
- Modify: `frontend/src/router/index.js`

**Step 1: Add IT assets routes**

Add to router configuration:

```javascript
{
    path: '/it-assets',
    name: 'ITAssets',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { title: 'IT资产管理', icon: 'Monitor' },
    children: [
        {
            path: '',
            name: 'ITAssetList',
            component: () => import('@/views/it_assets/ITAssetList.vue')
        },
        {
            path: ':id/edit',
            name: 'ITAssetEdit',
            component: () => import('@/views/it_assets/ITAssetForm.vue')
        },
        {
            path: 'licenses',
            name: 'SoftwareLicenseList',
            component: () => import('@/views/it_assets/SoftwareLicenseList.vue')
        }
    ]
}
```

**Step 2: Commit**

```bash
git add src/router/index.js
git commit -m "feat: add IT assets router configuration"
```

---

## Task 17: Run Full Test Suite and Verify

**Step 1: Run backend tests**

```bash
cd backend
./venv/Scripts/python.exe -m pytest apps/it_assets/tests/ -v --tb=short
```

Expected: All tests pass

**Step 2: Check API endpoints work**

```bash
curl http://localhost:8000/api/it/it-assets/ -H "X-Organization-Id: test-org-id"
```

**Step 3: Commit if all passing**

```bash
git commit --allow-empty -m "test(it_assets): all tests passing"
```

---

## Completion Checklist

After finishing all tasks, verify:

- [ ] All models inherit from BaseModel
- [ ] All serializers inherit from BaseModelSerializer
- [ ] All ViewSets inherit from BaseModelViewSetWithBatch
- [ ] All filters inherit from BaseModelFilter
- [ ] Organization isolation works correctly
- [ ] Soft delete works correctly
- [ ] Configuration changes are logged automatically
- [ ] Frontend API layer uses centralized request utility
- [ ] All test files have >80% coverage
- [ ] Documentation updated in PRD

---

## Total Estimated Time: 8-10 hours

**Breakdown:**
- Models: 2h
- Serializers/Filters/ViewSets: 2.5h
- Tests: 2h
- Frontend: 2.5h
- Integration & verification: 1h
