"""
Asset models for GZEAMS.
"""
from django.db import models
from django.core.validators import MinValueValidator
from apps.common.models import BaseModel


class AssetCategory(BaseModel):
    """
    Asset Category Model

    Supports hierarchical tree structure with parent-child relationships.
    System categories (is_custom=False) are predefined; users can create custom categories.
    """
    # Basic Information
    code = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Unique category code (e.g., '2001' for computer equipment)"
    )
    name = models.CharField(
        max_length=200,
        help_text="Category display name"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent category for tree structure"
    )
    full_name = models.CharField(
        max_length=500,
        editable=False,
        help_text="Full path name (e.g., 'Computer Equipment > Desktop')"
    )

    # Tree Structure
    level = models.IntegerField(
        default=0,
        editable=False,
        help_text="Tree level (0=root, 1=first child, ...)"
    )
    sort_order = models.IntegerField(
        default=0,
        help_text="Display order within same level"
    )

    # Category Type
    is_custom = models.BooleanField(
        default=False,
        help_text="True=user-created, False=system predefined"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Category status (can be deactivated without deletion)"
    )

    # Depreciation Configuration
    DEPRECIATION_METHODS = [
        ('straight_line', 'Straight Line Method'),
        ('double_declining', 'Double Declining Balance'),
        ('sum_of_years', 'Sum of Years Digits'),
        ('no_depreciation', 'No Depreciation'),
    ]
    depreciation_method = models.CharField(
        max_length=50,
        choices=DEPRECIATION_METHODS,
        default='straight_line'
    )
    default_useful_life = models.IntegerField(
        default=60,
        help_text="Default useful life in months"
    )
    residual_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5.00,
        help_text="Default residual value rate (%)"
    )

    class Meta:
        db_table = 'asset_category'
        verbose_name = 'Asset Category'
        verbose_name_plural = 'Asset Categories'
        ordering = ['sort_order', 'code']
        indexes = [
            models.Index(fields=['organization', 'code']),
            models.Index(fields=['organization', 'parent']),
            models.Index(fields=['organization', 'is_deleted', 'is_active']),
        ]

    def __str__(self):
        return f"{self.code} - {self.full_name}"

    def save(self, *args, **kwargs):
        # Auto-calculate level and full_name before saving
        if self.parent:
            self.level = self.parent.level + 1
            self.full_name = f"{self.parent.full_name} > {self.name}"
        else:
            self.level = 0
            self.full_name = self.name
        super().save(*args, **kwargs)

    @classmethod
    def get_tree(cls, organization_id):
        """
        Get category tree for an organization.

        Returns hierarchical tree structure with nested children.
        Includes is_leaf and asset_count for each category.
        """
        categories = cls.objects.filter(
            organization_id=organization_id,
            is_deleted=False
        ).order_by('sort_order', 'code')

        # Build tree structure
        from collections import defaultdict
        children_map = defaultdict(list)
        root_categories = []

        for cat in categories:
            if cat.parent_id:
                children_map[cat.parent_id].append(cat)
            else:
                root_categories.append(cat)

        def build_tree(category):
            """Recursively build tree with children."""
            # Get children for this category
            children = children_map.get(category.id, [])

            # Count assets in this category (non-deleted only)
            asset_count = category.assets.filter(is_deleted=False).count()

            data = {
                'id': category.id,
                'code': category.code,
                'name': category.name,
                'full_name': category.full_name,
                'level': category.level,
                'is_custom': category.is_custom,
                'depreciation_method': category.depreciation_method,
                'default_useful_life': category.default_useful_life,
                'residual_rate': category.residual_rate,
                'sort_order': category.sort_order,
                'is_active': category.is_active,
                'is_leaf': len(children) == 0,  # True if no children
                'asset_count': asset_count,  # Count of assets in this category
                'children': []
            }
            # Add children recursively
            for child in children:
                data['children'].append(build_tree(child))
            return data

        return [build_tree(cat) for cat in root_categories]

    def can_delete(self):
        """
        Check if category can be deleted (no children, no assets).
        """
        has_children = self.children.filter(is_deleted=False).exists()
        # TODO: Check for assets when Asset model is implemented
        return not has_children


