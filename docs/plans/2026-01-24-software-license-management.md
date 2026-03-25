# Software License Management Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a software license management module for tracking software products, licenses, and asset allocations with compliance reporting.

**Architecture:**
- Backend: Django app `software_licenses` with 3 models (Software, SoftwareLicense, LicenseAllocation) all inheriting from BaseModel
- Frontend: Vue 3 pages using BaseListPage/BaseFormPage components with TypeScript API layer
- All models automatically get organization isolation, soft delete, and audit trails via BaseModel inheritance

**Tech Stack:**
- Backend: Django 5.0, DRF, PostgreSQL (JSONB for custom_fields)
- Frontend: Vue 3 (Composition API), TypeScript, Element Plus, Pinia
- Testing: pytest (backend), vitest (frontend)

---

## Phase 1: Backend - Models and Migrations (2h)

### Task 1.1: Create software_licenses app structure

**Files:**
- Create: `backend/apps/software_licenses/__init__.py`
- Create: `backend/apps/software_licenses/models.py`

**Step 1: Create app directory**

```bash
# In backend/ directory
mkdir -p apps/software_licenses
```

**Step 2: Create __init__.py**

```python
# backend/apps/software_licenses/__init__.py
"""
Software Licenses Application

Manages software catalog, licenses, and asset allocations.
"""
```

**Step 3: Write models with Software catalog**

```python
# backend/apps/software_licenses/models.py

from django.db import models
from django.core.validators import MinValueValidator
from apps.common.models import BaseModel


class Software(BaseModel):
    """
    Software Catalog Model

    Defines software products available for license management.
    """

    class Meta:
        db_table = 'software_catalog'
        verbose_name = 'Software'
        verbose_name_plural = 'Software Catalog'
        ordering = ['name']
        indexes = [
            models.Index(fields=['organization', 'code']),
            models.Index(fields=['organization', 'vendor']),
        ]

    SOFTWARE_TYPE_CHOICES = [
        ('os', 'Operating System'),
        ('office', 'Office Suite'),
        ('professional', 'Professional Software'),
        ('development', 'Development Tool'),
        ('security', 'Security Software'),
        ('database', 'Database'),
        ('other', 'Other'),
    ]

    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Software code (e.g., WIN11, OFF365)'
    )
    name = models.CharField(
        max_length=200,
        help_text='Software name'
    )
    version = models.CharField(
        max_length=50,
        blank=True,
        help_text='Software version'
    )
    vendor = models.CharField(
        max_length=200,
        blank=True,
        help_text='Software vendor'
    )
    software_type = models.CharField(
        max_length=50,
        choices=SOFTWARE_TYPE_CHOICES,
        default='other',
        help_text='Software type'
    )
    license_type = models.CharField(
        max_length=50,
        blank=True,
        help_text='License type (perpetual, subscription, OEM, volume)'
    )
    category = models.ForeignKey(
        'assets.AssetCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='software_items',
        help_text='Related asset category'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this software is actively tracked'
    )

    def __str__(self):
        return f"{self.name} {self.version}".strip()
```

**Step 4: Add SoftwareLicense model to same file**

```python
# Add to backend/apps/software_licenses/models.py

class SoftwareLicense(BaseModel):
    """
    Software License Model

    Tracks software license purchases, allocations, and expirations.
    """

    class Meta:
        db_table = 'software_licenses'
        verbose_name = 'Software License'
        verbose_name_plural = 'Software Licenses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'software']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'expiry_date']),
        ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('revoked', 'Revoked'),
    ]

    license_no = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text='License number'
    )
    software = models.ForeignKey(
        Software,
        on_delete=models.CASCADE,
        related_name='licenses',
        help_text='Associated software'
    )
    license_key = models.CharField(
        max_length=500,
        blank=True,
        help_text='License key/serial (encrypted)'
    )

    # License Quantity
    total_units = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text='Total licensed units'
    )
    used_units = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Currently allocated units'
    )

    # License Period
    purchase_date = models.DateField(
        help_text='License purchase date'
    )
    expiry_date = models.DateField(
        null=True,
        blank=True,
        help_text='License expiration date (null for perpetual)'
    )

    # Financial
    purchase_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='License purchase price'
    )
    annual_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Annual maintenance/subscription cost'
    )

    # Status
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='active',
        help_text='License status'
    )

    # License Details
    license_type = models.CharField(
        max_length=50,
        blank=True,
        help_text='License type (perpetual, subscription, OEM, volume)'
    )
    agreement_no = models.CharField(
        max_length=100,
        blank=True,
        help_text='Enterprise agreement number'
    )
    vendor = models.ForeignKey(
        'assets.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='software_licenses',
        help_text='License vendor/supplier'
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text='License notes'
    )

    def __str__(self):
        return f"{self.license_no} - {self.software.name}"

    def is_expired(self):
        """Check if license is expired."""
        if self.expiry_date is None:
            return False  # Perpetual license
        from django.utils import timezone
        return timezone.now().date() > self.expiry_date

    def available_units(self):
        """Get available license units."""
        return self.total_units - self.used_units

    def utilization_rate(self):
        """Get license utilization rate as percentage."""
        if self.total_units == 0:
            return 0
        return (self.used_units / self.total_units) * 100
```

**Step 5: Add LicenseAllocation model to same file**

```python
# Add to backend/apps/software_licenses/models.py

class LicenseAllocation(BaseModel):
    """
    Software License Allocation Model

    Tracks which assets are assigned which software licenses.
    """

    class Meta:
        db_table = 'license_allocations'
        verbose_name = 'License Allocation'
        verbose_name_plural = 'License Allocations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'license']),
            models.Index(fields=['organization', 'asset']),
            models.Index(fields=['organization', 'license', 'asset']),
        ]
        unique_together = [['organization', 'license', 'asset']]

    license = models.ForeignKey(
        SoftwareLicense,
        on_delete=models.CASCADE,
        related_name='allocations',
        help_text='Allocated license'
    )
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.CASCADE,
        related_name='software_allocations',
        help_text='Asset with this software'
    )

    allocated_date = models.DateField(
        help_text='Allocation date'
    )
    allocated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='license_allocations',
        help_text='User who made the allocation'
    )

    allocation_key = models.CharField(
        max_length=500,
        blank=True,
        help_text='Specific license key for this allocation (encrypted)'
    )

    # Deallocation fields
    deallocated_date = models.DateField(
        null=True,
        blank=True,
        help_text='Deallocation date'
    )
    deallocated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='license_deallocations',
        help_text='User who deallocated'
    )

    is_active = models.BooleanField(
        default=True,
        help_text='Whether this allocation is active'
    )
    notes = models.TextField(
        blank=True,
        help_text='Allocation notes'
    )

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.license.software.name} -> {self.asset.asset_name} ({status})"

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        # Update license usage on create (only if active)
        if is_new and self.is_active:
            self.license.used_units += 1
            self.license.save()

        super().save(*args, **kwargs)
```

**Step 6: Commit**

```bash
git add backend/apps/software_licenses/
git commit -m "feat(software-licenses): add models for Software, SoftwareLicense, LicenseAllocation"
```

---

### Task 1.2: Create and run initial migration

**Files:**
- Create: `backend/apps/software_licenses/migrations/0001_initial.py`
- Modify: `backend/config/settings/__init__.py`

**Step 1: Add app to INSTALLED_APPS**

```python
# In backend/config/settings/__init__.py, add to INSTALLED_APPS:

INSTALLED_APPS = [
    # ... existing apps ...
    'apps.software_licenses',
]
```

**Step 2: Create migration**

```bash
cd backend
python manage.py makemigrations software_licenses
```

Expected output: `Migrations for 'software_licenses': 0001_initial.py`

**Step 3: Review generated migration**

Check that `backend/apps/software_licenses/migrations/0001_initial.py` contains:
- Software model with all fields
- SoftwareLicense model with all fields
- LicenseAllocation model with all fields
- unique_together constraint for allocations

**Step 4: Run migration**

```bash
python manage.py migrate software_licenses
```

Expected output: `Running migrations: Applying software_licenses.0001_initial... OK`

**Step 5: Verify tables created**

```bash
python manage.py dbshell
# In psql:
\dt software_*
# Should show: software_catalog, software_licenses, license_allocations
\q
```

**Step 6: Commit**

```bash
git add backend/apps/software_licenses/migrations/ backend/config/settings/__init__.py
git commit -m "feat(software-licenses): create and run initial migration"
```

---

## Phase 2: Backend - Serializers and Filters (2h)

### Task 2.1: Create serializers

**Files:**
- Create: `backend/apps/software_licenses/serializers/__init__.py`

**Step 1: Write serializers module**

