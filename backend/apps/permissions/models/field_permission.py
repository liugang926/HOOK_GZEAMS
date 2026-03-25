"""
FieldPermission Model - Field-level permission control.

Defines granular permissions for individual fields on content types.
Supports read, write, hidden, and masked permission types.
"""
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class FieldPermission(BaseModel):
    """
    Field-level permission for controlling access to specific model fields.

    Permission types:
    - read: Field can be viewed
    - write: Field can be edited
    - hidden: Field is completely hidden
    - masked: Field value is partially masked (e.g., phone: ***1234)
    """

    # Permission type choices
    PERMISSION_TYPE_CHOICES = [
        ('read', _('Read')),
        ('write', _('Write')),
        ('hidden', _('Hidden')),
        ('masked', _('Masked')),
    ]

    # Mask rule choices
    MASK_RULE_CHOICES = [
        ('phone', _('Phone - Keep first 3 and last 4 digits')),
        ('id_card', _('ID Card - Keep first 3 and last 4 digits')),
        ('bank_card', _('Bank Card - Keep last 4 digits')),
        ('name', _('Name - Keep last character')),
        ('email', _('Email - Mask local part')),
        ('amount', _('Amount - Show range only')),
        ('custom', _('Custom masking rule')),
    ]

    # Target assignment (user-specific)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name='field_permissions',
        verbose_name=_('User'),
        db_comment='User this permission applies to'
    )

    # Content type binding (which model and field)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='field_permissions',
        verbose_name=_('Content Type'),
        db_comment='Model this permission applies to'
    )
    field_name = models.CharField(
        max_length=100,
        verbose_name=_('Field Name'),
        db_comment='Name of the field this permission controls'
    )

    # Permission configuration
    permission_type = models.CharField(
        max_length=20,
        choices=PERMISSION_TYPE_CHOICES,
        default='read',
        verbose_name=_('Permission Type'),
        db_comment='Type of permission: read/write/hidden/masked'
    )
    mask_rule = models.CharField(
        max_length=50,
        choices=MASK_RULE_CHOICES,
        null=True,
        blank=True,
        verbose_name=_('Mask Rule'),
        db_comment='Masking rule when permission_type is masked'
    )
    custom_mask_pattern = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name=_('Custom Mask Pattern'),
        db_comment='Custom regex pattern for masking (when mask_rule=custom)'
    )

    # Condition for applying permission (optional)
    condition = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('Condition'),
        db_comment='Conditional expression for when this permission applies'
    )

    # Priority for conflict resolution
    priority = models.IntegerField(
        default=0,
        verbose_name=_('Priority'),
        db_comment='Higher priority permissions override lower ones'
    )

    # Metadata
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        db_comment='Description of what this permission controls'
    )

    class Meta:
        db_table = 'permissions_field_permission'
        verbose_name = _('Field Permission')
        verbose_name_plural = _('Field Permissions')
        indexes = [
            models.Index(fields=['content_type', 'field_name']),
            models.Index(fields=['user', 'permission_type']),
            models.Index(fields=['priority']),
            models.Index(fields=['-created_at']),
        ]
        unique_together = [
            ['user', 'content_type', 'field_name'],
        ]
        ordering = ['-priority', 'created_at']

    def __str__(self):
        return f'{self.content_type.model}.{self.field_name} - {self.permission_type} ({self.user.username})'

    def apply_mask(self, value):
        """
        Apply masking rule to a value.

        Args:
            value: The value to mask

        Returns:
            Masked value
        """
        if value is None:
            return None

        if not self.permission_type == 'masked':
            return value

        value_str = str(value)

        if self.mask_rule == 'phone':
            # Keep first 3 and last 4 digits
            if len(value_str) >= 7:
                return f'{value_str[:3]}****{value_str[-4:]}'
            return '****'

        elif self.mask_rule == 'id_card':
            # Keep first 3 and last 4 digits
            if len(value_str) >= 7:
                return f'{value_str[:3]}***********{value_str[-4:]}'
            return '***********'

        elif self.mask_rule == 'bank_card':
            # Keep last 4 digits
            if len(value_str) >= 4:
                return f'{"*" * (len(value_str) - 4)}{value_str[-4:]}'
            return '****'

        elif self.mask_rule == 'name':
            # Keep last character only
            if len(value_str) > 1:
                return f'{"*" * (len(value_str) - 1)}{value_str[-1]}'
            return value_str

        elif self.mask_rule == 'email':
            # Mask local part before @
            if '@' in value_str:
                local, domain = value_str.split('@', 1)
                if len(local) > 2:
                    return f'{local[0]}***{local[-1] if len(local) > 3 else ""}@{domain}'
                return f'***@{domain}'
            return '***@***'

        elif self.mask_rule == 'amount':
            # Show range only
            try:
                amount = float(value_str)
                if amount < 1000:
                    return '< 1K'
                elif amount < 10000:
                    return '1K-10K'
                elif amount < 100000:
                    return '1W-10W'
                else:
                    return '> 10W'
            except (ValueError, TypeError):
                return '***'

        return '***'

    @classmethod
    def get_effective_permission(cls, user, content_type, field_name, action='view'):
        """
        Get the effective field permission for a user.

        Args:
            user: User instance
            content_type: ContentType instance
            field_name: Name of the field
            action: Action being performed ('view', 'edit')

        Returns:
            FieldPermission instance or None
        """
        from apps.accounts.models import User

        if not isinstance(user, User) or not user.is_authenticated:
            return None

        # Check user-specific permission
        try:
            user_perm = cls.objects.filter(
                user=user,
                content_type=content_type,
                field_name=field_name,
                is_deleted=False
            ).order_by('-priority').first()

            return user_perm
        except cls.DoesNotExist:
            pass

        return None