class Supplier(BaseModel):
    """
    Supplier Model

    Inherits from BaseModel, automatically gets organization isolation
    and soft delete functionality.
    """
    class Meta:
        db_table = 'suppliers'
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'
        indexes = [
            models.Index(fields=['organization', 'code']),
        ]

    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Unique supplier code'
    )
    name = models.CharField(
        max_length=200,
        help_text='Supplier name'
    )
    contact = models.CharField(
        max_length=100,
        blank=True,
        help_text='Contact person'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text='Contact phone'
    )
    email = models.EmailField(
        blank=True,
        help_text='Contact email'
    )
    address = models.TextField(
        blank=True,
        help_text='Supplier address'
    )

    def __str__(self):
        return f"{self.code} - {self.name}"


class Location(BaseModel):
    """
    Location (Storage Place) Model

    Inherits from BaseModel, supports tree structure for
    building > floor > room hierarchy.
    """
    class Meta:
        db_table = 'locations'
        verbose_name = 'Location'
        verbose_name_plural = 'Locations'
        ordering = ['path']
        indexes = [
            models.Index(fields=['organization', 'path']),
        ]

    name = models.CharField(
        max_length=200,
        help_text='Location name'
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='children',
        help_text='Parent location for tree structure'
    )
    path = models.CharField(
        max_length=500,
        help_text='Full path (e.g., Building A > Floor 1 > Room 101)'
    )
    level = models.IntegerField(
        default=0,
        help_text='Tree level (0=root, 1=first child, ...)'
    )
    LOCATION_TYPE_CHOICES = [
        ('building', 'Building'),
        ('floor', 'Floor'),
        ('room', 'Room'),
        ('area', 'Area'),
        ('warehouse', 'Warehouse'),
        ('other', 'Other'),
    ]
    location_type = models.CharField(
        max_length=20,
        choices=LOCATION_TYPE_CHOICES,
        default='area',
        help_text='Location type'
    )

    def save(self, *args, **kwargs):
        if self.parent:
            self.level = self.parent.level + 1
            self.path = f"{self.parent.path} / {self.name}"
        else:
            self.level = 0
            self.path = self.name
        super().save(*args, **kwargs)

    def __str__(self):
        return self.path


class AssetStatusLog(BaseModel):
    """
    Asset Status Change Log Model

    Inherits from BaseModel, records complete status change history.
    """
    class Meta:
        db_table = 'asset_status_logs'
        verbose_name = 'Asset Status Log'
        verbose_name_plural = 'Asset Status Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'asset', '-created_at']),
        ]

    asset = models.ForeignKey(
        'Asset',
        on_delete=models.CASCADE,
        related_name='status_logs',
        help_text='Related asset'
    )
    old_status = models.CharField(
        max_length=20,
        help_text='Previous status'
    )
    new_status = models.CharField(
        max_length=20,
        help_text='New status'
    )
    reason = models.TextField(
        blank=True,
        help_text='Reason for status change'
    )

    def __str__(self):
        return f"{self.asset.asset_code}: {self.old_status} -> {self.new_status}"


