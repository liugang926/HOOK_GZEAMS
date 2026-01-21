"""
IT Asset models for GZEAMS.
"""
from django.db import models
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