```python
# backend/apps/software_licenses/serializers/__init__.py

from rest_framework import serializers
from apps.common.serializers.base import BaseModelSerializer
from .models import Software, SoftwareLicense, LicenseAllocation


class SoftwareSerializer(BaseModelSerializer):
    """Software Catalog Serializer"""

    class Meta(BaseModelSerializer.Meta):
        model = Software
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'version', 'vendor', 'software_type',
            'license_type', 'category', 'is_active',
        ]


class SoftwareListSerializer(BaseModelSerializer):
    """Lightweight serializer for list views"""

    class Meta(BaseModelSerializer.Meta):
        model = Software
        fields = BaseModelSerializer.Meta.fields + [
            'code', 'name', 'version', 'vendor', 'software_type', 'is_active',
        ]


class SoftwareDetailSerializer(BaseModelSerializer):
    """Detailed serializer with nested category"""

    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = Software
        fields = SoftwareSerializer.Meta.fields + ['category_name']


class SoftwareLicenseSerializer(BaseModelSerializer):
    """Software License Serializer"""
    software_name = serializers.CharField(source='software.name', read_only=True)
    software_version = serializers.CharField(source='software.version', read_only=True)
    available_units = serializers.IntegerField(read_only=True)
    utilization_rate = serializers.FloatField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = SoftwareLicense
        fields = BaseModelSerializer.Meta.fields + [
            'license_no', 'software', 'software_name', 'software_version',
            'license_key', 'total_units', 'used_units', 'available_units',
            'utilization_rate', 'purchase_date', 'expiry_date', 'is_expired',
            'purchase_price', 'annual_cost', 'status', 'license_type',
            'agreement_no', 'vendor', 'notes',
        ]
        extra_kwargs = {
            'license_key': {'write_only': True},
        }


class SoftwareLicenseListSerializer(BaseModelSerializer):
    """Lightweight license serializer for lists"""
    software_name = serializers.CharField(source='software.name', read_only=True)
    available_units = serializers.IntegerField(read_only=True)
    utilization_rate = serializers.FloatField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = SoftwareLicense
        fields = [
            'id', 'license_no', 'software', 'software_name',
            'total_units', 'used_units', 'available_units',
            'utilization_rate', 'expiry_date', 'status',
            'created_at', 'updated_at',
        ]


class SoftwareLicenseDetailSerializer(BaseModelSerializer):
    """Detailed license serializer"""
    software_name = serializers.CharField(source='software.name', read_only=True)
    software_version = serializers.CharField(source='software.version', read_only=True)
    software_type = serializers.CharField(source='software.software_type', read_only=True)
    available_units = serializers.IntegerField(read_only=True)
    utilization_rate = serializers.FloatField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = SoftwareLicense
        fields = SoftwareLicenseSerializer.Meta.fields + [
            'software_type', 'vendor_name',
        ]


class LicenseAllocationSerializer(BaseModelSerializer):
    """License Allocation Serializer"""
    software_name = serializers.CharField(source='license.software.name', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    allocated_by_name = serializers.CharField(source='allocated_by.username', read_only=True)
    deallocated_by_name = serializers.CharField(source='deallocated_by.username', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = LicenseAllocation
        fields = BaseModelSerializer.Meta.fields + [
            'license', 'software_name', 'asset', 'asset_name', 'asset_code',
            'allocated_date', 'allocated_by', 'allocated_by_name',
            'deallocated_date', 'deallocated_by', 'deallocated_by_name',
            'allocation_key', 'is_active', 'notes',
        ]


class LicenseAllocationListSerializer(BaseModelSerializer):
    """Lightweight allocation serializer for lists"""

    class Meta(BaseModelSerializer.Meta):
        model = LicenseAllocation
        fields = [
            'id', 'license', 'asset', 'allocated_date',
            'is_active', 'deallocated_date', 'created_at',
        ]


class LicenseAllocationDetailSerializer(BaseModelSerializer):
    """Detailed allocation serializer"""
    software_name = serializers.CharField(source='license.software.name', read_only=True)
    license_no = serializers.CharField(source='license.license_no', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    allocated_by_name = serializers.CharField(source='allocated_by.username', read_only=True)
    deallocated_by_name = serializers.CharField(source='deallocated_by.username', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = LicenseAllocation
        fields = LicenseAllocationSerializer.Meta.fields + [
            'software_name', 'license_no', 'asset_name', 'asset_code',
        ]


__all__ = [
    'SoftwareSerializer',
    'SoftwareListSerializer',
    'SoftwareDetailSerializer',
    'SoftwareLicenseSerializer',
    'SoftwareLicenseListSerializer',
    'SoftwareLicenseDetailSerializer',
    'LicenseAllocationSerializer',
    'LicenseAllocationListSerializer',
    'LicenseAllocationDetailSerializer',
]
```

**Step 2: Commit**

```bash
git add backend/apps/software_licenses/serializers/
git commit -m "feat(software-licenses): add serializers with list/detail variants"
```

---

### Task 2.2: Create filters

**Files:**
- Create: `backend/apps/software_licenses/filters/__init__.py`

**Step 1: Write filters module**

```python
# backend/apps/software_licenses/filters/__init__.py

from django_filters import rest_framework as filters
from apps.common.filters.base import BaseModelFilter
from .models import Software, SoftwareLicense, LicenseAllocation


class SoftwareFilter(BaseModelFilter):
    """Software Filter"""

    software_type = filters.CharFilter(field_name='software_type')
    vendor = filters.CharFilter(lookup_expr='icontains')
    is_active = filters.BooleanFilter()

    class Meta(BaseModelFilter.Meta):
        model = Software
        fields = BaseModelFilter.Meta.fields + [
            'software_type', 'vendor', 'is_active',
        ]


class SoftwareLicenseFilter(BaseModelFilter):
    """Software License Filter"""

    status = filters.CharFilter()
    software = filters.CharFilter(field_name='software__code')
    expiring_soon = filters.BooleanFilter(method='filter_expiring_soon')

    def filter_expiring_soon(self, queryset, name, value):
        """Filter licenses expiring within 30 days."""
        if value:
            from django.utils import timezone
            from datetime import timedelta
            delta = timezone.now().date() + timedelta(days=30)
            return queryset.filter(
                expiry_date__lte=delta,
                expiry_date__gte=timezone.now().date(),
                status='active'
            )
        return queryset

    class Meta(BaseModelFilter.Meta):
        model = SoftwareLicense
        fields = BaseModelFilter.Meta.fields + [
            'software', 'status', 'expiry_date',
        ]


class LicenseAllocationFilter(BaseModelFilter):
    """License Allocation Filter"""

    is_active = filters.BooleanFilter()
    software = filters.CharFilter(field_name='license__software__code')

    class Meta(BaseModelFilter.Meta):
        model = LicenseAllocation
        fields = BaseModelFilter.Meta.fields + [
            'license', 'asset', 'is_active',
        ]


__all__ = [
    'SoftwareFilter',
    'SoftwareLicenseFilter',
    'LicenseAllocationFilter',
]
```

**Step 2: Commit**

```bash
git add backend/apps/software_licenses/filters/
git commit -m "feat(software-licenses): add filter classes with expiring_soon custom filter"
```

---

## Phase 3: Backend - ViewSets and Services (3h)

### Task 3.1: Create services

**Files:**
- Create: `backend/apps/software_licenses/services/__init__.py`

**Step 1: Write services module**

```python
# backend/apps/software_licenses/services/__init__.py

from apps.common.services.base_crud import BaseCRUDService
from .models import Software, SoftwareLicense, LicenseAllocation


class SoftwareService(BaseCRUDService):
    """Software Catalog Service"""

    def __init__(self):
        super().__init__(Software)

    def get_by_code(self, code: str):
        """Get software by code."""
        return self.model_class.objects.filter(code=code).first()


class SoftwareLicenseService(BaseCRUDService):
    """Software License Service"""

    def __init__(self):
        super().__init__(SoftwareLicense)

    def get_expiring_licenses(self, organization_id: str, days: int = 30):
        """Get licenses expiring within specified days."""
        from django.utils import timezone
        from datetime import timedelta

        delta = timezone.now().date() + timedelta(days=days)

        return self.model_class.objects.filter(
            organization_id=organization_id,
            expiry_date__lte=delta,
            status='active'
        )

    def get_over_utilized_licenses(self, organization_id: str):
        """Get licenses with utilization over 100%."""
        licenses = self.model_class.objects.filter(
            organization_id=organization_id,
            status='active'
        )

        over_utilized = []
        for license in licenses:
            if license.utilization_rate() > 100:
                over_utilized.append(license)

        return over_utilized

    def allocate_license(self, license_id: str, asset_id: str,
                         allocated_by: str, allocation_key: str = None,
                         notes: str = None):
        """Allocate a license to an asset."""
        from django.utils import timezone

        license = self.get(license_id)

        if license.available_units() <= 0:
            raise ValueError('No available licenses')

        from apps.assets.models import Asset
        asset = Asset.objects.get(id=asset_id)

        allocation = LicenseAllocation.objects.create(
            organization_id=license.organization_id,
            license_id=license_id,
            asset_id=asset_id,
            allocated_by_id=allocated_by,
            allocated_date=timezone.now().date(),
            allocation_key=allocation_key,
            notes=notes or '',
            created_by_id=allocated_by
        )

        return allocation

    def deallocate_license(self, allocation_id: str, deallocated_by: str):
        """Deallocate a license from an asset."""
        from datetime import date

        allocation = LicenseAllocation.objects.get(id=allocation_id)

        if allocation.is_active and allocation.license.used_units > 0:
            allocation.license.used_units -= 1
            allocation.license.save()

        allocation.is_active = False
        allocation.deallocated_date = date.today()
        allocation.deallocated_by_id = deallocated_by
        allocation.save()

        return allocation


class LicenseAllocationService(BaseCRUDService):
    """License Allocation Service"""

    def __init__(self):
        super().__init__(LicenseAllocation)

    def get_by_asset(self, asset_id: str):
        """Get allocations for an asset."""
        return self.model_class.objects.filter(asset_id=asset_id, is_active=True)

    def get_by_license(self, license_id: str):
        """Get allocations for a license."""
        return self.model_class.objects.filter(license_id=license_id)


__all__ = [
    'SoftwareService',
    'SoftwareLicenseService',
    'LicenseAllocationService',
]
```

**Step 2: Commit**

```bash
git add backend/apps/software_licenses/services/
git commit -m "feat(software-licenses): add service classes with allocation methods"
```

---

### Task 3.2: Create viewsets

**Files:**
- Create: `backend/apps/software_licenses/viewsets/__init__.py`

**Step 1: Write viewsets module**

