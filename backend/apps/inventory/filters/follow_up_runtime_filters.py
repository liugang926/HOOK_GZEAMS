"""Runtime filters for inventory manual follow-up tasks."""

import django_filters
from django.utils.translation import gettext_lazy as _

from apps.common.filters.base import BaseModelFilter
from apps.inventory.models import InventoryFollowUp


class InventoryFollowUpFilter(BaseModelFilter):
    """FilterSet for inventory follow-up queues."""

    task = django_filters.UUIDFilter(field_name='task_id', label=_('Task'))
    difference = django_filters.UUIDFilter(field_name='difference_id', label=_('Difference'))
    assignee = django_filters.UUIDFilter(field_name='assignee_id', label=_('Assignee'))
    linked_action_code = django_filters.CharFilter(
        field_name='linked_action_code',
        lookup_expr='iexact',
        label=_('Linked Action Code'),
    )
    closure_type = django_filters.CharFilter(
        field_name='closure_type',
        lookup_expr='iexact',
        label=_('Closure Type'),
    )
    open_only = django_filters.BooleanFilter(
        method='filter_open_only',
        label=_('Open Only'),
    )

    ordering = django_filters.OrderingFilter(
        fields={
            'created_at': 'created_at',
            'assigned_at': 'assigned_at',
            'completed_at': 'completed_at',
            'status': 'status',
            'follow_up_code': 'follow_up_code',
        }
    )

    class Meta(BaseModelFilter.Meta):
        model = InventoryFollowUp
        fields = BaseModelFilter.Meta.fields + [
            'task',
            'difference',
            'assignee',
            'status',
            'linked_action_code',
            'closure_type',
            'open_only',
        ]

    def filter_open_only(self, queryset, name, value):
        """Filter only open follow-up tasks."""
        if value is None or not value:
            return queryset
        return queryset.filter(status=InventoryFollowUp.STATUS_PENDING)
