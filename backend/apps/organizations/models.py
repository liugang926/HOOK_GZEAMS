"""
Organization models for multi-tenant support.
"""
from django.db import models
import uuid
import secrets
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.common.models import BaseModel

User = get_user_model()


class Organization(models.Model):
    """
    Organization model for multi-tenant support.

    This is a standalone model (does not inherit from BaseModel)
    to avoid circular dependency since BaseModel has an
    organization ForeignKey.

    Supports hierarchical organization structure with parent-child relationships.
    """

    # Organization type choices
    ORG_TYPE_CHOICES = [
        ('group', 'Group'),          # 集团
        ('company', 'Company'),      # 公司
        ('branch', 'Branch'),        # 分支机构
        ('department', 'Department'), # 部门
    ]

    # === Basic Information ===
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(max_length=200, db_comment='Organization name')
    code = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        db_comment='Organization code (unique)'
    )

    # === Hierarchy Fields ===
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        db_comment='Parent organization'
    )
    level = models.IntegerField(
        default=0,
        editable=False,
        db_comment='Hierarchy level (0=root)'
    )
    path = models.CharField(
        max_length=500,
        editable=False,
        db_comment='Organization path (e.g., /group/company/branch)'
    )

    # === Organization Type ===
    org_type = models.CharField(
        max_length=20,
        choices=ORG_TYPE_CHOICES,
        default='company',
        db_comment='Organization type'
    )

    # === Contact Information ===
    contact_person = models.CharField(
        max_length=100,
        blank=True,
        db_comment='Contact person name'
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        db_comment='Contact phone number'
    )
    email = models.EmailField(
        blank=True,
        db_comment='Organization email'
    )
    address = models.TextField(
        blank=True,
        db_comment='Organization address'
    )

    # === Financial Information ===
    credit_code = models.CharField(
        max_length=50,
        blank=True,
        db_comment='Unified social credit code (for finance integration)'
    )

    # === Status ===
    is_active = models.BooleanField(
        default=True,
        db_comment='Is organization active'
    )
    is_deleted = models.BooleanField(
        default=False,
        db_comment='Soft delete flag'
    )

    # === Configuration ===
    settings = models.JSONField(
        default=dict,
        db_comment='Organization-level settings'
    )

    # === WeWork Integration Fields ===
    # These fields store WeWork (企业微信) department mapping
    wework_dept_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        db_comment='WeWork department ID for sync'
    )
    wework_parent_id = models.IntegerField(
        null=True,
        blank=True,
        db_comment='WeWork parent department ID'
    )

    # === Invite Code ===
    invite_code = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        db_comment='Invite code for joining organization'
    )
    invite_code_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_comment='Invite code expiration time'
    )

    # === Audit Fields ===
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_comment='Creation timestamp'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_comment='Last update timestamp'
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_organizations',
        db_comment='User who created this organization'
    )

    # Custom managers
    objects = models.Manager()  # Default manager - filter by is_deleted=False in get_queryset
    all_objects = models.Manager()  # Returns all records including deleted

    class Meta:
        db_table = 'organizations'
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['parent']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_deleted']),
            models.Index(fields=['invite_code']),
            models.Index(fields=['wework_dept_id']),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    def save(self, *args, **kwargs):
        """
        Override save to auto-calculate hierarchy fields.

        - level: parent.level + 1 or 0 for root
        - path: parent.path + / + code or / + code for root
        """
        # Track if this is a new instance (before super().save())
        is_new = self._state.adding

        # Calculate level and path based on parent
        if self.parent:
            self.level = self.parent.level + 1
            self.path = f"{self.parent.path}/{self.code}"
        else:
            self.level = 0
            self.path = f"/{self.code}"

        # For new organizations without invite code, generate one
        if is_new and not self.invite_code:
            self._generate_invite_code()

        super().save(*args, **kwargs)

    def get_all_children(self):
        """
        Get all descendant organizations recursively.

        Returns:
            QuerySet: All descendant organizations
        """
        if not self.pk:
            return Organization.objects.none()

        # Get all organizations whose path starts with this organization's path
        # and has a deeper level
        return Organization.objects.filter(
            path__startswith=f"{self.path}/",
            is_deleted=False
        )

    def _generate_invite_code(self, days_valid=30):
        """
        Generate a new 8-character random invite code without saving.

        This internal method only sets the fields without calling save(),
        to avoid recursion issues during object creation.

        Args:
            days_valid: Number of days the code remains valid (default: 30)
        """
        # Generate unique 8-character code
        import random
        import string

        max_attempts = 100
        for _ in range(max_attempts):
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            # Use all_objects to avoid filtering issues
            if not Organization.all_objects.filter(invite_code=code).exists():
                self.invite_code = code
                break

        # Set expiration
        self.invite_code_expires_at = timezone.now() + timedelta(days=days_valid)

    def regenerate_invite_code(self, days_valid=30):
        """
        Generate a new 8-character random invite code and save to database.

        Args:
            days_valid: Number of days the code remains valid (default: 30)
        """
        # Generate the code
        self._generate_invite_code(days_valid)
        # Save to database
        self.save(update_fields=['invite_code', 'invite_code_expires_at'])

    def is_invite_code_valid(self):
        """Check if the invite code is valid and not expired."""
        if not self.invite_code:
            return False
        if not self.is_active:
            return False
        if self.invite_code_expires_at:
            return timezone.now() < self.invite_code_expires_at
        return True

    def clean(self):
        """Validate organization constraints."""
        # Prevent setting self as parent
        if self.parent and self.parent_id == self.pk:
            raise ValidationError({"parent": "An organization cannot be its own parent."})

        # Prevent circular parent references
        if self.parent:
            if self.get_all_children().filter(id=self.parent_id).exists():
                raise ValidationError({"parent": "Circular parent reference detected."})

    @classmethod
    def get_default_organization(cls):
        """
        Get or create the default organization.

        This is used for system initialization when no organizations exist.

        Returns:
            Organization: The default organization
        """
        defaults = {
            'name': 'Default Organization',
            'code': 'DEFAULT',
            'org_type': 'company',
            'is_active': True,
        }
        org, created = cls.objects.get_or_create(
            code='DEFAULT',
            defaults=defaults
        )
        if created:
            org.regenerate_invite_code()
        return org

    @classmethod
    def initialize_default_organization(cls):
        """
        Initialize the default organization for a new installation.

        This should be called during system setup to ensure there's
        always at least one organization available.

        Returns:
            Organization: The default organization
        """
        return cls.get_default_organization()


