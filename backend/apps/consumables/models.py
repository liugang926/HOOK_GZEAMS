"""
Consumables Management Models

Models for managing low-value consumables and office supplies:
- ConsumableCategory: Hierarchical category structure
- Consumable: Consumable item master data
- ConsumableStock: Stock transaction records
- ConsumablePurchase: Purchase orders for procuring consumables
- ConsumableIssue: Issue orders for distributing consumables
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.common.models import BaseModel



# ========== Category Model ==========

class ConsumableCategory(BaseModel):
    """
    Consumable Category Model

    Manages hierarchical categories for consumables and office supplies.
    Inherits from BaseModel for organization isolation and soft delete.
    """

    class Meta:
        db_table = 'consumable_categories'
        verbose_name = 'Consumable Category'
        verbose_name_plural = 'Consumable Categories'
        ordering = ['path', 'code']
        indexes = [
            models.Index(fields=['organization', 'code']),
            models.Index(fields=['organization', 'parent']),
            models.Index(fields=['organization', 'is_active']),
        ]

    # Basic Information
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Category code (unique)'
    )
    name = models.CharField(
        max_length=100,
        help_text='Category name'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text='Parent category'
    )

    # Hierarchy fields
    level = models.IntegerField(
        default=1,
        help_text='Hierarchy level (1=top level)'
    )
    path = models.CharField(
        max_length=500,
        blank=True,
        help_text='Category path for display'
    )

    # Stock Alert Settings
    enable_alert = models.BooleanField(
        default=True,
        help_text='Enable stock alert for this category'
    )
    min_stock = models.IntegerField(
        default=10,
        help_text='Minimum stock level for alert'
    )
    max_stock = models.IntegerField(
        default=100,
        help_text='Maximum stock level'
    )
    reorder_point = models.IntegerField(
        default=20,
        help_text='Reorder point to trigger purchase'
    )

    # Unit and Pricing
    unit = models.CharField(
        max_length=50,
        default='unit',
        help_text='Default unit of measure'
    )
    default_supplier = models.ForeignKey(
        'assets.Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consumable_categories',
        help_text='Default supplier'
    )
    reference_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Reference purchase price'
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Whether category is active'
    )

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        """Validate category data"""
        if self.parent:
            if self.parent.id == self.id:
                raise ValidationError({'parent': 'Cannot set self as parent'})

    def save(self, *args, **kwargs):
        """Update level and path before saving"""
        self.clean()
        if self.parent:
            self.level = self.parent.level + 1
            self.path = f"{self.parent.path}/{self.name}"
        else:
            self.level = 1
            self.path = self.name
        super().save(*args, **kwargs)


# ========== Consumable Model ==========

# Consumable Status choices removed - using Dictionary CONSUMABLE_STATUS


class Consumable(BaseModel):
    """
    Consumable Model

    Master data for consumable items and office supplies.
    Inherits from BaseModel for organization isolation and soft delete.
    """

    class Meta:
        db_table = 'consumables'
        verbose_name = 'Consumable'
        verbose_name_plural = 'Consumables'
        ordering = ['code']
        indexes = [
            models.Index(fields=['organization', 'code']),
            models.Index(fields=['organization', 'category']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'warehouse']),
        ]

    # Basic Information
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Consumable code (unique)'
    )
    name = models.CharField(
        max_length=200,
        help_text='Consumable name'
    )
    category = models.ForeignKey(
        ConsumableCategory,
        on_delete=models.PROTECT,
        related_name='consumables',
        help_text='Category'
    )
    specification = models.CharField(
        max_length=200,
        blank=True,
        help_text='Specification or model'
    )
    brand = models.CharField(
        max_length=100,
        blank=True,
        help_text='Brand'
    )
    unit = models.CharField(
        max_length=50,
        default='unit',
        help_text='Unit of measure'
    )

    # Stock Information
    current_stock = models.IntegerField(
        default=0,
        help_text='Current stock quantity'
    )
    available_stock = models.IntegerField(
        default=0,
        help_text='Available stock (not locked)'
    )
    locked_stock = models.IntegerField(
        default=0,
        help_text='Locked stock (pending orders)'
    )

    # Pricing
    purchase_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Last purchase price'
    )
    average_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Weighted average price'
    )

    # Stock Alert Settings
    min_stock = models.IntegerField(
        default=10,
        help_text='Minimum stock level'
    )
    max_stock = models.IntegerField(
        default=100,
        help_text='Maximum stock level'
    )
    reorder_point = models.IntegerField(
        default=20,
        help_text='Reorder point'
    )

    # Status
    status = models.CharField(
        max_length=50,
        default='normal',
        db_index=True,
        help_text='Stock status'
    )
    warehouse = models.ForeignKey(
        'assets.Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consumables',
        help_text='Default warehouse location'
    )

    # Additional Information
    remark = models.TextField(
        blank=True,
        help_text='Additional remarks'
    )

    def __str__(self):
        return f"{self.code} - {self.name}"

    def get_status_label(self, lang=None):
        """Get localized status label"""
        from django.utils.translation import get_language
        from apps.system.services import DictionaryService
        return DictionaryService.get_label('CONSUMABLE_STATUS', self.status, lang=lang or get_language())

    def update_stock_status(self):
        """Update status based on available stock"""
        if self.available_stock <= 0:
            self.status = 'out_of_stock'
        elif self.available_stock <= self.min_stock:
            self.status = 'low_stock'
        else:
            self.status = 'normal'

    def is_low_stock(self):
        """Check if stock is at or below reorder point"""
        return self.available_stock <= self.reorder_point

    def save(self, *args, **kwargs):
        """Update status before saving"""
        self.update_stock_status()
        super().save(*args, **kwargs)


# ========== Consumable Stock Transaction Model ==========

class TransactionType(models.TextChoices):
    """Transaction type choices"""
    PURCHASE = 'purchase', 'Purchase'
    ISSUE = 'issue', 'Issue'
    RETURN = 'return', 'Return'
    TRANSFER_IN = 'transfer_in', 'Transfer In'
    TRANSFER_OUT = 'transfer_out', 'Transfer Out'
    INVENTORY_ADD = 'inventory_add', 'Inventory Addition'
    INVENTORY_REDUCE = 'inventory_reduce', 'Inventory Reduction'
    ADJUSTMENT = 'adjustment', 'Adjustment'


class ConsumableStock(BaseModel):
    """
    Consumable Stock Transaction Model

    Records all stock transactions for traceability.
    Inherits from BaseModel for organization isolation and soft delete.
    """

    class Meta:
        db_table = 'consumable_stock_transactions'
        verbose_name = 'Stock Transaction'
        verbose_name_plural = 'Stock Transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'consumable', '-created_at']),
            models.Index(fields=['organization', 'transaction_type']),
            models.Index(fields=['organization', 'source_type', 'source_id']),
        ]

    # Reference
    consumable = models.ForeignKey(
        Consumable,
        on_delete=models.CASCADE,
        related_name='stock_logs',
        help_text='Consumable'
    )

    # Transaction Details
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        help_text='Type of transaction'
    )
    quantity = models.IntegerField(
        help_text='Quantity (positive for in, negative for out)'
    )
    before_stock = models.IntegerField(
        default=0,
        help_text='Stock before transaction'
    )
    after_stock = models.IntegerField(
        default=0,
        help_text='Stock after transaction'
    )

    # Source Reference
    source_type = models.CharField(
        max_length=50,
        blank=True,
        help_text='Source type (purchase/issue/etc)'
    )
    source_id = models.CharField(
        max_length=100,
        blank=True,
        help_text='Source record ID'
    )
    source_no = models.CharField(
        max_length=100,
        blank=True,
        db_index=True,
        help_text='Source document number'
    )

    # Handler
    handler = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='handled_stock_transactions',
        help_text='Person who handled transaction'
    )

    # Additional Information
    remark = models.TextField(
        blank=True,
        help_text='Transaction remarks'
    )

    def __str__(self):
        return f"{self.consumable.name} - {self.get_transaction_type_label()} ({self.quantity})"

    @classmethod
    def create_transaction(cls, consumable, transaction_type, quantity,
                          source_type='', source_id='', source_no='',
                          handler=None, remark=''):
        """Create a stock transaction and update consumable stock"""
        before_stock = consumable.current_stock
        after_stock = before_stock + quantity

        transaction = cls.objects.create(
            organization=consumable.organization,
            consumable=consumable,
            transaction_type=transaction_type,
            quantity=quantity,
            before_stock=before_stock,
            after_stock=after_stock,
            source_type=source_type,
            source_id=source_id,
            source_no=source_no,
            handler=handler,
            remark=remark
        )

        # Update consumable stock
        consumable.current_stock = after_stock
        if transaction_type in [TransactionType.PURCHASE, TransactionType.TRANSFER_IN,
                                  TransactionType.INVENTORY_ADD]:
            consumable.available_stock += quantity
        elif transaction_type in [TransactionType.ISSUE, TransactionType.TRANSFER_OUT,
                                     TransactionType.INVENTORY_REDUCE]:
            consumable.available_stock = max(0, consumable.available_stock + quantity)

        consumable.update_stock_status()
        consumable.save()

        return transaction


# ========== Purchase Order Model ==========

# Purchase Status choices removed - using Dictionary CONSUMABLE_PURCHASE_STATUS


class ConsumablePurchase(BaseModel):
    """
    Consumable Purchase Order Model

    Manages purchase orders for procuring consumables.
    Inherits from BaseModel for organization isolation and soft delete.
    """

    class Meta:
        db_table = 'consumable_purchases'
        verbose_name = 'Purchase Order'
        verbose_name_plural = 'Purchase Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'purchase_no']),
            models.Index(fields=['organization', 'supplier']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'purchase_date']),
        ]

    # Basic Information
    purchase_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Purchase order number (auto-generated: CP+YYYYMM+NNNN)'
    )
    purchase_date = models.DateField(
        help_text='Purchase date'
    )
    supplier = models.ForeignKey(
        'assets.Supplier',
        on_delete=models.PROTECT,
        related_name='consumable_purchases',
        help_text='Supplier'
    )

    # Financial
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text='Total purchase amount'
    )

    # Status
    status = models.CharField(
        max_length=50,
        default='draft',
        db_index=True,
        help_text='Purchase order status'
    )

    # Approval
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_purchases',
        help_text='Person who approved'
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

    # Receiving
    received_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_purchases',
        help_text='Person who received goods'
    )
    received_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Receiving timestamp'
    )

    # Additional Information
    remark = models.TextField(
        blank=True,
        help_text='Additional remarks'
    )

    def __str__(self):
        return f"{self.purchase_no} - {self.supplier.name if self.supplier else 'No Supplier'}"

    def get_status_label(self, lang=None):
        """Get localized status label"""
        from django.utils.translation import get_language
        from apps.system.services import DictionaryService
        return DictionaryService.get_label('CONSUMABLE_PURCHASE_STATUS', self.status, lang=lang or get_language())

    def save(self, *args, **kwargs):
        """Generate purchase number if not set"""
        if not self.purchase_no:
            self.purchase_no = self._generate_purchase_no()
        super().save(*args, **kwargs)

    def _generate_purchase_no(self):
        """Generate purchase order number using SequenceService"""
        from apps.system.services import SequenceService
        return SequenceService.get_next_sequence_value('CONSUMABLE_PURCHASE_NO')

    def calculate_total(self):
        """Calculate total from items"""
        total = sum(item.amount for item in self.items.all())
        self.total_amount = total
        self.save()
        return total


class PurchaseItem(BaseModel):
    """
    Purchase Order Line Item

    Line items for consumable purchase orders.
    Inherits from BaseModel for organization isolation and soft delete.
    """

    class Meta:
        db_table = 'consumable_purchase_items'
        verbose_name = 'Purchase Item'
        verbose_name_plural = 'Purchase Items'
        unique_together = [['purchase', 'consumable']]
        indexes = [
            models.Index(fields=['organization', 'purchase']),
            models.Index(fields=['organization', 'consumable']),
        ]

    # References
    purchase = models.ForeignKey(
        ConsumablePurchase,
        on_delete=models.CASCADE,
        related_name='items',
        help_text='Purchase order'
    )
    consumable = models.ForeignKey(
        Consumable,
        on_delete=models.PROTECT,
        help_text='Consumable'
    )

    # Item Details
    quantity = models.IntegerField(
        help_text='Purchase quantity'
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Unit price'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text='Total amount (quantity * unit_price)'
    )

    # Additional Information
    remark = models.TextField(
        blank=True,
        help_text='Item remarks'
    )

    def __str__(self):
        return f"{self.purchase.purchase_no} - {self.consumable.name}"

    def save(self, *args, **kwargs):
        """Calculate amount if not set"""
        if not self.amount:
            self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)


# ========== Issue Order Model ==========

# Issue Status choices removed - using Dictionary CONSUMABLE_ISSUE_STATUS


class ConsumableIssue(BaseModel):
    """
    Consumable Issue Order Model

    Manages issue orders for distributing consumables to departments/employees.
    Inherits from BaseModel for organization isolation and soft delete.
    """

    class Meta:
        db_table = 'consumable_issues'
        verbose_name = 'Issue Order'
        verbose_name_plural = 'Issue Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'issue_no']),
            models.Index(fields=['organization', 'applicant']),
            models.Index(fields=['organization', 'department']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'issue_date']),
        ]

    # Basic Information
    issue_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Issue order number (auto-generated: CI+YYYYMM+NNNN)'
    )
    issue_date = models.DateField(
        help_text='Issue date'
    )
    applicant = models.ForeignKey(
        'accounts.User',
        on_delete=models.PROTECT,
        related_name='consumable_issues',
        help_text='Applicant'
    )
    department = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.PROTECT,
        related_name='consumable_issues',
        help_text='Department'
    )

    # Issue Details
    issue_reason = models.TextField(
        blank=True,
        help_text='Reason for issue'
    )

    # Status
    status = models.CharField(
        max_length=50,
        default='draft',
        db_index=True,
        help_text='Issue order status'
    )

    # Approval
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_issues',
        help_text='Person who approved'
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

    # Issuance
    issued_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issued_consumables',
        help_text='Person who issued items'
    )
    issued_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Issuance timestamp'
    )

    # Additional Information
    remark = models.TextField(
        blank=True,
        help_text='Additional remarks'
    )

    def __str__(self):
        return f"{self.issue_no} - {self.applicant.username}"

    def get_status_label(self, lang=None):
        """Get localized status label"""
        from django.utils.translation import get_language
        from apps.system.services import DictionaryService
        return DictionaryService.get_label('CONSUMABLE_ISSUE_STATUS', self.status, lang=lang or get_language())

    def save(self, *args, **kwargs):
        """Generate issue number if not set"""
        if not self.issue_no:
            self.issue_no = self._generate_issue_no()
        super().save(*args, **kwargs)

    def _generate_issue_no(self):
        """Generate issue order number using SequenceService"""
        from apps.system.services import SequenceService
        return SequenceService.get_next_sequence_value('CONSUMABLE_ISSUE_NO')


class IssueItem(BaseModel):
    """
    Issue Order Line Item

    Line items for consumable issue orders.
    Inherits from BaseModel for organization isolation and soft delete.
    """

    class Meta:
        db_table = 'consumable_issue_items'
        verbose_name = 'Issue Item'
        verbose_name_plural = 'Issue Items'
        unique_together = [['issue', 'consumable']]
        indexes = [
            models.Index(fields=['organization', 'issue']),
            models.Index(fields=['organization', 'consumable']),
        ]

    # References
    issue = models.ForeignKey(
        ConsumableIssue,
        on_delete=models.CASCADE,
        related_name='items',
        help_text='Issue order'
    )
    consumable = models.ForeignKey(
        Consumable,
        on_delete=models.PROTECT,
        help_text='Consumable'
    )

    # Item Details
    quantity = models.IntegerField(
        help_text='Issue quantity'
    )

    # Snapshot for reference
    snapshot_before_stock = models.IntegerField(
        default=0,
        help_text='Stock before issuance (snapshot)'
    )

    # Additional Information
    remark = models.TextField(
        blank=True,
        help_text='Item remarks'
    )

    def __str__(self):
        return f"{self.issue.issue_no} - {self.consumable.name} (x{self.quantity})"