class Asset(BaseModel):
    """
    Asset Card Model

    The core model for fixed asset management. Each physical asset
    corresponds to one Asset card, recording its complete lifecycle
    information.

    Inherits from BaseModel, automatically gets:
    - organization: Multi-tenant data isolation
    - is_deleted, deleted_at: Soft delete support
    - created_at, updated_at, created_by: Audit fields
    - custom_fields: Dynamic metadata storage (JSONB)
    """

    class Meta:
        db_table = 'assets'
        verbose_name = 'Asset'
        verbose_name_plural = 'Assets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'asset_code']),
            models.Index(fields=['organization', 'asset_category']),
            models.Index(fields=['organization', 'custodian']),
            models.Index(fields=['organization', 'qr_code']),
            models.Index(fields=['organization', 'asset_status']),
            models.Index(fields=['organization', 'department']),
        ]

    # ========== Basic Information ==========
    asset_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Unique asset code (auto-generated: ZCYYYYMMNNNN)'
    )
    asset_name = models.CharField(
        max_length=200,
        help_text='Asset name'
    )
    asset_category = models.ForeignKey(
        'assets.AssetCategory',
        on_delete=models.PROTECT,
        related_name='assets',
        help_text='Asset category'
    )
    specification = models.CharField(
        max_length=200,
        blank=True,
        help_text='Specification/model'
    )
    brand = models.CharField(
        max_length=100,
        blank=True,
        help_text='Brand'
    )
    model = models.CharField(
        max_length=100,
        blank=True,
        help_text='Model'
    )
    unit = models.CharField(
        max_length=50,
        default='unit',
        help_text='Unit of measurement (references Dictionary: UNIT)'
    )
    serial_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='Serial number'
    )

    # ========== Financial Information ==========
    purchase_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Original purchase price'
    )
    current_value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text='Current net value'
    )
    accumulated_depreciation = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text='Accumulated depreciation'
    )
    purchase_date = models.DateField(
        help_text='Purchase date'
    )
    depreciation_start_date = models.DateField(
        null=True,
        blank=True,
        help_text='Depreciation start date'
    )
    useful_life = models.IntegerField(
        default=60,
        help_text='Useful life in months'
    )
    residual_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=5.00,
        help_text='Residual value rate (%)'
    )

    # ========== Supplier Information ==========
    supplier = models.ForeignKey(
        'assets.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='supplied_assets',
        help_text='Supplier'
    )
    supplier_order_no = models.CharField(
        max_length=100,
        blank=True,
        help_text='Supplier order number'
    )
    invoice_no = models.CharField(
        max_length=100,
        blank=True,
        help_text='Invoice number'
    )

    # ========== Usage Information ==========
    department = models.ForeignKey(
        'organizations.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assets',
        help_text='Using department'
    )
    location = models.ForeignKey(
        'assets.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assets',
        help_text='Storage location'
    )
    custodian = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='custodian_assets',
        help_text='Custodian'
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='using_assets',
        help_text='Actual user'
    )

    # ========== Status Information ==========
    # Status values are managed via Dictionary (code: ASSET_STATUS)
    # Available statuses: pending, in_use, idle, maintenance, lent, lost, scrapped
    # Use DictionaryService.get_items('ASSET_STATUS') for options

    asset_status = models.CharField(
        max_length=50,
        default='pending',
        db_index=True,
        help_text='Asset status (references Dictionary: ASSET_STATUS)'
    )

    # ========== Label Information ==========
    qr_code = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text='QR code (auto-generated UUID)'
    )
    rfid_code = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text='RFID code'
    )

    # ========== Attachment Information ==========
    images = models.JSONField(
        default=list,
        blank=True,
        help_text='Asset images'
    )
    attachments = models.JSONField(
        default=list,
        blank=True,
        help_text='Attachment list'
    )
    remarks = models.TextField(
        blank=True,
        help_text='Remarks'
    )

    def __str__(self):
        return f"{self.asset_code} - {self.asset_name}"

    def save(self, *args, **kwargs):
        # Auto-generate asset code using SequenceService
        if not self.asset_code:
            self.asset_code = self._generate_asset_code()

        # Auto-generate QR code if not provided
        if not self.qr_code:
            self.qr_code = self._generate_qr_code()

        # Set depreciation start date if not set
        if not self.depreciation_start_date and self.purchase_date:
            self.depreciation_start_date = self.purchase_date

        super().save(*args, **kwargs)

    def _generate_asset_code(self):
        """
        Generate asset code using SequenceService.

        Uses the ASSET_CODE sequence rule configured in system.
        Format: ZC + YYYYMM + 4-digit sequence (e.g., ZC2026010001)

        Falls back to legacy logic if SequenceService is unavailable.
        """
        try:
            from apps.system.services import SequenceService
            return SequenceService.get_next_value(
                'ASSET_CODE',
                organization_id=self.organization_id
            )
        except Exception:
            # Fallback to legacy generation if service fails
            from django.utils import timezone
            prefix = timezone.now().strftime('%Y%m')
            last_asset = Asset.all_objects.filter(
                asset_code__startswith=f"ZC{prefix}"
            ).order_by('-asset_code').first()
            if last_asset:
                seq = int(last_asset.asset_code[-4:]) + 1
            else:
                seq = 1
            return f"ZC{prefix}{seq:04d}"

    def _generate_qr_code(self):
        """Generate QR code content (UUID)."""
        import uuid
        return str(uuid.uuid4())

    @property
    def net_value(self):
        """Get net value (purchase price - accumulated depreciation)."""
        return float(self.purchase_price) - float(self.accumulated_depreciation)

    @property
    def residual_value(self):
        """Get estimated residual value."""
        return float(self.purchase_price) * float(self.residual_rate) / 100

    def get_status_label(self, lang=None):
        """
        Get status display label from Dictionary.

        Args:
            lang: Language code ('zh' or 'en')

        Returns:
            Localized status label
        """
        try:
            from apps.system.services import DictionaryService
            from django.utils.translation import get_language
            return DictionaryService.get_label(
                'ASSET_STATUS',
                self.asset_status,
                organization_id=self.organization_id,
                lang=lang or get_language()
            )
        except Exception:
            # Fallback to raw value
            return self.asset_status


