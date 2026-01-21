"""
IT Asset models for GZEAMS.
"""
from django.db import models
from django.db.models.functions import Greatest
from django.core.validators import MinValueValidator
from apps.common.models import BaseModel


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

    # Relationship to base Asset
    asset = models.OneToOneField(
        'assets.Asset',
        on_delete=models.CASCADE,
        related_name='it_info',
        help_text='Related asset'
    )

    # CPU Information
    cpu_model = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='CPU model name'
    )
    cpu_cores = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text='Number of CPU cores'
    )
    cpu_threads = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text='Number of CPU threads'
    )

    # RAM Information
    ram_capacity = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text='RAM capacity in GB'
    )
    ram_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='RAM type (DDR3, DDR4, DDR5)'
    )
    ram_slots = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text='Number of RAM slots'
    )

    # Disk Information
    DISK_TYPE_CHOICES = [
        ('HDD', 'HDD'),
        ('SSD', 'SSD'),
        ('NVMe', 'NVMe'),
        ('SATA', 'SATA'),
    ]
    disk_type = models.CharField(
        max_length=20,
        choices=DISK_TYPE_CHOICES,
        blank=True,
        null=True,
        help_text='Disk type'
    )
    disk_capacity = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text='Disk capacity in GB'
    )
    disk_count = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text='Number of disks'
    )

    # GPU Information
    gpu_model = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='GPU model name'
    )
    gpu_memory = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1)],
        help_text='GPU memory in MB'
    )

    # Network Information
    mac_address = models.CharField(
        max_length=17,
        blank=True,
        null=True,
        unique=True,
        help_text='MAC address (XX:XX:XX:XX:XX:XX)'
    )
    ip_address = models.CharField(
        max_length=45,
        blank=True,
        null=True,
        help_text='IP address (IPv4 or IPv6)'
    )
    hostname = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='Network hostname'
    )

    # Operating System Information
    os_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Operating system name'
    )
    os_version = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Operating system version'
    )
    os_architecture = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='OS architecture (x64, x86, ARM64)'
    )
    os_license_key = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text='OS license key'
    )

    # Security Information
    disk_encrypted = models.BooleanField(
        default=False,
        help_text='Is disk encrypted'
    )
    antivirus_software = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Antivirus software name'
    )
    antivirus_enabled = models.BooleanField(
        default=True,
        help_text='Is antivirus enabled'
    )

    # Active Directory Information
    ad_domain = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Active Directory domain'
    )
    ad_computer_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='AD computer name'
    )

    def __str__(self):
        return f"IT Info: {self.asset.asset_name if self.asset else 'N/A'}"

    def get_full_config(self):
        """
        Get full configuration summary as a formatted string.

        Returns a human-readable summary of the IT asset configuration.
        """
        parts = []

        # CPU
        if self.cpu_model:
            cpu_info = self.cpu_model
            if self.cpu_cores:
                cpu_info += f" ({self.cpu_cores} cores"
                if self.cpu_threads:
                    cpu_info += f" / {self.cpu_threads} threads"
                cpu_info += ")"
            parts.append(f"CPU: {cpu_info}")

        # RAM
        if self.ram_capacity:
            ram_info = f"{self.ram_capacity}GB"
            if self.ram_type:
                ram_info += f" {self.ram_type}"
            parts.append(f"RAM: {ram_info}")

        # Disk
        if self.disk_capacity:
            disk_info = f"{self.disk_capacity}GB"
            if self.disk_type:
                disk_info += f" {self.disk_type}"
            if self.disk_count and self.disk_count > 1:
                disk_info += f" x{self.disk_count}"
            parts.append(f"Disk: {disk_info}")

        # GPU
        if self.gpu_model:
            gpu_info = self.gpu_model
            if self.gpu_memory:
                gpu_info += f" ({self.gpu_memory}MB)"
            parts.append(f"GPU: {gpu_info}")

        # OS
        if self.os_name:
            os_info = self.os_name
            if self.os_version:
                os_info += f" {self.os_version}"
            if self.os_architecture:
                os_info += f" ({self.os_architecture})"
            parts.append(f"OS: {os_info}")

        # Network
        if self.hostname:
            parts.append(f"Hostname: {self.hostname}")
        if self.ip_address:
            parts.append(f"IP: {self.ip_address}")

        return " | ".join(parts) if parts else "No configuration available"


class Software(BaseModel):
    """
    Software catalog model.

    Represents software products available in the organization.
    """

    class Meta:
        db_table = 'software'
        verbose_name = 'Software'
        verbose_name_plural = 'Software'
        ordering = ['name', 'version']
        indexes = [
            models.Index(fields=['organization', 'name']),
            models.Index(fields=['organization', 'vendor']),
            models.Index(fields=['organization', 'category']),
        ]

    name = models.CharField(
        max_length=200,
        help_text='Software name'
    )
    vendor = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Software vendor/manufacturer'
    )
    version = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Software version'
    )
    category = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Software category (e.g., Productivity, Security, Development)'
    )

    LICENSE_TYPE_CHOICES = [
        ('open_source', 'Open Source'),
        ('freeware', 'Freeware'),
        ('commercial', 'Commercial'),
        ('enterprise', 'Enterprise'),
        ('subscription', 'Subscription'),
        ('oem', 'OEM'),
    ]
    license_type = models.CharField(
        max_length=50,
        choices=LICENSE_TYPE_CHOICES,
        default='commercial',
        help_text='Type of software license'
    )

    description = models.TextField(
        blank=True,
        null=True,
        help_text='Software description'
    )
    website_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text='Official website URL'
    )

    def __str__(self):
        version_str = f" {self.version}" if self.version else ""
        return f"{self.name}{version_str}"