class Department(BaseModel):
    """
    Department model - inherits from BaseModel.

    Supports hierarchical department structure with parent-child relationships.
    Includes leader designation, full path tracking, and SSO sync fields.
    """

    # Basic Information
    code = models.CharField(
        max_length=50,
        db_index=True,
        db_comment='Department code (unique per organization)'
    )
    name = models.CharField(
        max_length=100,
        db_comment='Department name'
    )

    # Hierarchy Fields
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        db_comment='Parent department'
    )
    level = models.IntegerField(
        default=0,
        editable=False,
        db_comment='Hierarchy level (0=root)'
    )
    path = models.CharField(
        max_length=500,
        default='',
        editable=False,
        db_comment='Department code path (e.g., /HQ/TECH)'
    )
    order = models.IntegerField(
        default=0,
        db_comment='Display order'
    )

    # Full path display (e.g., "总部/技术部/后端组")
    full_path = models.CharField(
        max_length=500,
        default='',
        editable=False,
        db_comment='Full path for display'
    )
    full_path_name = models.CharField(
        max_length=1000,
        default='',
        editable=False,
        db_comment='Full path with names (e.g., "Headquarters/Technology/Backend")'
    )

    # Department Leader
    leader = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='led_departments',
        db_comment='Department leader'
    )

    # SSO sync fields - WeWork
    wework_dept_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        db_comment='WeWork department ID for sync'
    )
    wework_leader_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_comment='WeWork leader user ID'
    )

    # SSO sync fields - DingTalk
    dingtalk_dept_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        db_comment='DingTalk department ID for sync'
    )
    dingtalk_leader_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_comment='DingTalk leader user ID'
    )

    # SSO sync fields - Feishu
    feishu_dept_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        db_index=True,
        db_comment='Feishu department ID for sync'
    )
    feishu_leader_id = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        db_comment='Feishu leader user ID'
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        db_comment='Is department active'
    )

    class Meta:
        db_table = 'departments'
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'
        unique_together = [['organization', 'code']]
        indexes = [
            models.Index(fields=['organization', 'parent']),
            models.Index(fields=['organization', 'wework_dept_id']),
            models.Index(fields=['level']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.full_path_name} ({self.code})"

    def save(self, *args, **kwargs):
        """
        Override save to auto-calculate hierarchy fields.

        - level: parent.level + 1 or 0 for root
        - path: parent.path + / + code or / + code for root
        - full_path: parent.full_path + / + name or name for root
        - full_path_name: parent.full_path_name + / + name or name for root
        """
        # Calculate level and path based on parent
        if self.parent:
            self.level = self.parent.level + 1
            self.path = f"{self.parent.path}/{self.code}" if self.parent.path else f"/{self.code}"
            self.full_path = f"{self.parent.full_path}/{self.name}" if self.parent.full_path else self.name
            self.full_path_name = f"{self.parent.full_path_name}/{self.name}" if self.parent.full_path_name else self.name
        else:
            self.level = 0
            self.path = f"/{self.code}"
            self.full_path = self.name
            self.full_path_name = self.name

        super().save(*args, **kwargs)

        # Recursively update children paths
        self._update_children_paths()

    def _update_children_paths(self):
        """Update all children department paths."""
        for child in self.children.filter(is_deleted=False):
            child.save(update_fields=['level', 'path', 'full_path', 'full_path_name'])

    def get_descendant_ids(self):
        """
        Get all descendant department IDs.

        Returns:
            list: List of department IDs including self and all descendants
        """
        ids = [self.id]
        for child in self.children.filter(is_deleted=False):
            ids.extend(child.get_descendant_ids())
        return ids

    def get_ancestor_ids(self):
        """
        Get all ancestor department IDs.

        Returns:
            list: List of ancestor department IDs
        """
        ids = []
        current = self.parent
        while current and not current.is_deleted:
            ids.append(current.id)
            current = current.parent
        return ids

    def get_full_tree(self):
        """
        Get full tree as nested dict structure.

        Returns:
            dict: Tree structure with descendants
        """
        return {
            'id': str(self.id),
            'code': self.code,
            'name': self.name,
            'full_path': self.full_path,
            'full_path_name': self.full_path_name,
            'level': self.level,
            'leader_id': str(self.leader_id) if self.leader_id else None,
            'is_active': self.is_active,
            'children': [
                child.get_full_tree()
                for child in self.children.filter(is_deleted=False, is_active=True)
            ]
        }

    def clean(self):
        """Validate department constraints."""
        # Prevent setting self as parent
        if self.parent and self.parent_id == self.pk:
            raise ValidationError({"parent": "A department cannot be its own parent."})

        # Prevent circular references
        if self.parent:
            descendant_ids = self.get_descendant_ids()
            if self.parent_id in descendant_ids:
                raise ValidationError({"parent": "Circular parent reference detected."})


class UserDepartment(BaseModel):
    """
    User-Department association model - supports multiple departments per user.

    A user can belong to multiple departments with different roles in each.
    One department can be marked as primary (for asset ownership default).
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_departments',
        db_comment='Associated user'
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='user_departments',
        db_comment='Associated department'
    )

    # Is this the primary department (for asset ownership)
    is_primary = models.BooleanField(
        default=False,
        db_comment='Is primary department for asset ownership'
    )

    # Is this the asset department (for asset management)
    is_asset_department = models.BooleanField(
        default=False,
        db_comment='Is department for asset management purposes'
    )

    # Job position/title in this department
    position = models.CharField(
        max_length=100,
        blank=True,
        db_comment='Job position in this department'
    )

    # Is user a leader in this department
    is_leader = models.BooleanField(
        default=False,
        db_comment='Is user a leader in this department'
    )

    # WeWork sync fields
    wework_department_order = models.IntegerField(
        null=True,
        blank=True,
        db_comment='WeWork department order'
    )
    is_primary_in_wework = models.BooleanField(
        default=False,
        db_comment='Is primary department in WeWork'
    )

    class Meta:
        db_table = 'user_departments'
        verbose_name = 'User Department'
        verbose_name_plural = 'User Departments'
        unique_together = [['user', 'organization', 'department']]
        indexes = [
            models.Index(fields=['user', 'organization']),
            models.Index(fields=['department']),
            models.Index(fields=['is_primary']),
            models.Index(fields=['is_leader']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.department.full_path_name}"

    def save(self, *args, **kwargs):
        """
        Override save to ensure only one primary department per user per org.

        When setting is_primary=True, all other user departments for the
        same organization will have is_primary set to False.
        """
        super().save(*args, **kwargs)

        # Ensure only one primary department per user per organization
        if self.is_primary:
            UserDepartment.objects.filter(
                user=self.user,
                organization=self.organization,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)

    @classmethod
    def get_user_primary_department(cls, user_id, organization_id):
        """
        Get user's primary department for an organization.

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            UserDepartment or None
        """
        return cls.objects.filter(
            user_id=user_id,
            organization_id=organization_id,
            is_primary=True,
            is_deleted=False
        ).select_related('department').first()

    @classmethod
    def get_user_departments(cls, user_id, organization_id):
        """
        Get all departments for a user in an organization.

        Args:
            user_id: User ID
            organization_id: Organization ID

        Returns:
            QuerySet: UserDepartment queryset
        """
        return cls.objects.filter(
            user_id=user_id,
            organization_id=organization_id,
            is_deleted=False
        ).select_related('department')
