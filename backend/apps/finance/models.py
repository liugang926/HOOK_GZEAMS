"""
Finance Models

Models for financial vouchers, voucher entries, and voucher templates.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.common.models import BaseModel


class FinanceVoucher(BaseModel):
    """
    Financial Voucher Model

    Represents a financial voucher for various business transactions.
    """

    class Meta:
        db_table = 'finance_vouchers'
        verbose_name = 'Finance Voucher'
        verbose_name_plural = 'Finance Vouchers'
        ordering = ['-voucher_date', '-created_at']
        indexes = [
            models.Index(fields=['organization', 'voucher_no']),
            models.Index(fields=['organization', 'voucher_date']),
            models.Index(fields=['organization', 'business_type']),
            models.Index(fields=['organization', 'status']),
        ]

    BUSINESS_TYPE_CHOICES = [
        ('purchase', 'Asset Purchase'),
        ('depreciation', 'Asset Depreciation'),
        ('disposal', 'Asset Disposal'),
        ('inventory', 'Asset Inventory'),
        ('other', 'Other'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('posted', 'Posted'),
        ('rejected', 'Rejected'),
    ]

    voucher_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Unique voucher number'
    )
    voucher_date = models.DateField(
        help_text='Voucher date'
    )
    business_type = models.CharField(
        max_length=50,
        choices=BUSINESS_TYPE_CHOICES,
        help_text='Business type'
    )
    summary = models.CharField(
        max_length=500,
        help_text='Voucher summary'
    )
    total_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Total voucher amount'
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='draft',
        help_text='Voucher status'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes'
    )

    # ERP integration fields
    erp_voucher_no = models.CharField(
        max_length=100,
        blank=True,
        help_text='ERP voucher number after posting'
    )
    posted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when voucher was posted to ERP'
    )
    posted_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posted_vouchers',
        help_text='User who posted to ERP'
    )

    def __str__(self):
        return f"{self.voucher_no} - {self.summary}"

    def calculate_total_amount(self):
        """
        Calculate total amount from voucher entries.

        Returns:
            Decimal: Total debit/credit amount
        """
        # Total should equal total debit amount (should equal total credit)
        total_debit = self.entries.aggregate(
            total=models.Sum('debit_amount')
        )['total'] or 0
        return total_debit

    def is_balanced(self):
        """
        Check if voucher is balanced (debits = credits).

        Returns:
            bool: True if balanced
        """
        from django.db.models import Sum
        total_debit = self.entries.aggregate(
            total=Sum('debit_amount')
        )['total'] or 0
        total_credit = self.entries.aggregate(
            total=Sum('credit_amount')
        )['total'] or 0
        return total_debit == total_credit

    def can_submit(self):
        """Check if voucher can be submitted."""
        return self.status == 'draft' and self.is_balanced()

    def can_approve(self):
        """Check if voucher can be approved."""
        return self.status == 'submitted'

    def can_post(self):
        """Check if voucher can be posted to ERP."""
        return self.status == 'approved' and not self.erp_voucher_no


class VoucherEntry(BaseModel):
    """
    Voucher Entry Model

    Represents individual debit/credit entries within a voucher.
    """

    class Meta:
        db_table = 'voucher_entries'
        verbose_name = 'Voucher Entry'
        verbose_name_plural = 'Voucher Entries'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['organization', 'voucher']),
            models.Index(fields=['organization', 'account_code']),
        ]

    voucher = models.ForeignKey(
        FinanceVoucher,
        on_delete=models.CASCADE,
        related_name='entries',
        help_text='Parent voucher'
    )
    account_code = models.CharField(
        max_length=50,
        db_index=True,
        help_text='Account code (chart of accounts)'
    )
    account_name = models.CharField(
        max_length=200,
        help_text='Account name'
    )
    debit_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Debit amount'
    )
    credit_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Credit amount'
    )
    description = models.CharField(
        max_length=500,
        help_text='Entry description'
    )
    line_no = models.IntegerField(
        default=1,
        help_text='Line number for sorting'
    )

    def __str__(self):
        return f"{self.voucher.voucher_no} - {self.account_code}: {self.debit_amount or self.credit_amount}"


class VoucherTemplate(BaseModel):
    """
    Voucher Template Model

    Defines reusable voucher templates for different business scenarios.
    """

    class Meta:
        db_table = 'voucher_templates'
        verbose_name = 'Voucher Template'
        verbose_name_plural = 'Voucher Templates'
        ordering = ['code', 'name']
        indexes = [
            models.Index(fields=['organization', 'code']),
            models.Index(fields=['organization', 'business_type']),
        ]

    name = models.CharField(
        max_length=200,
        help_text='Template name'
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='Template code'
    )
    business_type = models.CharField(
        max_length=50,
        choices=FinanceVoucher.BUSINESS_TYPE_CHOICES,
        help_text='Business type'
    )
    template_config = models.JSONField(
        default=dict,
        help_text='Template configuration (accounts, amounts, formulas)'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether template is active'
    )
    description = models.TextField(
        blank=True,
        help_text='Template description'
    )

    def __str__(self):
        return f"{self.code} - {self.name}"


@receiver(post_save, sender=VoucherEntry)
def update_voucher_total(sender, instance, created, **kwargs):
    """
    Signal handler to update voucher total when entry is saved.

    This is triggered after a VoucherEntry is saved.
    """
    voucher = instance.voucher
    # Recalculate total amount
    voucher.total_amount = voucher.calculate_total_amount()
    voucher.save(update_fields=['total_amount', 'updated_at'])