```python
# backend/apps/software_licenses/viewsets/__init__.py

from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.viewsets.base import BaseModelViewSetWithBatch
from apps.common.permissions.base import IsOrganizationMember
from .models import Software, SoftwareLicense, LicenseAllocation
from .serializers import (
    SoftwareSerializer, SoftwareListSerializer, SoftwareDetailSerializer,
    SoftwareLicenseSerializer, SoftwareLicenseListSerializer, SoftwareLicenseDetailSerializer,
    LicenseAllocationSerializer, LicenseAllocationListSerializer, LicenseAllocationDetailSerializer
)
from .filters import SoftwareFilter, SoftwareLicenseFilter, LicenseAllocationFilter
from .services import SoftwareLicenseService


# Base permission classes
BASE_PERMISSION_CLASSES = [permissions.IsAuthenticated, IsOrganizationMember]


class SoftwareViewSet(BaseModelViewSetWithBatch):
    """
    Software Catalog ViewSet

    Provides:
    - Standard CRUD operations
    - Batch operations (delete, restore, update)
    """
    queryset = Software.objects.select_related('organization', 'category').all()
    permission_classes = BASE_PERMISSION_CLASSES
    filterset_class = SoftwareFilter
    search_fields = ['name', 'vendor', 'version', 'code']
    ordering_fields = ['created_at', 'updated_at', 'name', 'vendor', 'version']
    ordering = ['name', 'version']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return SoftwareListSerializer
        if self.action == 'retrieve':
            return SoftwareDetailSerializer
        return SoftwareSerializer


class SoftwareLicenseViewSet(BaseModelViewSetWithBatch):
    """
    Software License ViewSet

    Provides:
    - Standard CRUD operations
    - Batch operations (delete, restore, update)
    - Custom action: expiring (licenses expiring within 30 days)
    - Custom action: compliance_report
    """
    queryset = SoftwareLicense.objects.select_related(
        'software', 'vendor', 'organization'
    ).all()
    permission_classes = BASE_PERMISSION_CLASSES
    filterset_class = SoftwareLicenseFilter
    search_fields = ['software__name', 'license_no', 'agreement_no']
    ordering_fields = ['created_at', 'updated_at', 'expiry_date', 'software__name']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return SoftwareLicenseListSerializer
        if self.action == 'retrieve':
            return SoftwareLicenseDetailSerializer
        return SoftwareLicenseSerializer

    @action(detail=False, methods=['get'])
    def expiring(self, request):
        """
        Get licenses expiring within 30 days.

        GET /api/licenses/expiring/
        """
        from django.utils import timezone
        from datetime import timedelta

        thirty_days_from_now = timezone.now().date() + timedelta(days=30)
        queryset = self.get_queryset().filter(
            expiry_date__lte=thirty_days_from_now,
            expiry_date__gte=timezone.now().date(),
            status='active'
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=False, methods=['get'])
    def compliance_report(self, request):
        """
        Get software compliance report.

        GET /api/licenses/compliance-report/

        Returns:
        - total_licenses: Total active licenses
        - expiring_licenses: Count expiring within 30 days
        - over_utilized: List of licenses with >100% utilization
        """
        from django.utils import timezone
        from datetime import timedelta

        queryset = self.get_queryset().filter(status='active')
        total_licenses = queryset.count()

        # Expiring within 30 days
        thirty_days_from_now = timezone.now().date() + timedelta(days=30)
        expiring_licenses = queryset.filter(
            expiry_date__lte=thirty_days_from_now
        ).count()

        # Over-utilized licenses
        over_utilized = []
        for license in queryset:
            if license.utilization_rate() > 100:
                over_utilized.append({
                    'id': str(license.id),
                    'license_no': license.license_no,
                    'software': license.software.name,
                    'utilization': round(license.utilization_rate(), 1)
                })

        return Response({
            'success': True,
            'data': {
                'total_licenses': total_licenses,
                'expiring_licenses': expiring_licenses,
                'over_utilized': over_utilized
            }
        })


class LicenseAllocationViewSet(BaseModelViewSetWithBatch):
    """
    License Allocation ViewSet

    Provides:
    - Standard CRUD operations
    - Batch operations (delete, restore, update)
    - Custom action: deallocate (deallocate a license from an asset)
    """
    queryset = LicenseAllocation.objects.select_related(
        'license', 'license__software', 'asset',
        'allocated_by', 'deallocated_by', 'organization'
    ).all()
    permission_classes = BASE_PERMISSION_CLASSES
    filterset_class = LicenseAllocationFilter
    search_fields = ['asset__asset_code', 'asset__asset_name', 'license__software__name']
    ordering_fields = ['created_at', 'updated_at', 'allocated_date', 'deallocated_date']
    ordering = ['-allocated_date']

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return LicenseAllocationListSerializer
        if self.action == 'retrieve':
            return LicenseAllocationDetailSerializer
        return LicenseAllocationSerializer

    def perform_create(self, serializer):
        """Validate license availability before allocation."""
        license_obj = serializer.validated_data['license']

        if license_obj.available_units() <= 0:
            return Response(
                {
                    'success': False,
                    'error': {
                        'code': 'NO_AVAILABLE_LICENSES',
                        'message': 'No available licenses for this software'
                    }
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        from django.utils import timezone
        serializer.save(
            allocated_by=self.request.user,
            allocated_date=timezone.now().date()
        )

    @action(detail=True, methods=['post'])
    def deallocate(self, request, pk=None):
        """
        Deallocate a license from an asset.

        POST /api/license-allocations/{id}/deallocate/

        Request body:
        {
            "notes": "Optional notes about deallocation"
        }
        """
        from datetime import date

        allocation = self.get_object()

        if allocation.deallocated_date is not None:
            return Response({
                'success': False,
                'error': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'License is already deallocated'
                }
            }, status=400)

        # Update allocation
        allocation.deallocated_date = date.today()
        allocation.deallocated_by = request.user
        allocation.is_active = False
        allocation.notes = request.data.get('notes', allocation.notes)
        allocation.save()

        # Update license usage
        if allocation.license.used_units > 0:
            allocation.license.used_units -= 1
            allocation.license.save()

        serializer = self.get_serializer(allocation)
        return Response({
            'success': True,
            'message': 'License deallocated successfully',
            'data': serializer.data
        })


__all__ = [
    'SoftwareViewSet',
    'SoftwareLicenseViewSet',
    'LicenseAllocationViewSet',
]
```

**Step 2: Commit**

```bash
git add backend/apps/software_licenses/viewsets/
git commit -m "feat(software-licenses): add viewsets with expiring and compliance_report actions"
```

---

### Task 3.3: Configure URLs

**Files:**
- Create: `backend/apps/software_licenses/urls.py`
- Modify: `backend/config/urls.py`

**Step 1: Create app URLs**

```python
# backend/apps/software_licenses/urls.py

from rest_framework import routers
from apps.software_licenses.viewsets import (
    SoftwareViewSet,
    SoftwareLicenseViewSet,
    LicenseAllocationViewSet,
)

app_router = routers.DefaultRouter()

# Software catalog endpoints
app_router.register(r'software', SoftwareViewSet, basename='software')

# Software License endpoints
app_router.register(r'licenses', SoftwareLicenseViewSet, basename='software-license')

# License Allocation endpoints
app_router.register(r'license-allocations', LicenseAllocationViewSet, basename='license-allocation')

urlpatterns = app_router.urls
```

**Step 2: Add to main URLs**

```python
# In backend/config/urls.py, add to urlpatterns:

urlpatterns = [
    # ... existing patterns ...
    path('api/software-licenses/', include('apps.software_licenses.urls')),
]
```

**Step 3: Test URLs are registered**

```bash
cd backend
python manage.py show_urls 2>/dev/null | grep software-licenses || \
python manage.py shell -c "from django.urls import get_resolver; print([p for p in get_resolver().url_patterns if 'software' in str(p.pattern)])"
```

Expected: URLs for software, licenses, license-allocations

**Step 4: Commit**

```bash
git add backend/apps/software_licenses/urls.py backend/config/urls.py
git commit -m "feat(software-licenses): configure URL routes"
```

---

### Task 3.4: Create admin configuration

**Files:**
- Create: `backend/apps/software_licenses/admin.py`

**Step 1: Write admin configuration**

```python
# backend/apps/software_licenses/admin.py

from django.contrib import admin
from .models import Software, SoftwareLicense, LicenseAllocation


@admin.register(Software)
class SoftwareAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'version', 'vendor', 'software_type', 'is_active']
    list_filter = ['software_type', 'is_active', 'created_at']
    search_fields = ['code', 'name', 'vendor', 'version']
    ordering = ['name']


@admin.register(SoftwareLicense)
class SoftwareLicenseAdmin(admin.ModelAdmin):
    list_display = ['license_no', 'software', 'total_units', 'used_units', 'status', 'expiry_date']
    list_filter = ['status', 'software__software_type', 'purchase_date', 'expiry_date']
    search_fields = ['license_no', 'software__name', 'agreement_no']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LicenseAllocation)
class LicenseAllocationAdmin(admin.ModelAdmin):
    list_display = ['license', 'asset', 'allocated_date', 'is_active', 'deallocated_date']
    list_filter = ['is_active', 'allocated_date', 'deallocated_date']
    search_fields = ['asset__asset_code', 'asset__asset_name', 'license__software__name']
    ordering = ['-allocated_date']
```

**Step 2: Commit**

```bash
git add backend/apps/software_licenses/admin.py
git commit -m "feat(software-licenses): add Django admin configuration"
```

---

## Phase 4: Backend - Tests (2h)

### Task 4.1: Write model tests

**Files:**
- Create: `backend/apps/software_licenses/tests/__init__.py`
- Create: `backend/apps/software_licenses/tests/test_models.py`

**Step 1: Write failing test for Software model**

```python
# backend/apps/software_licenses/tests/test_models.py

import pytest
from django.test import TestCase
from apps.software_licenses.models import Software, SoftwareLicense, LicenseAllocation
from apps.assets.models import Asset, AssetCategory
from apps.organizations.models import Organization
from apps.accounts.models import User


class SoftwareModelTest(TestCase):
    """Software Model Tests"""

    def setUp(self):
        """Set up test data"""
        self.unique_suffix = "test1234"
        self.org = Organization.objects.create(
            name=f'Test Organization {self.unique_suffix}',
            code=f'TESTORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            organization=self.org
        )

    def test_create_software(self):
        """Test creating a software catalog entry"""
        software = Software.objects.create(
            organization=self.org,
            code='WIN11',
            name='Windows 11',
            version='Pro',
            vendor='Microsoft',
            software_type='os',
            created_by=self.user
        )

        self.assertEqual(software.code, 'WIN11')
        self.assertEqual(software.name, 'Windows 11')
        self.assertEqual(software.software_type, 'os')
        self.assertTrue(software.is_active)

    def test_software_str(self):
        """Test software string representation"""
        software = Software.objects.create(
            organization=self.org,
            code='OFF365',
            name='Microsoft Office 365',
            version='2021',
            created_by=self.user
        )

        str_repr = str(software)
        self.assertIn('Microsoft Office 365', str_repr)
        self.assertIn('2021', str_repr)


class SoftwareLicenseModelTest(TestCase):
    """Software License Model Tests"""

    def setUp(self):
        """Set up test data"""
        self.unique_suffix = "test5678"
        self.org = Organization.objects.create(
            name=f'Test Organization {self.unique_suffix}',
            code=f'TESTORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            organization=self.org
        )

        self.software = Software.objects.create(
            organization=self.org,
            code='OFF365',
            name='Microsoft Office 365',
            version='2021',
            vendor='Microsoft',
            software_type='office',
            created_by=self.user
        )

    def test_license_utilization_rate(self):
        """Test license utilization calculation"""
        license = SoftwareLicense.objects.create(
            organization=self.org,
            license_no='LIC-001',
            software=self.software,
            total_units=10,
            used_units=7,
            purchase_date='2026-01-01',
            created_by=self.user
        )

        self.assertEqual(license.utilization_rate(), 70.0)
        self.assertEqual(license.available_units(), 3)

    def test_is_expired(self):
        """Test license expiration check"""
        from django.utils import timezone

        # Perpetual license
        perpetual_license = SoftwareLicense.objects.create(
            organization=self.org,
            license_no='LIC-002',
            software=self.software,
            total_units=1,
            purchase_date='2026-01-01',
            expiry_date=None,
            created_by=self.user
        )
        self.assertFalse(perpetual_license.is_expired())

        # Expired license
        expired_license = SoftwareLicense.objects.create(
            organization=self.org,
            license_no='LIC-003',
            software=self.software,
            total_units=1,
            purchase_date='2020-01-01',
            expiry_date='2023-01-01',
            created_by=self.user
        )
        self.assertTrue(expired_license.is_expired())


class LicenseAllocationModelTest(TestCase):
    """License Allocation Model Tests"""

    def setUp(self):
        """Set up test data"""
        self.unique_suffix = "test9012"
        self.org = Organization.objects.create(
            name=f'Test Organization {self.unique_suffix}',
            code=f'TESTORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            organization=self.org
        )

        self.software = Software.objects.create(
            organization=self.org,
            code='WIN11',
            name='Windows 11',
            created_by=self.user
        )

        self.license = SoftwareLicense.objects.create(
            organization=self.org,
            license_no='LIC-ALLOC-001',
            software=self.software,
            total_units=5,
            used_units=0,
            purchase_date='2026-01-01',
            created_by=self.user
        )

        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='PC',
            name='Computer'
        )

        self.asset = Asset.objects.create(
            organization=self.org,
            asset_code='PC001',
            asset_name='Test PC',
            asset_category=self.category,
            purchase_price=5000,
            purchase_date='2026-01-01',
            created_by=self.user
        )

    def test_allocation_increases_usage(self):
        """Test that allocation increases license usage"""
        from django.utils import timezone

        LicenseAllocation.objects.create(
            organization=self.org,
            license=self.license,
            asset=self.asset,
            allocated_date=timezone.now().date(),
            allocated_by=self.user,
            created_by=self.user
        )

        self.license.refresh_from_db()
        self.assertEqual(self.license.used_units, 1)

    def test_unique_allocation_constraint(self):
        """Test that duplicate allocations are prevented"""
        from django.utils import timezone
        from django.db import IntegrityError

        LicenseAllocation.objects.create(
            organization=self.org,
            license=self.license,
            asset=self.asset,
            allocated_date=timezone.now().date(),
            allocated_by=self.user,
            created_by=self.user
        )

        # Try to create duplicate
        with self.assertRaises(IntegrityError):
            LicenseAllocation.objects.create(
                organization=self.org,
                license=self.license,
                asset=self.asset,
                allocated_date=timezone.now().date(),
                allocated_by=self.user,
                created_by=self.user
            )
```

