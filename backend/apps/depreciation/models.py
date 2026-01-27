from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Sum
from apps.common.models import BaseModel


class DepreciationConfig(BaseModel):
    """
    Depreciation Configuration Model

    Defines depreciation settings for each asset category.
    Determines how assets in a category are depreciated over time.
    """

    class Meta:
        db_table = 'depreciation_configs'
        verbose_name = 'Depreciation Configuration'
        verbose_name_plural = 'Depreciation Configurations'
        ordering = ['category__name']
        indexes = [
            models.Index(fields=['organization', 'category']),
            models.Index(fields=['organization', 'is_active']),
        ]
        unique_together = [['organization', 'category']]

    DEPRECIATION_METHOD_CHOICES = [
        ('straight_line', 'Straight Line Method'),
        ('double_declining', 'Double Declining Balance Method'),
        ('sum_of_years', 'Sum of Years Digits Method'),
        ('units_of_production', 'Units of Production Method'),
    ]

    # Category relationship
    category = models.ForeignKey(
        'assets.AssetCategory',
        on_delete=models.CASCADE,
        related_name='depreciation_configs',
        help_text='Asset category for this depreciation configuration'
    )

    # Depreciation parameters
    depreciation_method = models.CharField(
        max_length=50,
        choices=DEPRECIATION_METHOD_CHOICES,
        default='straight_line',
        help_text='Depreciation calculation method'
    )
    useful_life = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text='Useful life in months'
    )
    salvage_value_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Salvage value rate as percentage (e.g., 5.00 for 5%)'
    )

    # Configuration status
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this configuration is active'
    )

    # Notes
    notes = models.TextField(
        blank=True,
        help_text='Configuration notes'
    )

    def __str__(self):
        return f"{self.category.name} - {self.get_depreciation_method_display()}"

    def get_monthly_rate(self):
        """Calculate monthly depreciation rate."""
        if self.depreciation_method == 'straight_line':
            # Straight line: (1 - salvage_rate) / useful_life_months
            salvage_rate = self.salvage_value_rate / 100
            return (1 - salvage_rate) / self.useful_life
        return 0


class DepreciationRecord(BaseModel):
    """
    Depreciation Record Model

    Stores monthly depreciation calculation records for each asset.
    Tracks depreciation amount, accumulated amount, and net value.
    """

    class Meta:
        db_table = 'depreciation_records'
        verbose_name = 'Depreciation Record'
        verbose_name_plural = 'Depreciation Records'
        ordering = ['-period', '-created_at']
        indexes = [
            models.Index(fields=['organization', 'asset']),
            models.Index(fields=['organization', 'period']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'asset', 'period']),
        ]
        unique_together = [['organization', 'asset', 'period']]

    STATUS_CHOICES = [
        ('calculated', 'Calculated'),
        ('posted', 'Posted'),
        ('rejected', 'Rejected'),
    ]

    # Asset relationship
    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.CASCADE,
        related_name='depreciation_records',
        help_text='Asset being depreciated'
    )

    # Period information
    period = models.CharField(
        max_length=7,
        db_index=True,
        help_text='Depreciation period in YYYY-MM format'
    )

    # Financial amounts
    depreciation_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Depreciation amount for this period'
    )
    accumulated_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text='Total accumulated depreciation amount'
    )
    net_value = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text='Net book value after depreciation'
    )

    # Record status
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='calculated',
        help_text='Depreciation record status'
    )
    post_date = models.DateField(
        null=True,
        blank=True,
        help_text='Date when depreciation was posted to accounting'
    )

    # Additional information
    notes = models.TextField(
        blank=True,
        help_text='Record notes'
    )

    def __str__(self):
        return f"{self.asset.asset_code} - {self.period} ({self.get_status_display()})"


class DepreciationRun(BaseModel):
    """
    Depreciation Run Model

    Tracks batch depreciation calculation runs.
    Records the execution of periodic depreciation calculations.
    """

    class Meta:
        db_table = 'depreciation_runs'
        verbose_name = 'Depreciation Run'
        verbose_name_plural = 'Depreciation Runs'
        ordering = ['-run_date', '-created_at']
        indexes = [
            models.Index(fields=['organization', 'period']),
            models.Index(fields=['organization', 'status']),
        ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    # Run information
    period = models.CharField(
        max_length=7,
        db_index=True,
        help_text='Depreciation period in YYYY-MM format'
    )
    run_date = models.DateField(
        help_text='Date when depreciation calculation was executed'
    )

    # Run status
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Depreciation run status'
    )

    # Run statistics
    total_assets = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Total number of assets processed'
    )
    total_amount = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Total depreciation amount for this run'
    )

    # Error information
    error_message = models.TextField(
        blank=True,
        help_text='Error message if run failed'
    )

    # Additional information
    notes = models.TextField(
        blank=True,
        help_text='Run notes'
    )

    def __str__(self):
        return f"Depreciation Run - {self.period} ({self.get_status_display()})"

    def get_success_count(self):
        """Get number of successfully processed records."""
        return self.records.filter(status='calculated').count()

    def get_failed_count(self):
        """Get number of failed records."""
        return self.records.filter(status='rejected').count()