# ========== Asset Operation Models ==========


class AssetPickup(BaseModel):
    """
    Asset Pickup Order Model

    Records employee asset pickup requests with approval workflow.
    Inherits from BaseModel for organization isolation and soft delete.
    """

    class Meta:
        db_table = 'asset_pickups'
        verbose_name = 'Asset Pickup Order'
        verbose_name_plural = 'Asset Pickup Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'pickup_no']),
            models.Index(fields=['organization', 'applicant']),
            models.Index(fields=['organization', 'department']),
            models.Index(fields=['organization', 'status']),
        ]

    # Status values are managed via Dictionary (code: PICKUP_STATUS)
    # Available statuses: draft, pending, approved, rejected, completed, cancelled
    # Use DictionaryService.get_items('PICKUP_STATUS') for options

    # Basic Information
    pickup_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Pickup order number (auto-generated: LY+YYYYMM+NNNN)'
    )
    applicant = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='pickup_applications',
        help_text='Applicant who requests the pickup'
    )
    department = models.ForeignKey(
        'organizations.Department',
        on_delete=models.PROTECT,
        related_name='department_pickups',
        help_text='Pickup department'
    )
    pickup_date = models.DateField(
        help_text='Pickup date'
    )
    pickup_reason = models.TextField(
        blank=True,
        help_text='Reason for pickup'
    )

    # Status and Approval
    status = models.CharField(
        max_length=50,
        default='draft',
        db_index=True,
        help_text='Pickup order status (references Dictionary: PICKUP_STATUS)'
    )
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_pickups',
        help_text='Approver'
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Approval timestamp'
    )
    approval_comment = models.TextField(
        blank=True,
        help_text='Approval comment'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Completion timestamp'
    )

    def __str__(self):
        return f"{self.pickup_no} - {self.applicant.username}"

    def save(self, *args, **kwargs):
        if not self.pickup_no:
            self.pickup_no = self._generate_pickup_no()
        super().save(*args, **kwargs)

    def _generate_pickup_no(self):
        """
        Generate pickup order number using SequenceService.

        Uses the PICKUP_NO sequence rule configured in system.
        Falls back to legacy logic if SequenceService is unavailable.
        """
        try:
            from apps.system.services import SequenceService
            return SequenceService.get_next_value(
                'PICKUP_NO',
                organization_id=self.organization_id
            )
        except Exception:
            # Fallback to legacy generation
            from django.utils import timezone
            prefix = timezone.now().strftime('%Y%m')
            last_pickup = AssetPickup.all_objects.filter(
                pickup_no__startswith=f"LY{prefix}"
            ).order_by('-pickup_no').first()
            if last_pickup:
                seq = int(last_pickup.pickup_no[-4:]) + 1
            else:
                seq = 1
            return f"LY{prefix}{seq:04d}"

    def get_status_label(self, lang=None):
        """
        Get status display label from Dictionary.

        Args:
            lang: Language code ('zh' or 'en')

        Returns:
            Localized status label
        """
        try:
            from apps.system.services import DictionaryService
            from django.utils.translation import get_language
            return DictionaryService.get_label(
                'PICKUP_STATUS',
                self.status,
                organization_id=self.organization_id,
                lang=lang or get_language()
            )
        except Exception:
            return self.status