**Step 2: Run tests**

```bash
cd backend
pytest apps/software_licenses/tests/test_models.py -v
```

Expected: All tests PASS

**Step 3: Commit**

```bash
git add backend/apps/software_licenses/tests/test_models.py
git commit -m "test(software-licenses): add model tests for Software, SoftwareLicense, LicenseAllocation"
```

---

### Task 4.2: Write API tests

**Files:**
- Create: `backend/apps/software_licenses/tests/test_viewsets.py`

**Step 1: Write failing test for SoftwareLicense API**

```python
# backend/apps/software_licenses/tests/test_viewsets.py

import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from apps.software_licenses.models import Software, SoftwareLicense, LicenseAllocation
from apps.assets.models import Asset, AssetCategory
from apps.organizations.models import Organization
from apps.accounts.models import User


class SoftwareViewSetTest(TestCase):
    """Software API Tests"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.unique_suffix = "api1234"

        self.org = Organization.objects.create(
            name=f'Test Organization {self.unique_suffix}',
            code=f'TESTORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

    def test_create_software(self):
        """Test creating software via API"""
        url = '/api/software-licenses/software/'
        data = {
            'code': 'WIN11',
            'name': 'Windows 11',
            'version': 'Pro',
            'vendor': 'Microsoft',
            'software_type': 'os'
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['code'], 'WIN11')

    def test_list_software(self):
        """Test listing software"""
        Software.objects.create(
            organization=self.org,
            code='TEST1',
            name='Test Software',
            created_by=self.user
        )

        url = '/api/software-licenses/software/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(response.data['data']['count'], 1)


class SoftwareLicenseViewSetTest(TestCase):
    """Software License API Tests"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.unique_suffix = "lic5678"

        self.org = Organization.objects.create(
            name=f'Test Organization {self.unique_suffix}',
            code=f'TESTORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

        self.software = Software.objects.create(
            organization=self.org,
            code='WIN11',
            name='Windows 11',
            version='Pro',
            created_by=self.user
        )

    def test_create_license(self):
        """Test creating software license"""
        url = '/api/software-licenses/licenses/'
        data = {
            'license_no': 'LIC-001',
            'software': str(self.software.id),
            'total_units': 10,
            'purchase_date': '2026-01-01',
            'expiry_date': '2027-01-01'
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['total_units'], 10)
        self.assertEqual(response.data['data']['used_units'], 0)

    def test_expiring_endpoint(self):
        """Test expiring licenses endpoint"""
        from django.utils import timezone
        from datetime import timedelta

        # Create license expiring in 15 days
        SoftwareLicense.objects.create(
            organization=self.org,
            license_no='LIC-EXP001',
            software=self.software,
            total_units=1,
            purchase_date='2026-01-01',
            expiry_date=timezone.now().date() + timedelta(days=15),
            status='active',
            created_by=self.user
        )

        url = '/api/software-licenses/licenses/expiring/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data['data']), 0)

    def test_compliance_report(self):
        """Test compliance report endpoint"""
        # Create over-utilized license
        SoftwareLicense.objects.create(
            organization=self.org,
            license_no='LIC-OVER',
            software=self.software,
            total_units=10,
            used_units=12,
            purchase_date='2026-01-01',
            status='active',
            created_by=self.user
        )

        url = '/api/software-licenses/licenses/compliance-report/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data['data']['over_utilized']), 0)


class LicenseAllocationViewSetTest(TestCase):
    """License Allocation API Tests"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.unique_suffix = "alloc9012"

        self.org = Organization.objects.create(
            name=f'Test Organization {self.unique_suffix}',
            code=f'TESTORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

        self.software = Software.objects.create(
            organization=self.org,
            code='OFF365',
            name='Office 365',
            created_by=self.user
        )

        self.license = SoftwareLicense.objects.create(
            organization=self.org,
            license_no='LIC-ALLOC',
            software=self.software,
            total_units=5,
            purchase_date='2026-01-01',
            created_by=self.user
        )

        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='PC',
            name='Computer'
        )

        self.asset = Asset.objects.create(
            organization=self.org,
            asset_code='PC001',
            asset_name='Test PC',
            asset_category=self.category,
            purchase_price=5000,
            purchase_date='2026-01-01',
            created_by=self.user
        )

    def test_create_allocation(self):
        """Test creating allocation via API"""
        url = '/api/software-licenses/license-allocations/'
        data = {
            'license': str(self.license.id),
            'asset': str(self.asset.id),
            'notes': 'Test allocation'
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['data']['software_name'], 'Office 365')

        # Verify license usage increased
        self.license.refresh_from_db()
        self.assertEqual(self.license.used_units, 1)

    def test_deallocate_action(self):
        """Test deallocate action"""
        # First create allocation
        allocation = LicenseAllocation.objects.create(
            organization=self.org,
            license=self.license,
            asset=self.asset,
            allocated_by=self.user,
            created_by=self.user
        )

        url = f'/api/software-licenses/license-allocations/{allocation.id}/deallocate/'
        response = self.client.post(url, {'notes': 'No longer needed'})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['success'], True)

        # Verify license usage decreased
        self.license.refresh_from_db()
        self.assertEqual(self.license.used_units, 0)

    def test_no_availablelicenses_error(self):
        """Test allocation when no licenses available"""
        # Use up all licenses
        self.license.used_units = self.license.total_units
        self.license.save()

        url = '/api/software-licenses/license-allocations/'
        data = {
            'license': str(self.license.id),
            'asset': str(self.asset.id)
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error']['code'], 'NO_AVAILABLE_LICENSES')
```

**Step 2: Run tests**

```bash
cd backend
pytest apps/software_licenses/tests/test_viewsets.py -v
```

Expected: All tests PASS

**Step 3: Commit**

```bash
git add backend/apps/software_licenses/tests/test_viewsets.py
git commit -m "test(software-licenses): add API viewset tests"
```

---

## Phase 5: Frontend - API Layer (1h)

### Task 5.1: Create TypeScript API module

**Files:**
- Create: `frontend/src/api/softwareLicenses.ts`
- Create: `frontend/src/types/softwareLicenses.ts`

**Step 1: Write type definitions**

```typescript
// frontend/src/types/softwareLicenses.ts

/**
 * Software License Management Types
 */

export interface Software {
  id: string
  organization: any
  code: string
  name: string
  version: string
  vendor: string
  softwareType: 'os' | 'office' | 'professional' | 'development' | 'security' | 'database' | 'other'
  licenseType: string
  category?: any
  isActive: boolean
  isDeleted: boolean
  createdAt: string
  updatedAt: string
  createdBy: any
  customFields?: Record<string, any>
}

export interface SoftwareLicense {
  id: string
  organization: any
  licenseNo: string
  software: string
  softwareName?: string
  softwareVersion?: string
  licenseKey?: string
  totalUnits: number
  usedUnits: number
  availableUnits?: number
  utilizationRate?: number
  purchaseDate: string
  expiryDate?: string
  isExpired?: boolean
  purchasePrice?: number
  annualCost?: number
  status: 'active' | 'expired' | 'suspended' | 'revoked'
  licenseType: string
  agreementNo?: string
  vendor?: any
  notes?: string
  isDeleted: boolean
  createdAt: string
  updatedAt: string
  createdBy: any
  customFields?: Record<string, any>
}

export interface LicenseAllocation {
  id: string
  organization: any
  license: string
  softwareName?: string
  licenseNo?: string
  asset: string
  assetName?: string
  assetCode?: string
  allocatedDate: string
  allocatedBy?: string
  allocatedByName?: string
  allocationKey?: string
  deallocatedDate?: string
  deallocatedBy?: string
  deallocatedByName?: string
  isActive: boolean
  notes?: string
  isDeleted: boolean
  createdAt: string
  updatedAt: string
  createdBy: any
  customFields?: Record<string, any>
}

export interface ComplianceReport {
  totalLicenses: number
  expiringLicenses: number
  overUtilized: Array<{
    id: string
    licenseNo: string
    software: string
    utilization: number
  }>
}
```

**Step 2: Write API service**

