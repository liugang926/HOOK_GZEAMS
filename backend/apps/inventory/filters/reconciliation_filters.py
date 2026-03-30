"""
Filters for inventory reconciliation and report objects.
"""
import django_filters
from django.utils.translation import gettext_lazy as _

from apps.common.filters.base import BaseModelFilter
from apps.inventory.models import InventoryReconciliation, InventoryReport


class InventoryReconciliationFilter(BaseModelFilter):
    """FilterSet for inventory reconciliation records."""

    reconciliation_no = django_filters.CharFilter(
        field_name='reconciliation_no',
        lookup_expr='icontains',
        label=_('Reconciliation No'),
    )
    task = django_filters.UUIDFilter(field_name='task_id', label=_('Task'))
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=InventoryReconciliation.STATUS_CHOICES,
        label=_('Status'),
    )
    reconciled_at_from = django_filters.DateFilter(
        field_name='reconciled_at',
        lookup_expr='gte',
        label=_('Reconciled From'),
    )
    reconciled_at_to = django_filters.DateFilter(
        field_name='reconciled_at',
        lookup_expr='lte',
        label=_('Reconciled To'),
    )
    ordering = django_filters.OrderingFilter(
        fields={
            'created_at': 'created_at',
            'reconciled_at': 'reconciled_at',
            'submitted_at': 'submitted_at',
            'approved_at': 'approved_at',
            'difference_count': 'difference_count',
            'adjustment_count': 'adjustment_count',
        }
    )

    class Meta(BaseModelFilter.Meta):
        model = InventoryReconciliation
        fields = BaseModelFilter.Meta.fields + [
            'reconciliation_no',
            'task',
            'status',
            'reconciled_at_from',
            'reconciled_at_to',
        ]


class InventoryReportFilter(BaseModelFilter):
    """FilterSet for generated inventory reports."""

    report_no = django_filters.CharFilter(
        field_name='report_no',
        lookup_expr='icontains',
        label=_('Report No'),
    )
    task = django_filters.UUIDFilter(field_name='task_id', label=_('Task'))
    status = django_filters.ChoiceFilter(
        field_name='status',
        choices=InventoryReport.STATUS_CHOICES,
        label=_('Status'),
    )
    generated_at_from = django_filters.DateFilter(
        field_name='generated_at',
        lookup_expr='gte',
        label=_('Generated From'),
    )
    generated_at_to = django_filters.DateFilter(
        field_name='generated_at',
        lookup_expr='lte',
        label=_('Generated To'),
    )
    ordering = django_filters.OrderingFilter(
        fields={
            'created_at': 'created_at',
            'generated_at': 'generated_at',
            'submitted_at': 'submitted_at',
            'approved_at': 'approved_at',
            'report_no': 'report_no',
        }
    )

    class Meta(BaseModelFilter.Meta):
        model = InventoryReport
        fields = BaseModelFilter.Meta.fields + [
            'report_no',
            'task',
            'status',
            'generated_at_from',
            'generated_at_to',
        ]