class PickupItem(BaseModel):
    """Asset Pickup Order Line Item"""

    class Meta:
        db_table = 'pickup_items'
        verbose_name = 'Pickup Item'
        verbose_name_plural = 'Pickup Items'
        indexes = [
            models.Index(fields=['pickup', 'asset']),
        ]

    pickup = models.ForeignKey(
        AssetPickup,
        on_delete=models.CASCADE,
        related_name='items',
        help_text='Parent pickup order'
    )
    asset = models.ForeignKey(
        'Asset',
        on_delete=models.PROTECT,
        related_name='pickup_items',
        help_text='Asset to pick up'
    )
    quantity = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text='Quantity'
    )
    remark = models.TextField(
        blank=True,
        help_text='Item remark'
    )
    # Snapshot fields for preserving original state
    snapshot_original_location = models.ForeignKey(
        'Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text='Original location snapshot'
    )
    snapshot_original_custodian = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text='Original custodian snapshot'
    )

    def __str__(self):
        return f"{self.pickup.pickup_no} - {self.asset.asset_name}"


class AssetTransfer(BaseModel):
    """
    Asset Transfer Order Model

    Records asset transfers between departments with dual approval.
    Inherits from BaseModel for organization isolation and soft delete.
    """

    class Meta:
        db_table = 'asset_transfers'
        verbose_name = 'Asset Transfer Order'
        verbose_name_plural = 'Asset Transfer Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'transfer_no']),
            models.Index(fields=['organization', 'from_department']),
            models.Index(fields=['organization', 'to_department']),
            models.Index(fields=['organization', 'status']),
        ]

    # Status values are managed via Dictionary (code: TRANSFER_STATUS)
    # Available statuses: draft, pending, out_approved, approved, rejected, completed, cancelled
    # Use DictionaryService.get_items('TRANSFER_STATUS') for options

    # Basic Information
    transfer_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Transfer order number (auto-generated: TF+YYYYMM+NNNN)'
    )
    from_department = models.ForeignKey(
        'organizations.Department',
        on_delete=models.PROTECT,
        related_name='transfers_out',
        help_text='Source department'
    )
    to_department = models.ForeignKey(
        'organizations.Department',
        on_delete=models.PROTECT,
        related_name='transfers_in',
        help_text='Target department'
    )
    transfer_date = models.DateField(
        help_text='Transfer date'
    )
    transfer_reason = models.TextField(
        blank=True,
        help_text='Reason for transfer'
    )

    # Status and Approval
    status = models.CharField(
        max_length=50,
        default='draft',
        db_index=True,
        help_text='Transfer order status (references Dictionary: TRANSFER_STATUS)'
    )
    from_approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='out_approved_transfers',
        help_text='Source department approver'
    )
    from_approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Source approval timestamp'
    )
    from_approve_comment = models.TextField(
        blank=True,
        help_text='Source approval comment'
    )
    to_approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='in_approved_transfers',
        help_text='Target department approver'
    )
    to_approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Target approval timestamp'
    )
    to_approve_comment = models.TextField(
        blank=True,
        help_text='Target approval comment'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Completion timestamp'
    )

    def __str__(self):
        return f"{self.transfer_no} - {self.from_department.name} to {self.to_department.name}"

    def save(self, *args, **kwargs):
        if not self.transfer_no:
            self.transfer_no = self._generate_transfer_no()
        super().save(*args, **kwargs)

    def _generate_transfer_no(self):
        """
        Generate transfer order number using SequenceService.

        Uses the TRANSFER_NO sequence rule configured in system.
        Falls back to legacy logic if SequenceService is unavailable.
        """
        try:
            from apps.system.services import SequenceService
            return SequenceService.get_next_value(
                'TRANSFER_NO',
                organization_id=self.organization_id
            )
        except Exception:
            # Fallback to legacy generation
            from django.utils import timezone
            prefix = timezone.now().strftime('%Y%m')
            last_transfer = AssetTransfer.all_objects.filter(
                transfer_no__startswith=f"TF{prefix}"
            ).order_by('-transfer_no').first()
            if last_transfer:
                seq = int(last_transfer.transfer_no[-4:]) + 1
            else:
                seq = 1
            return f"TF{prefix}{seq:04d}"

    def get_status_label(self, lang=None):
        """
        Get status display label from Dictionary.

        Args:
            lang: Language code ('zh' or 'en')

        Returns:
            Localized status label
        """
        try:
            from apps.system.services import DictionaryService
            from django.utils.translation import get_language
            return DictionaryService.get_label(
                'TRANSFER_STATUS',
                self.status,
                organization_id=self.organization_id,
                lang=lang or get_language()
            )
        except Exception:
            return self.status