```typescript
// frontend/src/api/softwareLicenses.ts

/**
 * Software Licenses API Service
 *
 * API methods for software catalog, licenses, and allocations.
 */

import request from '@/utils/request'
import type { PaginatedResponse, BatchResponse } from '@/types/api'
import type { Software, SoftwareLicense, LicenseAllocation, ComplianceReport } from '@/types/softwareLicenses'

/**
 * Software Catalog API
 */
export const softwareApi = {
  /**
   * List software catalog with pagination and filters
   */
  list(params?: {
    page?: number
    pageSize?: number
    softwareType?: string
    vendor?: string
    isActive?: boolean
    search?: string
  }): Promise<PaginatedResponse<Software>> {
    return request.get('/software-licenses/software/', { params })
  },

  /**
   * Get single software by ID
   */
  get(id: string): Promise<Software> {
    return request.get(`/software-licenses/software/${id}/`)
  },

  /**
   * Create new software entry
   */
  create(data: Partial<Software>): Promise<Software> {
    return request.post('/software-licenses/software/', data)
  },

  /**
   * Update software
   */
  update(id: string, data: Partial<Software>): Promise<Software> {
    return request.put(`/software-licenses/software/${id}/`, data)
  },

  /**
   * Delete software (soft delete)
   */
  delete(id: string): Promise<void> {
    return request.delete(`/software-licenses/software/${id}/`)
  },

  /**
   * Batch delete software
   */
  batchDelete(ids: string[]): Promise<BatchResponse> {
    return request.post('/software-licenses/software/batch-delete/', { ids })
  }
}

/**
 * Software Licenses API
 */
export const softwareLicenseApi = {
  /**
   * List software licenses with pagination and filters
   */
  list(params?: {
    page?: number
    pageSize?: number
    software?: string
    status?: string
    expiringSoon?: boolean
    search?: string
  }): Promise<PaginatedResponse<SoftwareLicense>> {
    return request.get('/software-licenses/licenses/', { params })
  },

  /**
   * Get single license by ID
   */
  get(id: string): Promise<SoftwareLicense> {
    return request.get(`/software-licenses/licenses/${id}/`)
  },

  /**
   * Create new license
   */
  create(data: Partial<SoftwareLicense>): Promise<SoftwareLicense> {
    return request.post('/software-licenses/licenses/', data)
  },

  /**
   * Update license
   */
  update(id: string, data: Partial<SoftwareLicense>): Promise<SoftwareLicense> {
    return request.put(`/software-licenses/licenses/${id}/`, data)
  },

  /**
   * Delete license (soft delete)
   */
  delete(id: string): Promise<void> {
    return request.delete(`/software-licenses/licenses/${id}/`)
  },

  /**
   * Get licenses expiring within 30 days
   */
  expiring(params?: {
    page?: number
    pageSize?: number
  }): Promise<PaginatedResponse<SoftwareLicense>> {
    return request.get('/software-licenses/licenses/expiring/', { params })
  },

  /**
   * Get compliance report
   */
  complianceReport(): Promise<{ data: ComplianceReport }> {
    return request.get('/software-licenses/licenses/compliance-report/')
  },

  /**
   * Batch delete licenses
   */
  batchDelete(ids: string[]): Promise<BatchResponse> {
    return request.post('/software-licenses/licenses/batch-delete/', { ids })
  }
}

/**
 * License Allocations API
 */
export const licenseAllocationApi = {
  /**
   * List allocations with pagination and filters
   */
  list(params?: {
    page?: number
    pageSize?: number
    license?: string
    asset?: string
    isActive?: boolean
    search?: string
  }): Promise<PaginatedResponse<LicenseAllocation>> {
    return request.get('/software-licenses/license-allocations/', { params })
  },

  /**
   * Get single allocation by ID
   */
  get(id: string): Promise<LicenseAllocation> {
    return request.get(`/software-licenses/license-allocations/${id}/`)
  },

  /**
   * Create allocation (assign license to asset)
   */
  create(data: {
    license: string
    asset: string
    allocationKey?: string
    notes?: string
  }): Promise<LicenseAllocation> {
    return request.post('/software-licenses/license-allocations/', data)
  },

  /**
   * Update allocation
   */
  update(id: string, data: Partial<LicenseAllocation>): Promise<LicenseAllocation> {
    return request.put(`/software-licenses/license-allocations/${id}/`, data)
  },

  /**
   * Delete allocation
   */
  delete(id: string): Promise<void> {
    return request.delete(`/software-licenses/license-allocations/${id}/`)
  },

  /**
   * Deallocate license from asset
   */
  deallocate(id: string, data?: { notes?: string }): Promise<{ data: LicenseAllocation }> {
    return request.post(`/software-licenses/license-allocations/${id}/deallocate/`, data)
  },

  /**
   * Batch delete allocations
   */
  batchDelete(ids: string[]): Promise<BatchResponse> {
    return request.post('/software-licenses/license-allocations/batch-delete/', { ids })
  }
}

// Re-export types
export type { Software, SoftwareLicense, LicenseAllocation, ComplianceReport }
```

**Step 3: Commit**

```bash
git add frontend/src/api/softwareLicenses.ts frontend/src/types/softwareLicenses.ts
git commit -m "feat(software-licenses): add TypeScript API service and type definitions"
```

---

## Phase 6: Frontend - Components and Pages (6h)

### Task 6.1: Create Software Catalog page

**Files:**
- Create: `frontend/src/views/softwareLicenses/SoftwareCatalog.vue`
- Create: `frontend/src/views/softwareLicenses/SoftwareForm.vue`

**Step 1: Create Software Catalog list page**

```vue
<!-- frontend/src/views/softwareLicenses/SoftwareCatalog.vue -->

<template>
  <BaseListPage
    title="软件目录"
    :api="softwareApi.list"
    :table-columns="columns"
    :search-fields="searchFields"
    :batch-actions="batchActions"
    @row-click="handleRowClick"
  >
    <template #toolbar>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        新建软件
      </el-button>
    </template>
    <template #softwareType="{ row }">
      <el-tag :type="getSoftwareTypeColor(row.softwareType)">
        {{ getSoftwareTypeLabel(row.softwareType) }}
      </el-tag>
    </template>
    <template #isActive="{ row }">
      <el-tag :type="row.isActive ? 'success' : 'info'">
        {{ row.isActive ? '启用' : '停用' }}
      </el-tag>
    </template>
    <template #actions="{ row }">
      <el-button link type="primary" @click.stop="handleEdit(row)">编辑</el-button>
      <el-button link type="primary" @click.stop="handleViewLicenses(row)">许可证</el-button>
    </template>
  </BaseListPage>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { softwareApi } from '@/api/softwareLicenses'
import type { TableColumn, SearchField } from '@/types/common'
import { Plus } from '@element-plus/icons-vue'

const router = useRouter()

const columns: TableColumn[] = [
  { prop: 'code', label: '代码', width: 120 },
  { prop: 'name', label: '软件名称', minWidth: 180 },
  { prop: 'version', label: '版本', width: 100 },
  { prop: 'vendor', label: '厂商', width: 150 },
  { prop: 'softwareType', label: '类型', width: 120, slot: true },
  { prop: 'isActive', label: '状态', width: 100, slot: true },
  { prop: 'actions', label: '操作', width: 150, slot: true, fixed: 'right' }
]

const searchFields: SearchField[] = [
  { prop: 'search', label: '搜索', placeholder: '代码/名称/厂商' },
  { prop: 'softwareType', label: '类型', type: 'select', options: [
    { label: '操作系统', value: 'os' },
    { label: '办公软件', value: 'office' },
    { label: '专业软件', value: 'professional' },
    { label: '开发工具', value: 'development' },
    { label: '安全软件', value: 'security' },
    { label: '数据库', value: 'database' },
    { label: '其他', value: 'other' }
  ]},
  { prop: 'isActive', label: '状态', type: 'select', options: [
    { label: '启用', value: true },
    { label: '停用', value: false }
  ]}
]

const batchActions = [
  {
    label: '批量删除',
    type: 'danger' as const,
    action: async (selectedRows: any[]) => {
      const ids = selectedRows.map(row => row.id)
      await softwareApi.batchDelete(ids)
    },
    confirm: true,
    confirmMessage: '确定要删除选中的软件吗？'
  }
]

const getSoftwareTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    os: '操作系统',
    office: '办公软件',
    professional: '专业软件',
    development: '开发工具',
    security: '安全软件',
    database: '数据库',
    other: '其他'
  }
  return labels[type] || type
}

const getSoftwareTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    os: 'primary',
    office: 'success',
    professional: 'warning',
    development: 'info',
    security: 'danger',
    database: '',
    other: 'info'
  }
  return colors[type] || ''
}

const handleRowClick = (row: any) => {
  // Navigate to detail or edit
}

const handleCreate = () => {
  router.push('/software-licenses/software/create')
}

const handleEdit = (row: any) => {
  router.push(`/software-licenses/software/${row.id}/edit`)
}

const handleViewLicenses = (row: any) => {
  router.push(`/software-licenses/licenses?software=${row.code}`)
}
</script>
```

**Step 2: Create Software Form page**

```vue
<!-- frontend/src/views/softwareLicenses/SoftwareForm.vue -->

<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>{{ isEdit ? '编辑软件' : '新建软件' }}</span>
        <el-button @click="handleBack">返回</el-button>
      </div>
    </template>

    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
      @submit.prevent="handleSubmit"
    >
      <el-form-item label="软件代码" prop="code">
        <el-input
          v-model="formData.code"
          placeholder="如: WIN11, OFF365"
          :disabled="isEdit"
        />
      </el-form-item>

      <el-form-item label="软件名称" prop="name">
        <el-input v-model="formData.name" placeholder="软件产品名称" />
      </el-form-item>

      <el-form-item label="版本" prop="version">
        <el-input v-model="formData.version" placeholder="如: 2021, Pro, 22H2" />
      </el-form-item>

      <el-form-item label="厂商" prop="vendor">
        <el-input v-model="formData.vendor" placeholder="软件厂商" />
      </el-form-item>

      <el-form-item label="软件类型" prop="softwareType">
        <el-select v-model="formData.softwareType" placeholder="选择类型">
          <el-option label="操作系统" value="os" />
          <el-option label="办公软件" value="office" />
          <el-option label="专业软件" value="professional" />
          <el-option label="开发工具" value="development" />
          <el-option label="安全软件" value="security" />
          <el-option label="数据库" value="database" />
          <el-option label="其他" value="other" />
        </el-select>
      </el-form-item>

      <el-form-item label="许可类型" prop="licenseType">
        <el-input v-model="formData.licenseType" placeholder="如: perpetual, subscription, OEM" />
      </el-form-item>

      <el-form-item label="状态" prop="isActive">
        <el-switch v-model="formData.isActive" active-text="启用" inactive-text="停用" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" native-type="submit" :loading="submitting">
          保存
        </el-button>
        <el-button @click="handleBack">取消</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { softwareApi } from '@/api/softwareLicenses'
import type { Software } from '@/types/softwareLicenses'

const router = useRouter()
const route = useRoute()
const formRef = ref<FormInstance>()
const submitting = ref(false)

const isEdit = computed(() => !!route.params.id)

const formData = ref<Partial<Software>>({
  code: '',
  name: '',
  version: '',
  vendor: '',
  softwareType: 'other',
  licenseType: '',
  isActive: true
})

const rules: FormRules = {
  code: [
    { required: true, message: '请输入软件代码', trigger: 'blur' },
    { pattern: /^[A-Z0-9_]+$/, message: '代码只能包含大写字母、数字和下划线', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入软件名称', trigger: 'blur' }
  ],
  softwareType: [
    { required: true, message: '请选择软件类型', trigger: 'change' }
  ]
}

const loadSoftware = async () => {
  const id = route.params.id as string
  try {
    const data = await softwareApi.get(id)
    formData.value = data
  } catch (error) {
    ElMessage.error('加载软件信息失败')
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEdit.value) {
        await softwareApi.update(route.params.id as string, formData.value)
        ElMessage.success('更新成功')
      } else {
        await softwareApi.create(formData.value)
        ElMessage.success('创建成功')
      }
      handleBack()
    } catch (error: any) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

const handleBack = () => {
  router.back()
}

onMounted(() => {
  if (isEdit.value) {
    loadSoftware()
  }
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
```

