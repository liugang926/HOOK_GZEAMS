"""
Filters for Inventory Scan model.
"""
import django_filters
from django.utils.translation import gettext_lazy as _

from apps.common.filters.base import BaseModelFilter
from apps.inventory.models import InventoryScan


class InventoryScanFilter(BaseModelFilter):
    """Filter for inventory scans."""

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

    # QR code search
    qr_code = django_filters.CharFilter(
        field_name='qr_code',
        lookup_expr='icontains',
        label=_('QR Code')
    )

    # Scan method filter
    scan_method = django_filters.ChoiceFilter(
        field_name='scan_method',
        choices=InventoryScan.SCAN_METHOD_CHOICES,
        label=_('Scan Method')
    )

    # Scan status filter
    scan_status = django_filters.ChoiceFilter(
        field_name='scan_status',
        choices=InventoryScan.SCAN_STATUS_CHOICES,
        label=_('Scan Status')
    )

    # Scanned by user filter
    scanned_by = django_filters.UUIDFilter(
        field_name='scanned_by',
        label=_('Scanned By')
    )

    # Scanned date range
    scanned_at_from = django_filters.DateFilter(
        field_name='scanned_at',
        lookup_expr='date__gte',
        label=_('Scanned Date From')
    )
    scanned_at_to = django_filters.DateFilter(
        field_name='scanned_at',
        lookup_expr='date__lte',
        label=_('Scanned Date To')
    )

    # Original location filter
    original_location_name = django_filters.CharFilter(
        field_name='original_location_name',
        lookup_expr='icontains',
        label=_('Original Location')
    )

    # Actual location filter
    actual_location_name = django_filters.CharFilter(
        field_name='actual_location_name',
        lookup_expr='icontains',
        label=_('Actual Location')
    )

    # Location changed filter (scans where location differs)
    location_changed = django_filters.BooleanFilter(
        method='filter_location_changed',
        label=_('Location Changed')
    )

    # Original custodian filter
    original_custodian_name = django_filters.CharFilter(
        field_name='original_custodian_name',
        lookup_expr='icontains',
        label=_('Original Custodian')
    )

    # Actual custodian filter
    actual_custodian_name = django_filters.CharFilter(
        field_name='actual_custodian_name',
        lookup_expr='icontains',
        label=_('Actual Custodian')
    )

    # Has photos filter
    has_photos = django_filters.BooleanFilter(
        method='filter_has_photos',
        label=_('Has Photos')
    )

    # Has remark filter
    has_remark = django_filters.BooleanFilter(
        method='filter_has_remark',
        label=_('Has Remark')
    )

    # Has GPS coordinates filter
    has_gps = django_filters.BooleanFilter(
        method='filter_has_gps',
        label=_('Has GPS Coordinates')
    )

    # Ordering
    ordering = django_filters.OrderingFilter(
        fields={
            'scanned_at': 'scanned_at',
            'created_at': 'created_at',
            'asset_code': 'asset__asset_code',
            'task_code': 'task__task_code',
        },
        field_labels={
            'scanned_at': _('Scanned At'),
            'created_at': _('Created At'),
            'asset_code': _('Asset Code'),
            'task_code': _('Task Code'),
        }
    )

    class Meta:
        model = InventoryScan
        fields = [
            'task',
            'asset',
            'qr_code',
            'scan_method',
            'scan_status',
            'scanned_by',
            'scanned_at_from',
            'scanned_at_to',
        ]

    def filter_location_changed(self, queryset, name, value):
        """Filter scans where location changed."""
        if value is None:
            return queryset
        if value:
            return queryset.filter(
                original_location_name__isnull=False,
                actual_location_name__isnull=False
            ).exclude(
                original_location_name=models.F('actual_location_name')
            )
        return queryset.filter(
            models.Q(original_location_name__isnull=True) |
            models.Q(actual_location_name__isnull=True) |
            models.Q(original_location_name=models.F('actual_location_name'))
        )

    def filter_has_photos(self, queryset, name, value):
        """Filter scans with/without photos."""
        if value is None:
            return queryset
        if value:
            return queryset.filter(photos__len__gt=0)
        return queryset.filter(photos__len=0)

    def filter_has_remark(self, queryset, name, value):
        """Filter scans with/without remarks."""
        if value is None:
            return queryset
        if value:
            return queryset.exclude(remark='')
        return queryset.filter(remark='')

    def filter_has_gps(self, queryset, name, value):
        """Filter scans with/without GPS coordinates."""
        if value is None:
            return queryset
        if value:
            return queryset.filter(
                latitude__isnull=False,
                longitude__isnull=False
            )
        return queryset.exclude(
            latitude__isnull=False,
            longitude__isnull=False
        )
