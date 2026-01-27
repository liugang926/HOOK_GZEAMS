"""
Insurance management models.

This module contains models for managing insurance companies,
policies, insured assets, premium payments, claims, and renewals.
"""

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

    # Claims Contact
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


class InsurancePolicy(BaseModel):
    """
    Insurance Policy Model

    Manages insurance policies for assets.
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

    @property
    def total_insured_assets(self):
        """Get count of insured assets."""
        return self.insured_assets.count()

    @property
    def total_claims(self):
        """Get count of claims."""
        return self.claims.count()

    @property
    def total_claim_amount(self):
        """Get total claimed amount."""
        from django.db.models import Sum
        return self.claims.aggregate(
            total=Sum('claimed_amount')
        )['total'] or 0


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
        blank=True,
        null=True,
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
