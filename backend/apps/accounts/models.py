"""
User and authentication models with multi-organization support.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from apps.common.models import BaseModel


class UserOrganization(models.Model):
    """
    Through model for User-Organization many-to-many relationship.

    Tracks user membership in organizations with role information.
    """

    # Role choices
    ROLE_CHOICES = [
        ('admin', 'Administrator'),  # Full access to organization
        ('member', 'Member'),        # Standard access
        ('auditor', 'Auditor'),      # Read-only access
    ]

    # === Fields ===
    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='user_orgs',
        db_comment='User reference'
    )
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='org_users',
        db_comment='Organization reference'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member',
        db_comment='User role in this organization'
    )
    is_active = models.BooleanField(
        default=True,
        db_comment='Is this membership active'
    )
    is_primary = models.BooleanField(
        default=False,
        db_comment='Is this the user primary organization'
    )
    joined_at = models.DateTimeField(
        auto_now_add=True,
        db_comment='When user joined the organization'
    )
    invited_by = models.ForeignKey(
        'User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invited_users',
        db_comment='User who sent the invitation'
    )

    class Meta:
        db_table = 'user_organizations'
        unique_together = [['user', 'organization']]
        verbose_name = 'User Organization'
        verbose_name_plural = 'User Organizations'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['is_primary']),
        ]

    def __str__(self):
        return f"{self.user.username} @ {self.organization.name} ({self.role})"

    def save(self, *args, **kwargs):
        """
        Override save to enforce business rules.

        - Ensure only one primary organization per user
        """
        if self.is_primary:
            # Set all other user_orgs for this user to is_primary=False
            UserOrganization.objects.filter(
                user=self.user
            ).exclude(
                pk=self.pk
            ).update(is_primary=False)

        super().save(*args, **kwargs)

    def clean(self):
        """Validate constraints."""
        from django.core.exceptions import ValidationError

        # Check if user already has this organization
        if UserOrganization.objects.filter(
            user=self.user,
            organization=self.organization
        ).exclude(pk=self.pk).exists():
            raise ValidationError({
                'organization': 'User already has this organization.'
            })


class User(AbstractUser, BaseModel):
    """
    Custom User model extending Django's AbstractUser.

    Adds multi-organization support with ability to belong to multiple
    organizations and switch between them.
    """

    # === Current Organization ===
    # The organization the user is currently logged in as
    current_organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='current_users',
        db_comment='User current selected organization'
    )

    # === SSO Integration Fields ===
    # WeChat Work (企业微信)
    wework_userid = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        unique=True,
        db_comment='WeChat Work User ID',
        db_index=True
    )
    wework_unionid = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        unique=True,
        db_comment='WeChat Work Union ID'
    )

    # DingTalk (钉钉)
    dingtalk_userid = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        unique=True,
        db_comment='DingTalk User ID',
        db_index=True
    )
    dingtalk_unionid = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        unique=True,
        db_comment='DingTalk Union ID'
    )

    # Feishu (飞书)
    feishu_userid = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        unique=True,
        db_comment='Feishu User ID',
        db_index=True
    )
    feishu_unionid = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        unique=True,
        db_comment='Feishu Union ID'
    )

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['wework_userid']),
            models.Index(fields=['dingtalk_userid']),
            models.Index(fields=['feishu_userid']),
        ]

    def __str__(self):
        return f"{self.username} ({self.get_full_name() or 'No Name'})"

    def get_accessible_organizations(self):
        """
        Get all organizations this user has access to.

        Returns:
            QuerySet: Organizations where user has active membership
        """
        if not self.pk:
            from apps.organizations.models import Organization
            return Organization.objects.none()

        org_ids = self.user_orgs.filter(
            is_active=True
        ).values_list('organization_id', flat=True)
        from apps.organizations.models import Organization
        return Organization.objects.filter(
            id__in=org_ids,
            is_deleted=False
        )

    def get_org_role(self, org_id):
        """
        Get the user's role in a specific organization.

        Args:
            org_id: UUID of the organization

        Returns:
            str: Role name (admin, member, auditor) or None
        """
        if not self.pk:
            return None
        user_org = self.user_orgs.filter(
            organization_id=org_id,
            is_active=True
        ).first()
        return user_org.role if user_org else None

    def switch_organization(self, org_id):
        """
        Switch the user's current organization.

        Args:
            org_id: UUID of the organization to switch to

        Returns:
            bool: True if successful, False otherwise
        """
        accessible_ids = self.get_accessible_organizations().values_list(
            'id', flat=True
        )
        if str(org_id) not in [str(oid) for oid in accessible_ids]:
            return False

        self.current_organization_id = org_id
        self.save(update_fields=['current_organization'])

        # Update is_primary on UserOrganization
        self.user_orgs.filter(organization_id=org_id).update(is_primary=True)
        self.user_orgs.exclude(organization_id=org_id).update(is_primary=False)

        return True

    def get_primary_organization(self):
        """
        Get the user's primary (default) organization.

        Returns:
            Organization: The primary organization or None
        """
        if not self.pk:
            return None

        primary_user_org = self.user_orgs.filter(
            is_primary=True,
            is_active=True
        ).select_related('organization').first()

        if primary_user_org:
            return primary_user_org.organization

        # Fallback to first accessible organization
        first_org = self.get_accessible_organizations().first()
        return first_org
