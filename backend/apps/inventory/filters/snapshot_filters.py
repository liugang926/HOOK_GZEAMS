"""
Filters for Inventory Snapshot model.
"""
import django_filters
from django.utils.translation import gettext_lazy as _

from apps.common.filters.base import BaseModelFilter
from apps.inventory.models import InventorySnapshot


class InventorySnapshotFilter(BaseModelFilter):
    """Filter for inventory snapshots."""

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
        field_name='asset_code',
        lookup_expr='icontains',
        label=_('Asset Code')
    )

    # Asset name search
    asset_name = django_filters.CharFilter(
        field_name='asset_name',
        lookup_expr='icontains',
        label=_('Asset Name')
    )

    # Category filter
    asset_category_id = django_filters.UUIDFilter(
        field_name='asset_category_id',
        label=_('Category')
    )

    # Location filter
    location_id = django_filters.UUIDFilter(
        field_name='location_id',
        label=_('Location')
    )

    # Location name search
    location_name = django_filters.CharFilter(
        field_name='location_name',
        lookup_expr='icontains',
        label=_('Location Name')
    )

    # Custodian filter
    custodian_id = django_filters.UUIDFilter(
        field_name='custodian_id',
        label=_('Custodian')
    )

    # Custodian name search
    custodian_name = django_filters.CharFilter(
        field_name='custodian_name',
        lookup_expr='icontains',
        label=_('Custodian Name')
    )

    # Department filter
    department_id = django_filters.UUIDFilter(
        field_name='department_id',
        label=_('Department')
    )

    # Department name search
    department_name = django_filters.CharFilter(
        field_name='department_name',
        lookup_expr='icontains',
        label=_('Department Name')
    )

    # Asset status filter
    asset_status = django_filters.ChoiceFilter(
        field_name='asset_status',
        choices=[('in_use', _('In Use')), ('idle', _('Idle')), ('damaged', _('Damaged'))],
        label=_('Asset Status')
    )

    # Scanned status filter
    scanned = django_filters.BooleanFilter(
        field_name='scanned',
        label=_('Scanned')
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

    # Scan count range
    scan_count_min = django_filters.NumberFilter(
        field_name='scan_count',
        lookup_expr='gte',
        label=_('Minimum Scan Count')
    )
    scan_count_max = django_filters.NumberFilter(
        field_name='scan_count',
        lookup_expr='lte',
        label=_('Maximum Scan Count')
    )

    # Ordering
    ordering = django_filters.OrderingFilter(
        fields={
            'asset_code': 'asset_code',
            'asset_name': 'asset_name',
            'location_name': 'location_name',
            'custodian_name': 'custodian_name',
            'scanned_at': 'scanned_at',
            'scan_count': 'scan_count',
        },
        field_labels={
            'asset_code': _('Asset Code'),
            'asset_name': _('Asset Name'),
            'location_name': _('Location Name'),
            'custodian_name': _('Custodian Name'),
            'scanned_at': _('Scanned At'),
            'scan_count': _('Scan Count'),
        }
    )

    class Meta:
        model = InventorySnapshot
        fields = [
            'task',
            'asset',
            'asset_code',
            'asset_name',
            'asset_category_id',
            'location_id',
            'location_name',
            'custodian_id',
            'custodian_name',
            'department_id',
            'department_name',
            'asset_status',
            'scanned',
            'scanned_at_from',
            'scanned_at_to',
            'scan_count_min',
            'scan_count_max',
        ]
