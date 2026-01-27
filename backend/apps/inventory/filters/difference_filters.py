"""
Filters for Inventory Difference model.
"""
import django_filters
from django.utils.translation import gettext_lazy as _

from apps.common.filters.base import BaseModelFilter
from apps.inventory.models import InventoryDifference


class InventoryDifferenceFilter(BaseModelFilter):
    """Filter for inventory differences."""

    # Task filter
    task = django_filters.UUIDFilter(
        field_name='task',
        label=_('Task')
    )

    # Asset filter
    asset = django_filters.UUIDFilter(
        field_name='asset',
        label=_('Asset')
    )

    # Asset code search
    asset_code = django_filters.CharFilter(
        field_name='asset__asset_code',
        lookup_expr='icontains',
        label=_('Asset Code')
    )

    # Asset name search
    asset_name = django_filters.CharFilter(
        field_name='asset__asset_name',
        lookup_expr='icontains',
        label=_('Asset Name')
    )

    # Difference type filter
    difference_type = django_filters.ChoiceFilter(
        field_name='difference_type',
        choices=InventoryDifference.DIFFERENCE_TYPE_CHOICES,
        label=_('Difference Type')
    )

    # Status filter
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=InventoryDifference.RESOLUTION_STATUS_CHOICES,
        label=_('Status')
    )

    # Resolved by user filter
    resolved_by = django_filters.UUIDFilter(
        field_name='resolved_by',
        label=_('Resolved By')
    )

    # Resolved date range
    resolved_at_from = django_filters.DateFilter(
        field_name='resolved_at',
        lookup_expr='date__gte',
        label=_('Resolved Date From')
    )
    resolved_at_to = django_filters.DateFilter(
        field_name='resolved_at',
        lookup_expr='date__lte',
        label=_('Resolved Date To')
    )

    # Location filter
    expected_location = django_filters.CharFilter(
        field_name='expected_location',
        lookup_expr='icontains',
        label=_('Expected Location')
    )
    actual_location = django_filters.CharFilter(
        field_name='actual_location',
        lookup_expr='icontains',
        label=_('Actual Location')
    )

    # Custodian filter
    expected_custodian = django_filters.CharFilter(
        field_name='expected_custodian',
        lookup_expr='icontains',
        label=_('Expected Custodian')
    )
    actual_custodian = django_filters.CharFilter(
        field_name='actual_custodian',
        lookup_expr='icontains',
        label=_('Actual Custodian')
    )

    # Quantity difference range
    quantity_difference_min = django_filters.NumberFilter(
        field_name='quantity_difference',
        lookup_expr='lte',  # Negative values (missing)
        label=_('Max Negative Difference')
    )
    quantity_difference_max = django_filters.NumberFilter(
        field_name='quantity_difference',
        lookup_expr='gte',  # Positive values (surplus)
        label=_('Max Positive Difference')
    )

    # Description search
    description = django_filters.CharFilter(
        field_name='description',
        lookup_expr='icontains',
        label=_('Description')
    )

    # Resolution search
    resolution = django_filters.CharFilter(
        field_name='resolution',
        lookup_expr='icontains',
        label=_('Resolution')
    )

    # Pending differences only (quick filter)
    pending_only = django_filters.BooleanFilter(
        method='filter_pending_only',
        label=_('Pending Only')
    )

    # Unresolved differences (pending + no resolution)
    unresolved_only = django_filters.BooleanFilter(
        method='filter_unresolved_only',
        label=_('Unresolved Only')
    )

    # Ordering
    ordering = django_filters.OrderingFilter(
        fields={
            'created_at': 'created_at',
            'resolved_at': 'resolved_at',
            'difference_type': 'difference_type',
            'status': 'status',
            'asset_code': 'asset__asset_code',
            'task_code': 'task__task_code',
        },
        field_labels={
            'created_at': _('Created At'),
            'resolved_at': _('Resolved At'),
            'difference_type': _('Difference Type'),
            'status': _('Status'),
            'asset_code': _('Asset Code'),
            'task_code': _('Task Code'),
        }
    )

    class Meta:
        model = InventoryDifference
        fields = [
            'task',
            'asset',
            'difference_type',
            'status',
            'resolved_by',
            'resolved_at_from',
            'resolved_at_to',
            'pending_only',
            'unresolved_only',
        ]

    def filter_pending_only(self, queryset, name, value):
        """Filter only pending differences."""
        if value is None or not value:
            return queryset
        return queryset.filter(status=InventoryDifference.STATUS_PENDING)

    def filter_unresolved_only(self, queryset, name, value):
        """Filter only unresolved differences (pending or ignored without resolution)."""
        if value is None or not value:
            return queryset
        return queryset.filter(
            status__in=[InventoryDifference.STATUS_PENDING, InventoryDifference.STATUS_IGNORED]
        )