**Step 3: Commit**

```bash
git add frontend/src/views/softwareLicenses/SoftwareCatalog.vue frontend/src/views/softwareLicenses/SoftwareForm.vue
git commit -m "feat(software-licenses): add Software Catalog list and form pages"
```

---

### Task 6.2: Create Software Licenses page

**Files:**
- Create: `frontend/src/views/softwareLicenses/SoftwareLicenseList.vue`
- Create: `frontend/src/views/softwareLicenses/SoftwareLicenseForm.vue`
- Create: `frontend/src/components/softwareLicenses/AllocationDialog.vue`

**Step 1: Create Licenses list page with compliance panel**

```vue
<!-- frontend/src/views/softwareLicenses/SoftwareLicenseList.vue -->

<template>
  <div class="software-license-page">
    <el-row :gutter="20">
      <!-- License List -->
      <el-col :span="16">
        <BaseListPage
          title="软件许可证"
          :api="softwareLicenseApi.list"
          :table-columns="columns"
          :search-fields="searchFields"
          :batch-actions="batchActions"
          @row-click="handleRowClick"
        >
          <template #toolbar>
            <el-button type="primary" @click="handleCreate">
              <el-icon><Plus /></el-icon>
              新建许可证
            </el-button>
            <el-button @click="loadComplianceReport">
              <el-icon><Refresh /></el-icon>
              刷新统计
            </el-button>
          </template>
          <template #utilization="{ row }">
            <el-progress
              :percentage="Math.round(row.utilizationRate || 0)"
              :status="getUtilizationStatus(row.utilizationRate)"
              :stroke-width="8"
            />
          </template>
          <template #expiry="{ row }">
            <el-tag v-if="!row.expiryDate" type="success">永久</el-tag>
            <el-tag v-else-if="row.isExpired" type="danger">已过期</el-tag>
            <el-tag v-else-if="isExpiringSoon(row.expiryDate)" type="warning">
              {{ formatDate(row.expiryDate) }}
            </el-tag>
            <el-tag v-else type="info">{{ formatDate(row.expiryDate) }}</el-tag>
          </template>
          <template #status="{ row }">
            <el-tag :type="getStatusColor(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
          <template #actions="{ row }">
            <el-button link type="primary" @click.stop="handleEdit(row)">编辑</el-button>
            <el-button link type="primary" @click.stop="handleAllocate(row)">分配</el-button>
          </template>
        </BaseListPage>
      </el-col>

      <!-- Compliance Panel -->
      <el-col :span="8">
        <el-card shadow="hover" class="compliance-card">
          <template #header>
            <span>合规概览</span>
          </template>
          <div v-loading="loadingCompliance">
            <el-statistic title="许可证总数" :value="complianceData.totalLicenses" />
            <el-divider />
            <el-statistic title="即将过期" :value="complianceData.expiringLicenses">
              <template #suffix>
                <el-text type="warning" size="small">30天内</el-text>
              </template>
            </el-statistic>
            <el-divider />
            <div class="over-utilized-section">
              <div class="section-title">过度分配</div>
              <el-tag
                v-for="item in complianceData.overUtilized"
                :key="item.id"
                type="danger"
                size="small"
                class="over-tag"
              >
                {{ item.software }}: {{ item.utilization }}%
              </el-tag>
              <el-text v-if="complianceData.overUtilized.length === 0" type="success" size="small">
                无过度分配
              </el-text>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Allocation Dialog -->
    <AllocationDialog
      v-model="allocationDialogVisible"
      :license="selectedLicense"
      @allocated="handleAllocated"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import BaseListPage from '@/components/common/BaseListPage.vue'
import AllocationDialog from '@/components/softwareLicenses/AllocationDialog.vue'
import { softwareLicenseApi } from '@/api/softwareLicenses'
import type { TableColumn, SearchField } from '@/types/common'
import type { SoftwareLicense, ComplianceReport } from '@/types/softwareLicenses'
import { Plus, Refresh } from '@element-plus/icons-vue'

const router = useRouter()

const columns: TableColumn[] = [
  { prop: 'licenseNo', label: '许可证编号', width: 150 },
  { prop: 'softwareName', label: '软件名称', minWidth: 150 },
  { prop: 'totalUnits', label: '总数量', width: 100, align: 'right' },
  { prop: 'usedUnits', label: '已用', width: 80, align: 'right' },
  { prop: 'availableUnits', label: '可用', width: 80, align: 'right' },
  { prop: 'utilization', label: '使用率', width: 150, slot: true },
  { prop: 'expiry', label: '到期日', width: 120, slot: true },
  { prop: 'status', label: '状态', width: 100, slot: true },
  { prop: 'actions', label: '操作', width: 150, slot: true, fixed: 'right' }
]

const searchFields: SearchField[] = [
  { prop: 'search', label: '搜索', placeholder: '许可证号/软件名称' },
  { prop: 'status', label: '状态', type: 'select', options: [
    { label: '生效中', value: 'active' },
    { label: '已过期', value: 'expired' },
    { label: '暂停', value: 'suspended' },
    { label: '撤销', value: 'revoked' }
  ]},
  { prop: 'expiringSoon', label: '即将过期', type: 'boolean' }
]

const batchActions = [
  {
    label: '批量删除',
    type: 'danger' as const,
    action: async (selectedRows: any[]) => {
      const ids = selectedRows.map(row => row.id)
      await softwareLicenseApi.batchDelete(ids)
    },
    confirm: true,
    confirmMessage: '确定要删除选中的许可证吗？'
  }
]

const complianceData = ref<ComplianceReport>({
  totalLicenses: 0,
  expiringLicenses: 0,
  overUtilized: []
})
const loadingCompliance = ref(false)
const allocationDialogVisible = ref(false)
const selectedLicense = ref<SoftwareLicense | null>(null)

const getUtilizationStatus = (rate?: number) => {
  if (!rate) return undefined
  if (rate > 100) return 'exception'
  if (rate > 90) return 'warning'
  return 'success'
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('zh-CN')
}

const isExpiringSoon = (date: string) => {
  const days = Math.ceil((new Date(date).getTime() - Date.now()) / (1000 * 60 * 60 * 24))
  return days <= 30 && days >= 0
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    active: '生效中',
    expired: '已过期',
    suspended: '暂停',
    revoked: '撤销'
  }
  return labels[status] || status
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    active: 'success',
    expired: 'danger',
    suspended: 'warning',
    revoked: 'info'
  }
  return colors[status] || ''
}

const loadComplianceReport = async () => {
  loadingCompliance.value = true
  try {
    const response = await softwareLicenseApi.complianceReport()
    complianceData.value = response.data
  } catch (error) {
    console.error('Failed to load compliance report:', error)
  } finally {
    loadingCompliance.value = false
  }
}

const handleRowClick = (row: any) => {
  // Navigate to detail or edit
}

const handleCreate = () => {
  router.push('/software-licenses/licenses/create')
}

const handleEdit = (row: any) => {
  router.push(`/software-licenses/licenses/${row.id}/edit`)
}

const handleAllocate = (row: any) => {
  selectedLicense.value = row
  allocationDialogVisible.value = true
}

const handleAllocated = () => {
  // Refresh list after allocation
  loadComplianceReport()
}

onMounted(() => {
  loadComplianceReport()
})
</script>

<style scoped>
.software-license-page {
  padding: 20px;
}

.compliance-card {
  position: sticky;
  top: 20px;
}

.over-utilized-section {
  max-height: 300px;
  overflow-y: auto;
}

.section-title {
  font-weight: 500;
  margin-bottom: 10px;
  color: var(--el-text-color-primary);
}

.over-tag {
  margin: 5px 5px 5px 0;
}
</style>
```

**Step 2: Create License Form page**

```vue
<!-- frontend/src/views/softwareLicenses/SoftwareLicenseForm.vue -->

<template>
  <el-card>
    <template #header>
      <div class="card-header">
        <span>{{ isEdit ? '编辑许可证' : '新建许可证' }}</span>
        <el-button @click="handleBack">返回</el-button>
      </div>
    </template>

    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="140px"
      @submit.prevent="handleSubmit"
    >
      <el-form-item label="许可证编号" prop="licenseNo">
        <el-input
          v-model="formData.licenseNo"
          placeholder="如: OFF365-2024-001"
          :disabled="isEdit"
        />
      </el-form-item>

      <el-form-item label="软件" prop="software">
        <el-select
          v-model="formData.software"
          filterable
          placeholder="选择软件"
          style="width: 100%"
        >
          <el-option
            v-for="item in softwareOptions"
            :key="item.id"
            :label="`${item.name} ${item.version}`"
            :value="item.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="许可证密钥" prop="licenseKey">
        <el-input
          v-model="formData.licenseKey"
          type="password"
          show-password
          placeholder="可选，加密存储"
        />
      </el-form-item>

      <el-divider>许可数量</el-divider>

      <el-form-item label="总许可数" prop="totalUnits">
        <el-input-number v-model="formData.totalUnits" :min="1" :max="10000" />
      </el-form-item>

      <el-form-item label="已使用数">
        <el-input-number v-model="formData.usedUnits" :min="0" disabled />
        <el-text size="small" type="info">系统自动更新</el-text>
      </el-form-item>

      <el-divider>许可期限</el-divider>

      <el-form-item label="购买日期" prop="purchaseDate">
        <el-date-picker
          v-model="formData.purchaseDate"
          type="date"
          placeholder="选择日期"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>

      <el-form-item label="到期日期">
        <el-date-picker
          v-model="formData.expiryDate"
          type="date"
          placeholder="留空表示永久许可"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>

      <el-divider>财务信息</el-divider>

      <el-form-item label="购买价格">
        <el-input-number v-model="formData.purchasePrice" :min="0" :precision="2" />
        <span style="margin-left: 10px">元</span>
      </el-form-item>

      <el-form-item label="年维护成本">
        <el-input-number v-model="formData.annualCost" :min="0" :precision="2" />
        <span style="margin-left: 10px">元/年</span>
      </el-form-item>

      <el-divider>状态信息</el-divider>

      <el-form-item label="状态" prop="status">
        <el-select v-model="formData.status">
          <el-option label="生效中" value="active" />
          <el-option label="已过期" value="expired" />
          <el-option label="暂停" value="suspended" />
          <el-option label="撤销" value="revoked" />
        </el-select>
      </el-form-item>

      <el-form-item label="许可类型">
        <el-input v-model="formData.licenseType" placeholder="如: perpetual, subscription, OEM, volume" />
      </el-form-item>

      <el-form-item label="协议编号">
        <el-input v-model="formData.agreementNo" placeholder="企业协议编号" />
      </el-form-item>

      <el-form-item label="备注">
        <el-input
          v-model="formData.notes"
          type="textarea"
          :rows="3"
          placeholder="许可证相关备注"
        />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" native-type="submit" :loading="submitting">
          保存
        </el-button>
        <el-button @click="handleBack">取消</el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { softwareLicenseApi, softwareApi } from '@/api/softwareLicenses'
import type { SoftwareLicense, Software } from '@/types/softwareLicenses'

const router = useRouter()
const route = useRoute()
const formRef = ref<FormInstance>()
const submitting = ref(false)

const isEdit = computed(() => !!route.params.id)

const formData = ref<Partial<SoftwareLicense>>({
  licenseNo: '',
  software: '',
  licenseKey: '',
  totalUnits: 1,
  usedUnits: 0,
  purchaseDate: '',
  expiryDate: undefined,
  purchasePrice: undefined,
  annualCost: undefined,
  status: 'active',
  licenseType: '',
  agreementNo: '',
  notes: ''
})

const softwareOptions = ref<Software[]>([])

const rules: FormRules = {
  licenseNo: [
    { required: true, message: '请输入许可证编号', trigger: 'blur' }
  ],
  software: [
    { required: true, message: '请选择软件', trigger: 'change' }
  ],
  totalUnits: [
    { required: true, message: '请输入许可数量', trigger: 'blur' }
  ],
  purchaseDate: [
    { required: true, message: '请选择购买日期', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择状态', trigger: 'change' }
  ]
}

const loadSoftware = async () => {
  try {
    const response = await softwareApi.list({ pageSize: 1000 })
    softwareOptions.value = response.data.results || []
  } catch (error) {
    console.error('Failed to load software list:', error)
  }
}

const loadLicense = async () => {
  const id = route.params.id as string
  try {
    const data = await softwareLicenseApi.get(id)
    formData.value = data
  } catch (error) {
    ElMessage.error('加载许可证信息失败')
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      if (isEdit.value) {
        await softwareLicenseApi.update(route.params.id as string, formData.value)
        ElMessage.success('更新成功')
      } else {
        await softwareLicenseApi.create(formData.value)
        ElMessage.success('创建成功')
      }
      handleBack()
    } catch (error: any) {
      ElMessage.error(error.message || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

const handleBack = () => {
  router.back()
}

onMounted(() => {
  loadSoftware()
  if (isEdit.value) {
    loadLicense()
  }
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
```

