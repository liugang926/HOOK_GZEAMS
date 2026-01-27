"""
Filters for FieldPermission model.
"""
import django_filters
from django.contrib.contenttypes.models import ContentType

from apps.common.filters.base import BaseModelFilter
from apps.permissions.models.field_permission import FieldPermission


class FieldPermissionFilter(BaseModelFilter):
    """
    Filter for FieldPermission model.

    Extends BaseModelFilter with field permission-specific filters.
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

    # Field and permission type filters
    field_name = django_filters.CharFilter(lookup_expr='iexact')
    permission_type = django_filters.ChoiceFilter(
        choices=FieldPermission.PERMISSION_TYPE_CHOICES
    )
    mask_rule = django_filters.ChoiceFilter(
        choices=FieldPermission.MASK_RULE_CHOICES
    )

    # Priority filter
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
            'priority', 'field_name', 'permission_type',
            'created_at', 'updated_at'
        )
    )

    class Meta:
        model = FieldPermission
        fields = [
            'user',
            'user_username',
            'content_type',
            'content_type_app_label',
            'content_type_model',
            'field_name',
            'permission_type',
            'mask_rule',
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
