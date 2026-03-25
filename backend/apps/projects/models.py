"""
Asset project management models for GZEAMS.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Union

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone

from apps.common.models import BaseModel


def _normalize_decimal(
    value: Optional[Union[Decimal, int, float, str]],
    default: str = "0",
) -> Decimal:
    """Normalize arbitrary numeric input into Decimal."""
    if value in (None, ""):
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


class AssetProject(BaseModel):
    """Project definition for project-based asset allocation and accounting."""

    PROJECT_TYPE_CHOICES = [
        ("research", "Research"),
        ("development", "Development"),
        ("infrastructure", "Infrastructure"),
        ("implementation", "Implementation"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("planning", "Planning"),
        ("active", "Active"),
        ("suspended", "Suspended"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    project_code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Project code (auto-generated: XM+YYYYMM+NNNN)",
    )
    project_name = models.CharField(
        max_length=200,
        help_text="Project name",
    )
    project_alias = models.CharField(
        max_length=100,
        blank=True,
        help_text="Project alias or short name",
    )
    project_manager = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="managed_asset_projects",
        help_text="Project manager",
    )
    department = models.ForeignKey(
        "organizations.Department",
        on_delete=models.PROTECT,
        related_name="asset_projects",
        help_text="Owning department",
    )
    project_type = models.CharField(
        max_length=20,
        choices=PROJECT_TYPE_CHOICES,
        default="development",
        help_text="Project type",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="planning",
        db_index=True,
        help_text="Project status",
    )
    start_date = models.DateField(
        help_text="Planned start date",
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Planned end date",
    )
    actual_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Actual start date",
    )
    actual_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Actual end date",
    )
    planned_budget = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Planned budget amount",
    )
    actual_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Actual incurred cost",
    )
    asset_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Allocated asset cost",
    )
    description = models.TextField(
        blank=True,
        help_text="Project description",
    )
    technical_requirements = models.TextField(
        blank=True,
        help_text="Technical requirements",
    )
    total_assets = models.IntegerField(
        default=0,
        help_text="Total allocated assets",
    )
    active_assets = models.IntegerField(
        default=0,
        help_text="Currently active allocated assets",
    )
    completed_milestones = models.IntegerField(
        default=0,
        help_text="Completed milestone count",
    )
    total_milestones = models.IntegerField(
        default=0,
        help_text="Total milestone count",
    )

    class Meta:
        db_table = "asset_projects"
        verbose_name = "Asset Project"
        verbose_name_plural = "Asset Projects"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["organization", "project_code"]),
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["organization", "project_type"]),
            models.Index(fields=["organization", "department"]),
            models.Index(fields=["organization", "project_manager"]),
            models.Index(fields=["organization", "start_date", "end_date"]),
        ]

    def __str__(self):
        return f"{self.project_code} - {self.project_name}"

    def save(self, *args, **kwargs):
        if not self.project_code:
            self.project_code = self._generate_project_code()
        super().save(*args, **kwargs)

    def _generate_project_code(self) -> str:
        """Generate a project code using the current year and month."""
        prefix = timezone.now().strftime("%Y%m")
        last_project = AssetProject.all_objects.filter(
            project_code__startswith=f"XM{prefix}"
        ).order_by("-project_code").first()
        if last_project:
            sequence = int(last_project.project_code[-4:]) + 1
        else:
            sequence = 1
        return f"XM{prefix}{sequence:04d}"

    def refresh_rollups(self, save: bool = True):
        """Refresh denormalized asset allocation metrics for the project."""
        allocations = self.project_assets.filter(is_deleted=False)
        total_assets = allocations.count()
        active_assets = allocations.filter(return_status="in_use").count()
        asset_cost = allocations.aggregate(total=Sum("allocation_cost")).get("total") or Decimal("0")

        changed_fields = []
        if self.total_assets != total_assets:
            self.total_assets = total_assets
            changed_fields.append("total_assets")
        if self.active_assets != active_assets:
            self.active_assets = active_assets
            changed_fields.append("active_assets")
        if self.asset_cost != asset_cost:
            self.asset_cost = asset_cost
            changed_fields.append("asset_cost")

        if save and changed_fields:
            self.save(update_fields=changed_fields + ["updated_at"])

        return {
            "total_assets": self.total_assets,
            "active_assets": self.active_assets,
            "asset_cost": self.asset_cost,
        }


class ProjectAsset(BaseModel):
    """Asset allocation record for a project."""

    ALLOCATION_TYPE_CHOICES = [
        ("permanent", "Permanent"),
        ("temporary", "Temporary"),
        ("shared", "Shared"),
    ]

    RETURN_STATUS_CHOICES = [
        ("in_use", "In Use"),
        ("returned", "Returned"),
        ("transferred", "Transferred"),
    ]

    project = models.ForeignKey(
        "projects.AssetProject",
        on_delete=models.PROTECT,
        related_name="project_assets",
        help_text="Assigned project",
    )
    asset = models.ForeignKey(
        "assets.Asset",
        on_delete=models.PROTECT,
        related_name="project_allocations",
        help_text="Allocated asset",
    )
    allocation_no = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Allocation number (auto-generated: FP+YYYYMM+NNNN)",
    )
    allocation_date = models.DateField(
        default=timezone.now,
        help_text="Allocation date",
    )
    allocation_type = models.CharField(
        max_length=20,
        choices=ALLOCATION_TYPE_CHOICES,
        default="permanent",
        help_text="Allocation type",
    )
    allocated_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="project_assets_allocated",
        help_text="User who allocated the asset",
    )
    custodian = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_assets_custodied",
        help_text="Current custodian",
    )
    return_date = models.DateField(
        null=True,
        blank=True,
        help_text="Planned return date",
    )
    actual_return_date = models.DateField(
        null=True,
        blank=True,
        help_text="Actual return date",
    )
    return_status = models.CharField(
        max_length=20,
        choices=RETURN_STATUS_CHOICES,
        default="in_use",
        help_text="Asset return status",
    )
    allocation_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Asset cost snapshot at allocation time",
    )
    depreciation_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        default=Decimal("1.0000"),
        validators=[MinValueValidator(0)],
        help_text="Depreciation share ratio",
    )
    monthly_depreciation = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Monthly depreciation amount allocated to the project",
    )
    purpose = models.TextField(
        blank=True,
        help_text="Usage purpose",
    )
    usage_location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Usage location",
    )
    asset_snapshot = models.JSONField(
        default=dict,
        blank=True,
        help_text="Asset snapshot at allocation time",
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes",
    )

    class Meta:
        db_table = "project_assets"
        verbose_name = "Project Asset"
        verbose_name_plural = "Project Assets"
        ordering = ["-allocation_date", "-created_at"]
        indexes = [
            models.Index(fields=["organization", "project"]),
            models.Index(fields=["organization", "asset"]),
            models.Index(fields=["organization", "return_status"]),
            models.Index(fields=["organization", "allocation_date"]),
            models.Index(fields=["organization", "custodian"]),
        ]

    def __str__(self):
        return f"{self.allocation_no} - {self.project.project_name}"

    def save(self, *args, **kwargs):
        if not self.allocation_no:
            self.allocation_no = self._generate_allocation_no()

        if self.asset_id:
            asset = self.asset
            if _normalize_decimal(self.allocation_cost) <= Decimal("0"):
                self.allocation_cost = asset.current_value or asset.purchase_price
            if not self.asset_snapshot:
                self.asset_snapshot = self._build_asset_snapshot(asset)
            if _normalize_decimal(self.monthly_depreciation) <= Decimal("0") and getattr(asset, "useful_life", 0):
                monthly = (
                    _normalize_decimal(self.allocation_cost)
                    * _normalize_decimal(self.depreciation_rate, default="1")
                    / Decimal(str(max(int(asset.useful_life or 0), 1)))
                )
                self.monthly_depreciation = monthly.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        super().save(*args, **kwargs)

        if self.project_id:
            self.project.refresh_rollups()

    def soft_delete(self, user=None):
        """Soft delete the allocation and refresh project rollups."""
        super().soft_delete(user=user)
        if self.project_id:
            self.project.refresh_rollups()

    def _generate_allocation_no(self) -> str:
        """Generate an allocation number."""
        prefix = timezone.now().strftime("%Y%m")
        last_allocation = ProjectAsset.all_objects.filter(
            allocation_no__startswith=f"FP{prefix}"
        ).order_by("-allocation_no").first()
        if last_allocation:
            sequence = int(last_allocation.allocation_no[-4:]) + 1
        else:
            sequence = 1
        return f"FP{prefix}{sequence:04d}"

    @staticmethod
    def _build_asset_snapshot(asset) -> dict:
        """Create an immutable snapshot from the linked asset."""
        return {
            "asset_code": getattr(asset, "asset_code", ""),
            "asset_name": getattr(asset, "asset_name", ""),
            "category_name": getattr(getattr(asset, "asset_category", None), "name", ""),
            "department_name": getattr(getattr(asset, "department", None), "name", ""),
            "purchase_price": str(getattr(asset, "purchase_price", "") or ""),
            "current_value": str(getattr(asset, "current_value", "") or ""),
            "purchase_date": str(getattr(asset, "purchase_date", "") or ""),
            "asset_status": getattr(asset, "asset_status", ""),
        }


class ProjectMember(BaseModel):
    """Project membership and permission assignment."""

    ROLE_CHOICES = [
        ("manager", "Manager"),
        ("member", "Member"),
        ("observer", "Observer"),
    ]

    project = models.ForeignKey(
        "projects.AssetProject",
        on_delete=models.CASCADE,
        related_name="members",
        help_text="Associated project",
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        related_name="project_memberships",
        help_text="Project member",
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="member",
        help_text="Project role",
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Whether the user is the primary member",
    )
    join_date = models.DateField(
        default=timezone.now,
        help_text="Join date",
    )
    leave_date = models.DateField(
        null=True,
        blank=True,
        help_text="Leave date",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the membership is active",
    )
    responsibilities = models.TextField(
        blank=True,
        help_text="Responsibility summary",
    )
    can_allocate_asset = models.BooleanField(
        default=False,
        help_text="Whether the member can allocate assets",
    )
    can_view_cost = models.BooleanField(
        default=False,
        help_text="Whether the member can view cost data",
    )

    class Meta:
        db_table = "project_members"
        verbose_name = "Project Member"
        verbose_name_plural = "Project Members"
        ordering = ["-is_primary", "join_date", "created_at"]
        unique_together = [("project", "user")]
        indexes = [
            models.Index(fields=["organization", "project"]),
            models.Index(fields=["organization", "user"]),
            models.Index(fields=["organization", "is_active"]),
            models.Index(fields=["organization", "role"]),
        ]

    def __str__(self):
        return f"{self.project.project_name} - {self.user.username}"

    def save(self, *args, **kwargs):
        if self.is_primary and self.project_id:
            ProjectMember.all_objects.filter(
                project_id=self.project_id,
                is_deleted=False,
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