**Step 3: Create Allocation Dialog component**

```vue
<!-- frontend/src/components/softwareLicenses/AllocationDialog.vue -->

<template>
  <el-dialog
    v-model="visible"
    :title="`分配许可证 - ${license?.softwareName}`"
    width="600px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="120px"
    >
      <el-form-item label="可用数量">
        <el-text>{{ license?.availableUnits }} / {{ license?.totalUnits }}</el-text>
      </el-form-item>

      <el-form-item label="资产" prop="asset">
        <el-select
          v-model="formData.asset"
          filterable
          remote
          :remote-method="searchAssets"
          placeholder="搜索资产编码或名称"
          style="width: 100%"
          :loading="searching"
        >
          <el-option
            v-for="item in assetOptions"
            :key="item.id"
            :label="`${item.assetCode} - ${item.assetName}`"
            :value="item.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="分配密钥">
        <el-input
          v-model="formData.allocationKey"
          type="password"
          show-password
          placeholder="可选，特定于此分配的密钥"
        />
      </el-form-item>

      <el-form-item label="备注">
        <el-input
          v-model="formData.notes"
          type="textarea"
          :rows="3"
          placeholder="分配备注"
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        分配
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { licenseAllocationApi } from '@/api/softwareLicenses'
import { assetApi } from '@/api/assets'
import type { SoftwareLicense } from '@/types/softwareLicenses'

interface Props {
  modelValue: boolean
  license?: SoftwareLicense | null
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'allocated'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const formRef = ref<FormInstance>()
const submitting = ref(false)
const searching = ref(false)
const assetOptions = ref<any[]>([])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const formData = ref({
  asset: '',
  allocationKey: '',
  notes: ''
})

const rules: FormRules = {
  asset: [
    { required: true, message: '请选择资产', trigger: 'change' }
  ]
}

const searchAssets = async (query: string) => {
  if (!query) return

  searching.value = true
  try {
    const response = await assetApi.list({ search: query, pageSize: 50 })
    assetOptions.value = response.data.results || []
  } catch (error) {
    console.error('Failed to search assets:', error)
  } finally {
    searching.value = false
  }
}

const handleSubmit = async () => {
  if (!formRef.value || !props.license) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    submitting.value = true
    try {
      await licenseAllocationApi.create({
        license: props.license.id,
        asset: formData.value.asset,
        allocationKey: formData.value.allocationKey || undefined,
        notes: formData.value.notes || undefined
      })
      ElMessage.success('分配成功')
      emit('allocated')
      handleClose()
    } catch (error: any) {
      ElMessage.error(error.message || '分配失败')
    } finally {
      submitting.value = false
    }
  })
}

const handleClose = () => {
  formRef.value?.resetFields()
  formData.value = {
    asset: '',
    allocationKey: '',
    notes: ''
  }
  assetOptions.value = []
  visible.value = false
}
</script>
```

**Step 4: Commit**

```bash
git add frontend/src/views/softwareLicenses/SoftwareLicenseList.vue frontend/src/views/softwareLicenses/SoftwareLicenseForm.vue frontend/src/components/softwareLicenses/AllocationDialog.vue
git commit -m "feat(software-licenses): add License list, form pages and Allocation dialog"
```

---

### Task 6.3: Create Allocation List page

**Files:**
- Create: `frontend/src/views/softwareLicenses/AllocationList.vue`

**Step 1: Create Allocation List page**

```vue
<!-- frontend/src/views/softwareLicenses/AllocationList.vue -->

<template>
  <BaseListPage
    title="许可证分配记录"
    :api="licenseAllocationApi.list"
    :table-columns="columns"
    :search-fields="searchFields"
    @row-click="handleRowClick"
  >
    <template #toolbar>
      <el-button type="primary" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        新建分配
      </el-button>
    </template>
    <template #isActive="{ row }">
      <el-tag :type="row.isActive ? 'success' : 'info'">
        {{ row.isActive ? '已分配' : '已解除' }}
      </el-tag>
    </template>
    <template #actions="{ row }">
      <el-button
        v-if="row.isActive"
        link
        type="warning"
        @click.stop="handleDeallocate(row)"
      >
        解除分配
      </el-button>
      <el-text v-else type="info">已解除</el-text>
    </template>
  </BaseListPage>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import BaseListPage from '@/components/common/BaseListPage.vue'
import { licenseAllocationApi } from '@/api/softwareLicenses'
import type { TableColumn, SearchField } from '@/types/common'
import { Plus } from '@element-plus/icons-vue'

const router = useRouter()

const columns: TableColumn[] = [
  { prop: 'softwareName', label: '软件', minWidth: 150 },
  { prop: 'licenseNo', label: '许可证编号', width: 150 },
  { prop: 'assetCode', label: '资产编码', width: 130 },
  { prop: 'assetName', label: '资产名称', minWidth: 150 },
  { prop: 'allocatedDate', label: '分配日期', width: 120 },
  { prop: 'allocatedByName', label: '分配人', width: 100 },
  { prop: 'isActive', label: '状态', width: 100, slot: true },
  { prop: 'actions', label: '操作', width: 120, slot: true, fixed: 'right' }
]

const searchFields: SearchField[] = [
  { prop: 'search', label: '搜索', placeholder: '软件/资产' },
  { prop: 'isActive', label: '状态', type: 'select', options: [
    { label: '已分配', value: true },
    { label: '已解除', value: false }
  ]}
]

const handleRowClick = (row: any) => {
  // Show detail dialog
}

const handleCreate = () => {
  router.push('/software-licenses/licenses')
}

const handleDeallocate = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要解除 ${row.softwareName} 在 ${row.assetName} 上的分配吗？`,
      '确认解除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await licenseAllocationApi.deallocate(row.id)
    ElMessage.success('解除成功')
    // Refresh is handled by BaseListPage
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '解除失败')
    }
  }
}
</script>
```

**Step 2: Commit**

```bash
git add frontend/src/views/softwareLicenses/AllocationList.vue
git commit -m "feat(software-licenses): add Allocation List page with deallocate action"
```

---

### Task 6.4: Configure routes

**Files:**
- Modify: `frontend/src/router/index.ts`

**Step 1: Add routes for software licenses**

```typescript
// Add to frontend/src/router/index.ts imports:

const SoftwareCatalog = () => import('@/views/softwareLicenses/SoftwareCatalog.vue')
const SoftwareLicenseList = () => import('@/views/softwareLicenses/SoftwareLicenseList.vue')
const SoftwareLicenseForm = () => import('@/views/softwareLicenses/SoftwareLicenseForm.vue')
const SoftwareForm = () => import('@/views/softwareLicenses/SoftwareForm.vue')
const AllocationList = () => import('@/views/softwareLicenses/AllocationList.vue')
```

```typescript
// Add to children array in MainLayout route:

{
  path: 'software-licenses',
  children: [
    {
      path: 'software',
      name: 'SoftwareCatalog',
      component: SoftwareCatalog,
      meta: { title: '软件目录' }
    },
    {
      path: 'software/create',
      name: 'SoftwareCreate',
      component: SoftwareForm,
      meta: { title: '新建软件' }
    },
    {
      path: 'software/:id/edit',
      name: 'SoftwareEdit',
      component: SoftwareForm,
      meta: { title: '编辑软件' }
    },
    {
      path: 'licenses',
      name: 'SoftwareLicenseList',
      component: SoftwareLicenseList,
      meta: { title: '软件许可证' }
    },
    {
      path: 'licenses/create',
      name: 'SoftwareLicenseCreate',
      component: SoftwareLicenseForm,
      meta: { title: '新建许可证' }
    },
    {
      path: 'licenses/:id/edit',
      name: 'SoftwareLicenseEdit',
      component: SoftwareLicenseForm,
      meta: { title: '编辑许可证' }
    },
    {
      path: 'allocations',
      name: 'LicenseAllocations',
      component: AllocationList,
      meta: { title: '分配记录' }
    }
  ]
}
```

**Step 2: Commit**

```bash
git add frontend/src/router/index.ts
git commit -m "feat(software-licenses): configure routes for all software license pages"
```

---

## Phase 7: Testing and Integration (2h)

### Task 7.1: Backend integration tests

**Files:**
- Create: `backend/apps/software_licenses/tests/test_integration.py`

**Step 1: Write integration tests**

```python
# backend/apps/software_licenses/tests/test_integration.py

import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from apps.software_licenses.models import Software, SoftwareLicense, LicenseAllocation
from apps.assets.models import Asset, AssetCategory
from apps.organizations.models import Organization
from apps.accounts.models import User


