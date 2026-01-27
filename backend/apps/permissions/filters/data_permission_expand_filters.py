"""
Filters for DataPermissionExpand model.
"""
import django_filters

from apps.common.filters.base import BaseModelFilter
from apps.permissions.models.data_permission_expand import DataPermissionExpand


class DataPermissionExpandFilter(BaseModelFilter):
    """
    Filter for DataPermissionExpand model.

    Extends BaseModelFilter with expansion-specific filters.
    """

    # Data permission filter
    data_permission = django_filters.UUIDFilter(field_name='data_permission_id')

    # Status filter
    is_active = django_filters.BooleanFilter()

    # Priority filters
    priority = django_filters.NumberFilter()
    priority_gte = django_filters.NumberFilter(
        field_name='priority',
        lookup_expr='gte'
    )
    priority_lte = django_filters.NumberFilter(
        field_name='priority',
        lookup_expr='lte'
    )

    # Description filter
    description = django_filters.CharFilter(lookup_expr='icontains')

    # Ordering
    order = django_filters.OrderingFilter(
        fields=(
            'priority', 'is_active', 'created_at', 'updated_at'
        )
    )

    class Meta:
        model = DataPermissionExpand
        fields = [
            'data_permission',
            'is_active',
            'priority',
            'description',
            'created_at_from',
            'created_at_to',
            'updated_at_from',
            'updated_at_to',
            'created_by',
            'is_deleted',
            'order'
        ]