class SoftwareLicense(BaseModel):
    """
    Software License model.

    Tracks purchased licenses and their usage.
    """

    class Meta:
        db_table = 'software_license'
        verbose_name = 'Software License'
        verbose_name_plural = 'Software Licenses'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'software']),
            models.Index(fields=['organization', 'license_key']),
        ]

    software = models.ForeignKey(
        Software,
        on_delete=models.CASCADE,
        related_name='licenses',
        help_text='Related software'
    )

    license_key = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text='License key or serial number'
    )

    seats = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text='Total number of licensed seats'
    )

    seats_used = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Number of seats currently in use'
    )

    purchase_date = models.DateField(
        blank=True,
        null=True,
        help_text='License purchase date'
    )

    expiry_date = models.DateField(
        blank=True,
        null=True,
        help_text='License expiration date (null for perpetual)'
    )

    cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text='License purchase cost'
    )

    currency = models.CharField(
        max_length=10,
        default='USD',
        help_text='Currency for cost field'
    )

    LICENSE_STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
    ]
    status = models.CharField(
        max_length=20,
        choices=LICENSE_STATUS_CHOICES,
        default='active',
        help_text='License status'
    )

    vendor_reference = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Vendor reference or purchase order number'
    )

    notes = models.TextField(
        blank=True,
        null=True,
        help_text='Additional notes'
    )

    def __str__(self):
        return f"{self.software.name} - {self.license_key or 'No Key'} ({self.seats_used}/{self.seats} seats)"

    def available_seats(self):
        """Calculate number of available seats."""
        available = self.seats - self.seats_used
        return max(0, available)

    def is_expired(self):
        """Check if the license is expired."""
        if self.expiry_date is None:
            return False  # Perpetual license
        from django.utils import timezone
        return self.expiry_date < timezone.now().date()


class LicenseAllocation(BaseModel):
    """
    License Allocation model.

    Tracks which assets have been allocated software licenses.
    Automatically updates license seat usage.
    """

    class Meta:
        db_table = 'license_allocation'
        verbose_name = 'License Allocation'
        verbose_name_plural = 'License Allocations'
        ordering = ['-allocated_date']
        indexes = [
            models.Index(fields=['organization', 'license']),
            models.Index(fields=['organization', 'asset']),
            models.Index(fields=['organization', 'asset', 'license']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['asset', 'license', 'deallocated_date'],
                condition=models.Q(deallocated_date__isnull=True),
                name='unique_active_allocation'
            )
        ]

    license = models.ForeignKey(
        SoftwareLicense,
        on_delete=models.CASCADE,
        related_name='allocations',
        help_text='Allocated license'
    )

    asset = models.ForeignKey(
        'assets.Asset',
        on_delete=models.CASCADE,
        related_name='license_allocations',
        help_text='Asset that received the license'
    )

    allocated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='license_allocated',
        help_text='User who allocated the license'
    )

    allocated_date = models.DateField(
        help_text='Date when the license was allocated'
    )

    deallocated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='license_deallocated',
        help_text='User who deallocated the license'
    )

    deallocated_date = models.DateField(
        blank=True,
        null=True,
        help_text='Date when the license was deallocated (null if active)'
    )

    notes = models.TextField(
        blank=True,
        null=True,
        help_text='Notes about this allocation'
    )

    def __str__(self):
        status = "Active" if self.is_active() else "Deallocated"
        return f"{self.license.software.name} -> {self.asset.asset_name} ({status})"

    def is_active(self):
        """Check if the allocation is currently active."""
        return self.deallocated_date is None

    def save(self, *args, **kwargs):
        """
        Override save to update license seats_used count.
        """
        # Track if this is a new allocation or being deallocated
        # Note: self.pk is set before first save due to default=uuid.uuid4
        # So we need to check if the record exists in DB
        try:
            old_instance = LicenseAllocation.objects.get(pk=self.pk)
            is_new = False
        except LicenseAllocation.DoesNotExist:
            old_instance = None
            is_new = True

        # Determine if deallocation status changed
        was_active = old_instance.is_active() if old_instance else False
        is_active_now = self.deallocated_date is None

        # Save the instance
        super().save(*args, **kwargs)

        # Update license seats_used using direct query to avoid any caching issues
        if is_new and is_active_now:
            # New active allocation - increment seats_used
            SoftwareLicense.objects.filter(pk=self.license.pk).update(
                seats_used=models.F('seats_used') + 1
            )
        elif old_instance and was_active and not is_active_now:
            # Allocation being deallocated - decrement seats_used (ensure not negative)
            SoftwareLicense.objects.filter(pk=self.license.pk).update(
                seats_used=Greatest(models.F('seats_used') - 1, 0)
            )