class SoftwareLicenseIntegrationTest(TestCase):
    """Software License Integration Tests"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.unique_suffix = "int9876"

        self.org = Organization.objects.create(
            name=f'Test Organization {self.unique_suffix}',
            code=f'TESTORG_{self.unique_suffix}'
        )
        self.user = User.objects.create_user(
            username=f'testuser_{self.unique_suffix}',
            email=f'test{self.unique_suffix}@example.com',
            organization=self.org
        )
        self.client.force_authenticate(user=self.user)

        self.software = Software.objects.create(
            organization=self.org,
            code='WIN11',
            name='Windows 11',
            created_by=self.user
        )

        self.category = AssetCategory.objects.create(
            organization=self.org,
            code='PC',
            name='Computer'
        )
        self.asset = Asset.objects.create(
            organization=self.org,
            asset_code='PC001',
            asset_name='Test PC',
            asset_category=self.category,
            purchase_price=5000,
            purchase_date='2026-01-01',
            created_by=self.user
        )

    def test_full_allocation_workflow(self):
        """Test full license allocation workflow"""
        # Create license
        license_response = self.client.post('/api/software-licenses/licenses/', {
            'license_no': 'LIC-WORKFLOW-001',
            'software': str(self.software.id),
            'total_units': 5,
            'purchase_date': '2026-01-01'
        })
        self.assertEqual(license_response.status_code, 201)
        license_id = license_response.data['data']['id']

        # Allocate to asset
        allocation_response = self.client.post('/api/software-licenses/license-allocations/', {
            'license': license_id,
            'asset': str(self.asset.id),
            'notes': 'Test allocation'
        })
        self.assertEqual(allocation_response.status_code, 201)

        # Verify license usage increased
        license_detail = self.client.get(f'/api/software-licenses/licenses/{license_id}/')
        self.assertEqual(license_detail.data['data']['used_units'], 1)

        # Deallocate
        dealloc_url = f"/api/software-licenses/license-allocations/{allocation_response.data['data']['id']}/deallocate/"
        dealloc_response = self.client.post(dealloc_url, {'notes': 'Test deallocation'})
        self.assertEqual(dealloc_response.status_code, 200)

        # Verify license usage decreased
        license_detail = self.client.get(f'/api/software-licenses/licenses/{license_id}/')
        self.assertEqual(license_detail.data['data']['used_units'], 0)

    def test_no_availablelicenses_error(self):
        """Test allocation when no licenses available"""
        # Create license with 1 unit
        license_response = self.client.post('/api/software-licenses/licenses/', {
            'license_no': 'LIC-NO-AVAIL-001',
            'software': str(self.software.id),
            'total_units': 1,
            'purchase_date': '2026-01-01'
        })
        license_id = license_response.data['data']['id']

        # Use up the license
        self.client.post('/api/software-licenses/license-allocations/', {
            'license': license_id,
            'asset': str(self.asset.id)
        })

        # Try to allocate again - should fail
        second_asset = Asset.objects.create(
            organization=self.org,
            asset_code='PC002',
            asset_name='Second PC',
            asset_category=self.category,
            purchase_price=4000,
            purchase_date='2026-01-01',
            created_by=self.user
        )

        error_response = self.client.post('/api/software-licenses/license-allocations/', {
            'license': license_id,
            'asset': str(second_asset.id)
        })
        self.assertEqual(error_response.status_code, 400)
        self.assertEqual(error_response.data['error']['code'], 'NO_AVAILABLE_LICENSES')

    def test_compliance_report_accuracy(self):
        """Test compliance report returns accurate data"""
        from django.utils import timezone
        from datetime import timedelta

        # Create various licenses
        SoftwareLicense.objects.create(
            organization=self.org,
            license_no='LIC-COMP-001',
            software=self.software,
            total_units=10,
            used_units=0,
            purchase_date='2026-01-01',
            status='active',
            created_by=self.user
        )

        SoftwareLicense.objects.create(
            organization=self.org,
            license_no='LIC-COMP-002',
            software=self.software,
            total_units=5,
            used_units=6,
            purchase_date='2026-01-01',
            status='active',
            created_by=self.user
        )

        SoftwareLicense.objects.create(
            organization=self.org,
            license_no='LIC-COMP-003',
            software=self.software,
            total_units=1,
            purchase_date='2026-01-01',
            expiry_date=timezone.now().date() + timedelta(days=15),
            status='active',
            created_by=self.user
        )

        response = self.client.get('/api/software-licenses/licenses/compliance-report/')

        self.assertEqual(response.status_code, 200)
        data = response.data['data']
        self.assertEqual(data['total_licenses'], 3)
        self.assertEqual(data['expiring_licenses'], 1)
        self.assertEqual(len(data['over_utilized']), 1)
        self.assertEqual(data['over_utilized'][0]['utilization'], 120.0)
```

**Step 2: Run integration tests**

```bash
cd backend
pytest apps/software_licenses/tests/test_integration.py -v
```

Expected: All tests PASS

**Step 3: Commit**

```bash
git add backend/apps/software_licenses/tests/test_integration.py
git commit -m "test(software-licenses): add integration tests for full allocation workflow"
```

---

### Task 7.2: Create conftest for shared fixtures

**Files:**
- Create: `backend/apps/software_licenses/tests/conftest.py`

**Step 1: Create pytest fixtures**

```python
# backend/apps/software_licenses/tests/conftest.py

import pytest
from apps.organizations.models import Organization
from apps.accounts.models import User
from apps.software_licenses.models import Software, SoftwareLicense
from apps.assets.models import Asset, AssetCategory


@pytest.fixture
def org(db):
    """Create test organization"""
    return Organization.objects.create(
        name='Test Organization',
        code='TESTORG'
    )


@pytest.fixture
def user(org):
    """Create test user"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        organization=org
    )


@pytest.fixture
def software(org, user):
    """Create test software"""
    return Software.objects.create(
        organization=org,
        code='TESTSOFT',
        name='Test Software',
        version='1.0',
        created_by=user
    )


@pytest.fixture
def software_license(org, user, software):
    """Create test software license"""
    return SoftwareLicense.objects.create(
        organization=org,
        license_no='LIC-TEST-001',
        software=software,
        total_units=10,
        used_units=0,
        purchase_date='2026-01-01',
        created_by=user
    )


@pytest.fixture
def asset_category(org):
    """Create test asset category"""
    return AssetCategory.objects.create(
        organization=org,
        code='PC',
        name='Computer'
    )


@pytest.fixture
def asset(org, user, asset_category):
    """Create test asset"""
    return Asset.objects.create(
        organization=org,
        asset_code='PC001',
        asset_name='Test PC',
        asset_category=asset_category,
        purchase_price=5000,
        purchase_date='2026-01-01',
        created_by=user
    )


@pytest.fixture
def api_client():
    """Create API client"""
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def auth_client(api_client, user):
    """Create authenticated API client"""
    api_client.force_authenticate(user=user)
    return api_client
```

**Step 2: Commit**

```bash
git add backend/apps/software_licenses/tests/conftest.py
git commit -m "test(software-licenses): add pytest fixtures for tests"
```

---

## Phase 8: Documentation and Cleanup (1h)

### Task 8.1: Create module README

**Files:**
- Create: `backend/apps/software_licenses/README.md`

**Step 1: Write module documentation**

```markdown
# Software Licenses Module

## Overview

Manages software catalog, licenses, and asset allocations for tracking software compliance.

## Models

- `Software`: Software catalog entries
- `SoftwareLicense`: License tracking with quantity management
- `LicenseAllocation`: Asset-to-license assignments

## API Endpoints

### Software Catalog
- `GET /api/software-licenses/software/` - List software
- `POST /api/software-licenses/software/` - Create software
- `GET /api/software-licenses/software/{id}/` - Get software
- `PUT /api/software-licenses/software/{id}/` - Update software
- `DELETE /api/software-licenses/software/{id}/` - Delete software

### Software Licenses
- `GET /api/software-licenses/licenses/` - List licenses
- `POST /api/software-licenses/licenses/` - Create license
- `GET /api/software-licenses/licenses/expiring/` - Get expiring licenses (30 days)
- `GET /api/software-licenses/licenses/compliance-report/` - Get compliance report

### License Allocations
- `GET /api/software-licenses/license-allocations/` - List allocations
- `POST /api/software-licenses/license-allocations/` - Create allocation
- `POST /api/software-licenses/license-allocations/{id}/deallocate/` - Deallocate

## Running Tests

```bash
cd backend
pytest apps/software_licenses/tests/
```
```

**Step 2: Commit**

```bash
git add backend/apps/software_licenses/README.md
git commit -m "docs(software-licenses): add module README"
```

---

### Task 8.2: Final integration check

**Files:** None (verification task)

**Step 1: Run all backend tests**

```bash
cd backend
pytest apps/software_licenses/tests/ -v --tb=short
```

Expected: All tests PASS

**Step 2: Check API URLs are registered**

```bash
cd backend
python manage.py show_urls 2>/dev/null | grep software-licenses || \
python manage.py shell -c "
from django.urls import get_resolver
resolver = get_resolver()
for pattern in resolver.url_patterns:
    if 'software' in str(pattern.pattern):
        print(pattern)
"
```

Expected output: URLs for software, licenses, license-allocations

**Step 3: Verify frontend routes exist**

Check that `frontend/src/router/index.ts` includes:
- SoftwareCatalog route
- SoftwareLicenseList route
- AllocationList route

**Step 4: Create summary report**

```bash
git log --oneline --since="2 hours ago" | head -20
```

Count commits to verify progress.

**Step 5: Final commit if needed**

```bash
git add -A
git commit -m "chore(software-licenses): final integration cleanup"
```

---

## Summary

This plan implements the Software License Management module in approximately 26 hours:

| Phase | Tasks | Duration |
|-------|-------|----------|
| 1 | Models and Migrations | 2h |
| 2 | Serializers and Filters | 2h |
| 3 | ViewSets and Services | 3h |
| 4 | Backend Tests | 2h |
| 5 | Frontend API Layer | 1h |
| 6 | Frontend Components | 6h |
| 7 | Integration Testing | 2h |
| 8 | Documentation | 1h |

**Total**: 19 hours of active development + buffer

---

## Checklist

Before marking complete, verify:

- [ ] All models inherit from BaseModel
- [ ] All serializers inherit from BaseModelSerializer
- [ ] All viewsets inherit from BaseModelViewSetWithBatch
- [ ] All filters inherit from BaseModelFilter
- [ ] All services inherit from BaseCRUDService
- [ ] Backend tests pass (pytest)
- [ ] Frontend API service uses request wrapper
- [ ] Frontend pages use BaseListPage component
- [ ] Routes configured in router/index.ts
- [ ] Module README created

---

**End of Implementation Plan**
