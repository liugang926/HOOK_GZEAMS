"""
Filters for Inventory Task model.
"""
import django_filters
from django.utils.translation import gettext_lazy as _

from apps.common.filters.base import BaseModelFilter
from apps.inventory.models import InventoryTask


class InventoryTaskFilter(BaseModelFilter):
    """Filter for inventory tasks."""

    # Task code search (partial match)
    task_code = django_filters.CharFilter(
        field_name='task_code',
        lookup_expr='icontains',
        label=_('Task Code')
    )

    # Task name search (partial match)
    task_name = django_filters.CharFilter(
        field_name='task_name',
        lookup_expr='icontains',
        label=_('Task Name')
    )

    # Inventory type exact match
    inventory_type = django_filters.ChoiceFilter(
        field_name='inventory_type',
        choices=InventoryTask.INVENTORY_TYPE_CHOICES,
        label=_('Inventory Type')
    )

    # Status exact match
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=InventoryTask.STATUS_CHOICES,
        label=_('Status')
    )

    # Department filter
    department = django_filters.UUIDFilter(
        field_name='department',
        label=_('Department')
    )

    # Category filter
    category = django_filters.UUIDFilter(
        field_name='category',
        label=_('Category')
    )

    # Planned date range
    planned_date_from = django_filters.DateFilter(
        field_name='planned_date',
        lookup_expr='gte',
        label=_('Planned Date From')
    )
    planned_date_to = django_filters.DateFilter(
        field_name='planned_date',
        lookup_expr='lte',
        label=_('Planned Date To')
    )

    # Started date range
    started_at_from = django_filters.DateFilter(
        field_name='started_at',
        lookup_expr='gte',
        label=_('Started Date From')
    )
    started_at_to = django_filters.DateFilter(
        field_name='started_at',
        lookup_expr='lte',
        label=_('Started Date To')
    )

    # Completed date range
    completed_at_from = django_filters.DateFilter(
        field_name='completed_at',
        lookup_expr='gte',
        label=_('Completed Date From')
    )
    completed_at_to = django_filters.DateFilter(
        field_name='completed_at',
        lookup_expr='lte',
        label=_('Completed Date To')
    )

    # Executor filter (user who is assigned as executor)
    executor = django_filters.UUIDFilter(
        field_name='executors_relation__executor',
        label=_('Executor')
    )

    # Progress range filters
    progress_min = django_filters.NumberFilter(
        method='filter_progress_min',
        label=_('Minimum Progress %')
    )
    progress_max = django_filters.NumberFilter(
        method='filter_progress_max',
        label=_('Maximum Progress %')
    )

    # Ordering
    ordering = django_filters.OrderingFilter(
        fields={
            'task_code': 'task_code',
            'task_name': 'task_name',
            'created_at': 'created_at',
            'planned_date': 'planned_date',
            'started_at': 'started_at',
            'completed_at': 'completed_at',
            'total_count': 'total_count',
            'scanned_count': 'scanned_count',
        },
        field_labels={
            'task_code': _('Task Code'),
            'task_name': _('Task Name'),
            'created_at': _('Created At'),
            'planned_date': _('Planned Date'),
            'started_at': _('Started At'),
            'completed_at': _('Completed At'),
            'total_count': _('Total Count'),
            'scanned_count': _('Scanned Count'),
        }
    )

    class Meta:
        model = InventoryTask
        fields = [
            'task_code',
            'task_name',
            'inventory_type',
            'status',
            'department',
            'category',
            'planned_date_from',
            'planned_date_to',
            'started_at_from',
            'started_at_to',
            'completed_at_from',
            'completed_at_to',
            'executor',
        ]

    def filter_progress_min(self, queryset, name, value):
        """Filter by minimum progress percentage."""
        if value is None:
            return queryset
        # Annotate with progress percentage and filter
        return queryset.filter(
            scanned_count__gte=value
        )

    def filter_progress_max(self, queryset, name, value):
        """Filter by maximum progress percentage."""
        if value is None:
            return queryset
        return queryset.filter(
            scanned_count__lte=value
        )
