"""
Filters for PermissionAuditLog model.
"""
import django_filters
from django.contrib.contenttypes.models import ContentType

from apps.common.filters.base import BaseModelFilter
from apps.permissions.models.permission_audit_log import PermissionAuditLog


class PermissionAuditLogFilter(BaseModelFilter):
    """
    Filter for PermissionAuditLog model.

    Extends BaseModelFilter with audit log-specific filters.
    """

    # Actor filter
    actor = django_filters.UUIDFilter(field_name='actor_id')
    actor_username = django_filters.CharFilter(
        field_name='actor__username',
        lookup_expr='icontains'
    )

    # Target filters
    target_user = django_filters.UUIDFilter(field_name='target_user_id')
    target_user_username = django_filters.CharFilter(
        field_name='target_user__username',
        lookup_expr='icontains'
    )

    # Operation type filter
    operation_type = django_filters.ChoiceFilter(
        choices=PermissionAuditLog.OPERATION_TYPE_CHOICES
    )

    # Target type filter
    target_type = django_filters.ChoiceFilter(
        choices=PermissionAuditLog.TARGET_TYPE_CHOICES
    )

    # Result filter
    result = django_filters.ChoiceFilter(
        choices=PermissionAuditLog.SUCCESS_CHOICES
    )

    # Content type filter
    content_type = django_filters.ModelChoiceFilter(
        queryset=ContentType.objects.all()
    )

    # Object ID filter
    object_id = django_filters.UUIDFilter()

    # IP address filter
    ip_address = django_filters.CharFilter(lookup_expr='iexact')

    # Description filter
    error_message = django_filters.CharFilter(lookup_expr='icontains')

    # Ordering
    order = django_filters.OrderingFilter(
        fields=(
            'created_at', 'operation_type', 'result'
        )
    )

    class Meta:
        model = PermissionAuditLog
        fields = [
            'actor',
            'actor_username',
            'target_user',
            'target_user_username',
            'operation_type',
            'target_type',
            'result',
            'content_type',
            'object_id',
            'ip_address',
            'error_message',
            'created_at_from',
            'created_at_to',
            'updated_at_from',
            'updated_at_to',
            'created_by',
            'is_deleted',
            'order'
        ]