class TransferItem(BaseModel):
    """Asset Transfer Order Line Item"""

    class Meta:
        db_table = 'transfer_items'
        verbose_name = 'Transfer Item'
        verbose_name_plural = 'Transfer Items'
        indexes = [
            models.Index(fields=['transfer', 'asset']),
        ]

    transfer = models.ForeignKey(
        AssetTransfer,
        on_delete=models.CASCADE,
        related_name='items',
        help_text='Parent transfer order'
    )
    asset = models.ForeignKey(
        'Asset',
        on_delete=models.PROTECT,
        related_name='transfer_items',
        help_text='Asset to transfer'
    )
    from_location = models.ForeignKey(
        'Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text='Original location snapshot'
    )
    from_custodian = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        help_text='Original custodian snapshot'
    )
    to_location = models.ForeignKey(
        'Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transfer_in_locations',
        help_text='Target location'
    )
    remark = models.TextField(
        blank=True,
        help_text='Item remark'
    )

    def __str__(self):
        return f"{self.transfer.transfer_no} - {self.asset.asset_name}"


class AssetReturn(BaseModel):
    """
    Asset Return Order Model

    Records asset returns from employees back to storage.
    Inherits from BaseModel for organization isolation and soft delete.
    """

    class Meta:
        db_table = 'asset_returns'
        verbose_name = 'Asset Return Order'
        verbose_name_plural = 'Asset Return Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'return_no']),
            models.Index(fields=['organization', 'returner']),
            models.Index(fields=['organization', 'status']),
        ]
    # Status values are managed via Dictionary (code: RETURN_STATUS)
    # Available statuses: draft, pending, confirmed, completed, cancelled
    # Use DictionaryService.get_items('RETURN_STATUS') for options

    # Basic Information
    return_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Return order number (auto-generated: GH+YYYYMM+NNNN)'
    )
    returner = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='returns',
        help_text='User who returns the assets'
    )
    return_date = models.DateField(
        help_text='Return date'
    )
    return_reason = models.TextField(
        blank=True,
        help_text='Reason for return'
    )

    # Status and Confirmation
    status = models.CharField(
        max_length=50,
        default='draft',
        db_index=True,
        help_text='Return order status (references Dictionary: RETURN_STATUS)'
    )
    return_location = models.ForeignKey(
        'Location',
        on_delete=models.PROTECT,
        related_name='asset_returns',
        help_text='Storage location for returned assets'
    )

    # Status and Confirmation
    status = models.CharField(
        max_length=50,
        default='draft',
        db_index=True,
        help_text='Return order status (references Dictionary: RETURN_STATUS)'
    )
    confirmed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_returns',
        help_text=' confirmer'
    )
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Confirmation timestamp'
    )
    reject_reason = models.TextField(
        blank=True,
        help_text='Rejection reason'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Completion timestamp'
    )

    def __str__(self):
        return f"{self.return_no} - {self.returner.username}"

    def save(self, *args, **kwargs):
        if not self.return_no:
            self.return_no = self._generate_return_no()
        super().save(*args, **kwargs)

    def _generate_return_no(self):
        """
        Generate return order number using SequenceService.
        Format: RT+YYYYMM+NNNN
        """
        try:
            from apps.system.services import SequenceService
            return SequenceService.get_next_value(
                'RETURN_NO',
                organization_id=self.organization_id
            )
        except Exception:
            # Fallback
            from django.utils import timezone
            prefix = timezone.now().strftime('%Y%m')
            last_return = AssetReturn.objects.filter(
                return_no__startswith=f"RT{prefix}"
            ).order_by('-return_no').first()
            
            if last_return:
                seq = int(last_return.return_no[-4:]) + 1
            else:
                seq = 1
            return f"RT{prefix}{seq:04d}"

    def get_status_label(self, lang=None):
        """
        Get status display label from Dictionary.

        Args:
            lang: Language code ('zh' or 'en')

        Returns:
            Localized status label
        """
        try:
            from apps.system.services import DictionaryService
            from django.utils.translation import get_language
            return DictionaryService.get_label(
                'RETURN_STATUS',
                self.status,
                organization_id=self.organization_id,
                lang=lang or get_language()
            )
        except Exception:
            return self.status


