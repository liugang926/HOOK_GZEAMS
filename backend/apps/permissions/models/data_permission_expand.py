"""
DataPermissionExpand Model - Extended data permission configuration.

Allows for additional permission rules and conditions beyond basic scope.
"""
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from apps.common.models import BaseModel


class DataPermissionExpand(BaseModel):
    """
    Extended data permission configuration for complex scenarios.

    Allows defining additional filter conditions, field-based restrictions,
    and special access rules.
    """

    # Link to base data permission
    data_permission = models.ForeignKey(
        'DataPermission',
        on_delete=models.CASCADE,
        related_name='expansions',
        verbose_name=_('Data Permission'),
        db_comment='Base data permission this expands upon'
    )

    # Filter conditions (JSON format for flexible expression)
    filter_conditions = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_('Filter Conditions'),
        db_comment='Additional filter conditions in JSON format'
    )

    # Field restrictions (which fields are visible/editable)
    allowed_fields = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Allowed Fields'),
        db_comment='List of field names that are accessible'
    )

    # Denied fields (explicitly denied access)
    denied_fields = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Denied Fields'),
        db_comment='List of field names that are explicitly denied'
    )

    # Action-specific permissions
    actions = models.JSONField(
        default=list,
        blank=True,
        verbose_name=_('Allowed Actions'),
        db_comment='List of allowed actions (view, create, update, delete, export)'
    )

    # Priority (higher = evaluated first)
    priority = models.IntegerField(
        default=0,
        verbose_name=_('Priority'),
        db_comment='Higher priority rules are evaluated first'
    )

    # Is this expansion active
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Is Active'),
        db_comment='Whether this expansion is currently active'
    )

    # Metadata
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        db_comment='Description of what this expansion controls'
    )

    class Meta:
        db_table = 'permissions_data_permission_expand'
        verbose_name = _('Data Permission Expansion')
        verbose_name_plural = _('Data Permission Expansions')
        indexes = [
            models.Index(fields=['data_permission', 'priority']),
            models.Index(fields=['is_active']),
            models.Index(fields=['-created_at']),
        ]
        ordering = ['-priority', 'created_at']

    def __str__(self):
        return f'Expansion for {self.data_permission} (Priority: {self.priority})'

    def check_action_allowed(self, action):
        """
        Check if a specific action is allowed.

        Args:
            action: Action name to check

        Returns:
            True if action is allowed
        """
        if not self.is_active:
            return True  # Don't restrict if expansion is inactive

        if not self.actions:
            return True  # No action restrictions

        return action in self.actions

    def check_field_allowed(self, field_name):
        """
        Check if a field is accessible.

        Args:
            field_name: Field name to check

        Returns:
            True if field is allowed
        """
        if not self.is_active:
            return True

        # Check denied fields first
        if field_name in self.denied_fields:
            return False

        # If allowed_fields is specified and not empty, check it
        if self.allowed_fields and field_name not in self.allowed_fields:
            return False

        return True

    def get_filter_kwargs(self):
        """
        Get filter conditions as kwargs for queryset filtering.

        Returns:
            Dict of filter conditions
        """
        return self.filter_conditions if self.is_active else {}
