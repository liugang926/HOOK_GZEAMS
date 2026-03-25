"""
Filters for DataPermission model.
"""
import django_filters
from django.contrib.contenttypes.models import ContentType

from apps.common.filters.base import BaseModelFilter
from apps.permissions.models.data_permission import DataPermission


class DataPermissionFilter(BaseModelFilter):
    """
    Filter for DataPermission model.

    Extends BaseModelFilter with data permission-specific filters.
    """

    # Target filters
    user = django_filters.UUIDFilter(field_name='user_id')
    user_username = django_filters.CharFilter(
        field_name='user__username',
        lookup_expr='icontains'
    )

    # Content type filters
    content_type = django_filters.ModelChoiceFilter(
        queryset=ContentType.objects.all()
    )
    content_type_app_label = django_filters.CharFilter(
        field_name='content_type__app_label',
        lookup_expr='iexact'
    )
    content_type_model = django_filters.CharFilter(
        field_name='content_type__model',
        lookup_expr='iexact'
    )

    # Scope type filter
    scope_type = django_filters.ChoiceFilter(
        choices=DataPermission.SCOPE_TYPE_CHOICES
    )

    # Field filters
    department_field = django_filters.CharFilter(lookup_expr='iexact')
    user_field = django_filters.CharFilter(lookup_expr='iexact')

    # Description filter
    description = django_filters.CharFilter(lookup_expr='icontains')

    # Ordering
    order = django_filters.OrderingFilter(
        fields=(
            'scope_type', 'created_at', 'updated_at'
        )
    )

    class Meta:
        model = DataPermission
        fields = [
            'user',
            'user_username',
            'content_type',
            'content_type_app_label',
            'content_type_model',
            'scope_type',
            'department_field',
            'user_field',
            'description',
            'created_at_from',
            'created_at_to',
            'updated_at_from',
            'updated_at_to',
            'created_by',
            'is_deleted',
            'order'
        ]