class ReturnItem(BaseModel):
    """Asset Return Order Line Item"""

    class Meta:
        db_table = 'return_items'
        verbose_name = 'Return Item'
        verbose_name_plural = 'Return Items'
        indexes = [
            models.Index(fields=['asset_return', 'asset']),
        ]

    # Asset status after return
    ASSET_STATUS_CHOICES = [
        ('idle', 'Idle'),
        ('maintenance', 'Needs Maintenance'),
        ('scrapped', 'Needs Scrapping'),
    ]

    asset_return = models.ForeignKey(
        AssetReturn,
        on_delete=models.CASCADE,
        related_name='items',
        help_text='Parent return order'
    )
    asset = models.ForeignKey(
        'Asset',
        on_delete=models.PROTECT,
        related_name='return_items',
        help_text='Asset being returned'
    )
    asset_status = models.CharField(
        max_length=20,
        choices=ASSET_STATUS_CHOICES,
        default='idle',
        help_text='Asset status after return'
    )
    condition_description = models.TextField(
        blank=True,
        help_text='Asset condition description'
    )
    remark = models.TextField(
        blank=True,
        help_text='Item remark'
    )

    def __str__(self):
        return f"{self.asset_return.return_no} - {self.asset.asset_name}"


class AssetLoan(BaseModel):
    """
    Asset Loan Order Model

    Records temporary asset loans with return tracking.
    Inherits from BaseModel for organization isolation and soft delete.
    """

    class Meta:
        db_table = 'asset_loans'
        verbose_name = 'Asset Loan Order'
        verbose_name_plural = 'Asset Loan Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'loan_no']),
            models.Index(fields=['organization', 'borrower']),
            models.Index(fields=['organization', 'status']),
        ]

    # Status values are managed via Dictionary (code: LOAN_STATUS)
    # Available statuses: draft, pending, approved, rejected, borrowed, overdue, returned, cancelled
    # Use DictionaryService.get_items('LOAN_STATUS') for options

    # Asset condition choices
    CONDITION_CHOICES = [
        ('good', 'Good'),
        ('minor_damage', 'Minor Damage'),
        ('major_damage', 'Major Damage'),
        ('lost', 'Lost'),
    ]

    # Basic Information
    loan_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Loan order number (auto-generated: JY+YYYYMM+NNNN)'
    )
    borrower = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='loans',
        help_text='Borrower'
    )
    borrow_date = models.DateField(
        help_text='Borrow date'
    )
    expected_return_date = models.DateField(
        help_text='Expected return date'
    )
    actual_return_date = models.DateField(
        null=True,
        blank=True,
        help_text='Actual return date'
    )
    loan_reason = models.TextField(
        blank=True,
        help_text='Reason for loan'
    )

    # Status and Approval
    status = models.CharField(
        max_length=50,
        default='draft',
        db_index=True,
        help_text='Loan order status (references Dictionary: LOAN_STATUS)'
    )
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_loans',
        help_text='Approver'
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Approval timestamp'
    )
    approval_comment = models.TextField(
        blank=True,
        help_text='Approval comment'
    )

    # Lend and Return tracking
    lent_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lent_assets',
        help_text='Person who confirmed lending'
    )
    lent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Lend confirmation timestamp'
    )
    returned_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Return confirmation timestamp'
    )
    return_confirmed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='confirmed_loan_returns',
        help_text='Person who confirmed return'
    )
    asset_condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        blank=True,
        help_text='Asset condition upon return'
    )
    return_comment = models.TextField(
        blank=True,
        help_text='Return comment'
    )

    def __str__(self):
        return f"{self.loan_no} - {self.borrower.username}"

    def save(self, *args, **kwargs):
        if not self.loan_no:
            self.loan_no = self._generate_loan_no()
        super().save(*args, **kwargs)

    def _generate_loan_no(self):
        """
        Generate loan order number using SequenceService.
        Format: LN+YYYYMM+NNNN
        """
        try:
            from apps.system.services import SequenceService
            return SequenceService.get_next_value(
                'LOAN_NO',
                organization_id=self.organization_id
            )
        except Exception:
            # Fallback
            from django.utils import timezone
            prefix = timezone.now().strftime('%Y%m')
            last_loan = AssetLoan.objects.filter(
                loan_no__startswith=f"LN{prefix}"
            ).order_by('-loan_no').first()
            
            if last_loan:
                seq = int(last_loan.loan_no[-4:]) + 1
            else:
                seq = 1
            return f"LN{prefix}{seq:04d}"

    def get_status_label(self, lang=None):
        """
        Get status display label from Dictionary.

        Args:
            lang: Language code ('zh' or 'en')

        Returns:
            Localized status label
        """
        try:
            from apps.system.services import DictionaryService
            from django.utils.translation import get_language
            return DictionaryService.get_label(
                'LOAN_STATUS',
                self.status,
                organization_id=self.organization_id,
                lang=lang or get_language()
            )
        except Exception:
            return self.status

    def is_overdue(self):
        """Check if loan is overdue."""
        from django.utils import timezone
        if self.status == 'borrowed' and self.expected_return_date:
            return timezone.now().date() > self.expected_return_date
        return False

    def overdue_days(self):
        """Get number of overdue days."""
        from django.utils import timezone
        if self.is_overdue():
            return (timezone.now().date() - self.expected_return_date).days
        return 0


class LoanItem(BaseModel):
    """Asset Loan Order Line Item"""

    class Meta:
        db_table = 'loan_items'
        verbose_name = 'Loan Item'
        verbose_name_plural = 'Loan Items'
        indexes = [
            models.Index(fields=['loan', 'asset']),
        ]

    loan = models.ForeignKey(
        AssetLoan,
        on_delete=models.CASCADE,
        related_name='items',
        help_text='Parent loan order'
    )
    asset = models.ForeignKey(
        'Asset',
        on_delete=models.PROTECT,
        related_name='loan_items',
        help_text='Asset being borrowed'
    )
    remark = models.TextField(
        blank=True,
        help_text='Item remark'
    )

    def __str__(self):
        return f"{self.loan.loan_no} - {self.asset.asset_name}"
