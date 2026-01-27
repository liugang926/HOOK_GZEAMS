"""
Leasing management models for GZEAMS.

Handles lease contracts, rent payments, asset returns, and lease extensions.
"""
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
