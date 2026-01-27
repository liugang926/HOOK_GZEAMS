"""
Filter Classes for Lifecycle Management.

All filters inherit from BaseModelFilter for common filtering capabilities.
"""
import django_filters
from django_filters import rest_framework as filters
from django.db.models import F
from apps.common.filters.base import BaseModelFilter
from apps.lifecycle.models import (
    PurchaseRequest,
    PurchaseRequestItem,
    PurchaseRequestStatus,
    AssetReceipt,
    AssetReceiptItem,
    AssetReceiptStatus,
    Maintenance,
    MaintenanceStatus,
    MaintenancePriority,
    MaintenancePlan,
    MaintenancePlanStatus,
    MaintenanceTask,
    MaintenanceTaskStatus,
    DisposalRequest,
    DisposalItem,
    DisposalRequestStatus,
    DisposalType,
)


# ========== Purchase Request Filter ==========

class PurchaseRequestFilter(BaseModelFilter):
    """Filter for PurchaseRequest queries"""

    request_no = filters.CharFilter(field_name='request_no', lookup_expr='icontains')
    status = filters.ChoiceFilter(field_name='status', choices=PurchaseRequestStatus.choices)
    applicant_id = filters.UUIDFilter(field_name='applicant__id')
    applicant_name = filters.CharFilter(field_name='applicant__username', lookup_expr='icontains')
    department_id = filters.UUIDFilter(field_name='department__id')
    department_name = filters.CharFilter(field_name='department__name', lookup_expr='icontains')
    current_approver_id = filters.UUIDFilter(field_name='current_approver__id')
    approved_by_id = filters.UUIDFilter(field_name='approved_by__id')

    # Date range filters
    request_date_from = filters.DateFilter(field_name='request_date', lookup_expr='gte')
    request_date_to = filters.DateFilter(field_name='request_date', lookup_expr='lte')
    expected_date_from = filters.DateFilter(field_name='expected_date', lookup_expr='gte')
    expected_date_to = filters.DateFilter(field_name='expected_date', lookup_expr='lte')
    approved_at_from = filters.DateTimeFilter(field_name='approved_at', lookup_expr='gte')
    approved_at_to = filters.DateTimeFilter(field_name='approved_at', lookup_expr='lte')

    # M18 sync filter
    m18_synced = filters.BooleanFilter(method='filter_m18_synced')

    # Amount range filters
    budget_amount_min = filters.NumberFilter(field_name='budget_amount', lookup_expr='gte')
    budget_amount_max = filters.NumberFilter(field_name='budget_amount', lookup_expr='lte')

    class Meta:
        model = PurchaseRequest
        fields = [
            'request_no', 'status', 'applicant_id', 'applicant_name',
            'department_id', 'department_name', 'current_approver_id',
            'approved_by_id',
        ]

    def filter_m18_synced(self, queryset, name, value):
        """Filter by M18 sync status"""
        if value is True:
            return queryset.filter(m18_purchase_order_no__isnull=False)
        elif value is False:
            return queryset.filter(m18_purchase_order_no__isnull=True)
        return queryset


class PurchaseRequestItemFilter(BaseModelFilter):
    """Filter for PurchaseRequestItem queries"""

    purchase_request_id = filters.UUIDFilter(field_name='purchase_request__id')
    asset_category_id = filters.UUIDFilter(field_name='asset_category__id')
    asset_category_code = filters.CharFilter(field_name='asset_category__code', lookup_expr='icontains')
    item_name = filters.CharFilter(field_name='item_name', lookup_expr='icontains')
    brand = filters.CharFilter(field_name='brand', lookup_expr='icontains')
    suggested_supplier = filters.CharFilter(field_name='suggested_supplier', lookup_expr='icontains')

    # Quantity range filters
    quantity_min = filters.NumberFilter(field_name='quantity', lookup_expr='gte')
    quantity_max = filters.NumberFilter(field_name='quantity', lookup_expr='lte')

    # Amount range filters
    unit_price_min = filters.NumberFilter(field_name='unit_price', lookup_expr='gte')
    unit_price_max = filters.NumberFilter(field_name='unit_price', lookup_expr='lte')
    total_amount_min = filters.NumberFilter(field_name='total_amount', lookup_expr='gte')
    total_amount_max = filters.NumberFilter(field_name='total_amount', lookup_expr='lte')

    class Meta:
        model = PurchaseRequestItem
        fields = [
            'purchase_request_id', 'asset_category_id', 'asset_category_code',
            'item_name', 'brand', 'suggested_supplier',
        ]


# ========== Asset Receipt Filter ==========

class AssetReceiptFilter(BaseModelFilter):
    """Filter for AssetReceipt queries"""

    receipt_no = filters.CharFilter(field_name='receipt_no', lookup_expr='icontains')
    status = filters.ChoiceFilter(field_name='status', choices=AssetReceiptStatus.choices)
    receipt_type = filters.ChoiceFilter(field_name='receipt_type')
    purchase_request_id = filters.UUIDFilter(field_name='purchase_request__id')
    supplier = filters.CharFilter(field_name='supplier', lookup_expr='icontains')
    delivery_no = filters.CharFilter(field_name='delivery_no', lookup_expr='icontains')
    receiver_id = filters.UUIDFilter(field_name='receiver__id')
    inspector_id = filters.UUIDFilter(field_name='inspector__id')

    # Date range filters
    receipt_date_from = filters.DateFilter(field_name='receipt_date', lookup_expr='gte')
    receipt_date_to = filters.DateFilter(field_name='receipt_date', lookup_expr='lte')
    passed_at_from = filters.DateTimeFilter(field_name='passed_at', lookup_expr='gte')
    passed_at_to = filters.DateTimeFilter(field_name='passed_at', lookup_expr='lte')

    # M18 filter
    has_m18_order = filters.BooleanFilter(field_name='m18_purchase_order_no__isnull')

    class Meta:
        model = AssetReceipt
        fields = [
            'receipt_no', 'status', 'receipt_type', 'purchase_request_id',
            'supplier', 'delivery_no', 'receiver_id', 'inspector_id',
        ]


class AssetReceiptItemFilter(BaseModelFilter):
    """Filter for AssetReceiptItem queries"""

    asset_receipt_id = filters.UUIDFilter(field_name='asset_receipt__id')
    asset_category_id = filters.UUIDFilter(field_name='asset_category__id')
    asset_category_code = filters.CharFilter(field_name='asset_category__code', lookup_expr='icontains')
    item_name = filters.CharFilter(field_name='item_name', lookup_expr='icontains')
    brand = filters.CharFilter(field_name='brand', lookup_expr='icontains')

    # Quantity filters
    received_quantity_min = filters.NumberFilter(field_name='received_quantity', lookup_expr='gte')
    received_quantity_max = filters.NumberFilter(field_name='received_quantity', lookup_expr='lte')
    qualified_quantity_min = filters.NumberFilter(field_name='qualified_quantity', lookup_expr='gte')
    qualified_quantity_max = filters.NumberFilter(field_name='qualified_quantity', lookup_expr='lte')

    # Amount range filters
    unit_price_min = filters.NumberFilter(field_name='unit_price', lookup_expr='gte')
    unit_price_max = filters.NumberFilter(field_name='unit_price', lookup_expr='lte')

    # Asset generation filter
    asset_generated = filters.BooleanFilter(field_name='asset_generated')

    class Meta:
        model = AssetReceiptItem
        fields = [
            'asset_receipt_id', 'asset_category_id', 'asset_category_code',
            'item_name', 'brand', 'asset_generated',
        ]


# ========== Maintenance Filter ==========

class MaintenanceFilter(BaseModelFilter):
    """Filter for Maintenance queries"""

    maintenance_no = filters.CharFilter(field_name='maintenance_no', lookup_expr='icontains')
    status = filters.ChoiceFilter(field_name='status', choices=MaintenanceStatus.choices)
    priority = filters.ChoiceFilter(field_name='priority', choices=MaintenancePriority.choices)
    asset_id = filters.UUIDFilter(field_name='asset__id')
    asset_code = filters.CharFilter(field_name='asset__asset_code', lookup_expr='icontains')
    asset_name = filters.CharFilter(field_name='asset__asset_name', lookup_expr='icontains')
    reporter_id = filters.UUIDFilter(field_name='reporter__id')
    technician_id = filters.UUIDFilter(field_name='technician__id')
    verified_by_id = filters.UUIDFilter(field_name='verified_by__id')

    # Date range filters
    report_time_from = filters.DateTimeFilter(field_name='report_time', lookup_expr='gte')
    report_time_to = filters.DateTimeFilter(field_name='report_time', lookup_expr='lte')
    assigned_at_from = filters.DateTimeFilter(field_name='assigned_at', lookup_expr='gte')
    assigned_at_to = filters.DateTimeFilter(field_name='assigned_at', lookup_expr='lte')
    start_time_from = filters.DateTimeFilter(field_name='start_time', lookup_expr='gte')
    start_time_to = filters.DateTimeFilter(field_name='start_time', lookup_expr='lte')
    end_time_from = filters.DateTimeFilter(field_name='end_time', lookup_expr='gte')
    end_time_to = filters.DateTimeFilter(field_name='end_time', lookup_expr='lte')

    # Cost range filters
    total_cost_min = filters.NumberFilter(field_name='total_cost', lookup_expr='gte')
    total_cost_max = filters.NumberFilter(field_name='total_cost', lookup_expr='lte')

    # Assigned filter
    is_assigned = filters.BooleanFilter(method='filter_is_assigned')

    # Verified filter
    is_verified = filters.BooleanFilter(field_name='verified_by__isnull')

    class Meta:
        model = Maintenance
        fields = [
            'maintenance_no', 'status', 'priority', 'asset_id', 'asset_code',
            'asset_name', 'reporter_id', 'technician_id', 'verified_by_id',
        ]

    def filter_is_assigned(self, queryset, name, value):
        """Filter by technician assignment"""
        if value is True:
            return queryset.filter(technician__isnull=False)
        elif value is False:
            return queryset.filter(technician__isnull=True)
        return queryset


# ========== Maintenance Plan Filter ==========

class MaintenancePlanFilter(BaseModelFilter):
    """Filter for MaintenancePlan queries"""

    plan_code = filters.CharFilter(field_name='plan_code', lookup_expr='icontains')
    plan_name = filters.CharFilter(field_name='plan_name', lookup_expr='icontains')
    status = filters.ChoiceFilter(field_name='status', choices=MaintenancePlanStatus.choices)
    target_type = filters.ChoiceFilter(field_name='target_type')
    cycle_type = filters.ChoiceFilter(field_name='cycle_type')

    # Date range filters
    start_date_from = filters.DateFilter(field_name='start_date', lookup_expr='gte')
    start_date_to = filters.DateFilter(field_name='start_date', lookup_expr='lte')
    end_date_from = filters.DateFilter(field_name='end_date', lookup_expr='gte')
    end_date_to = filters.DateFilter(field_name='end_date', lookup_expr='lte')

    # Category/asset filters
    asset_category_id = filters.UUIDFilter(field_name='asset_categories__id')
    asset_id = filters.UUIDFilter(field_name='assets__id')

    class Meta:
        model = MaintenancePlan
        fields = [
            'plan_code', 'plan_name', 'status', 'target_type', 'cycle_type',
            'asset_category_id', 'asset_id',
        ]


# ========== Maintenance Task Filter ==========

class MaintenanceTaskFilter(BaseModelFilter):
    """Filter for MaintenanceTask queries"""

    task_no = filters.CharFilter(field_name='task_no', lookup_expr='icontains')
    status = filters.ChoiceFilter(field_name='status', choices=MaintenanceTaskStatus.choices)
    plan_id = filters.UUIDFilter(field_name='plan__id')
    asset_id = filters.UUIDFilter(field_name='asset__id')
    asset_code = filters.CharFilter(field_name='asset__asset_code', lookup_expr='icontains')
    asset_name = filters.CharFilter(field_name='asset__asset_name', lookup_expr='icontains')
    executor_id = filters.UUIDFilter(field_name='executor__id')
    verified_by_id = filters.UUIDFilter(field_name='verified_by__id')

    # Date range filters
    scheduled_date_from = filters.DateFilter(field_name='scheduled_date', lookup_expr='gte')
    scheduled_date_to = filters.DateFilter(field_name='scheduled_date', lookup_expr='lte')
    deadline_date_from = filters.DateFilter(field_name='deadline_date', lookup_expr='gte')
    deadline_date_to = filters.DateFilter(field_name='deadline_date', lookup_expr='lte')
    start_time_from = filters.DateTimeFilter(field_name='start_time', lookup_expr='gte')
    start_time_to = filters.DateTimeFilter(field_name='start_time', lookup_expr='lte')
    end_time_from = filters.DateTimeFilter(field_name='end_time', lookup_expr='gte')
    end_time_to = filters.DateTimeFilter(field_name='end_time', lookup_expr='lte')

    # Overdue filter
    is_overdue = filters.BooleanFilter(method='filter_is_overdue')

    # Assigned filter
    is_assigned = filters.BooleanFilter(method='filter_is_assigned')

    class Meta:
        model = MaintenanceTask
        fields = [
            'task_no', 'status', 'plan_id', 'asset_id', 'asset_code',
            'asset_name', 'executor_id', 'verified_by_id',
        ]

    def filter_is_overdue(self, queryset, name, value):
        """Filter overdue tasks"""
        from django.utils import timezone
        today = timezone.now().date()

        if value is True:
            return queryset.filter(
                status__in=[MaintenanceTaskStatus.PENDING, MaintenanceTaskStatus.OVERDUE],
                deadline_date__lt=today
            )
        return queryset

    def filter_is_assigned(self, queryset, name, value):
        """Filter by executor assignment"""
        if value is True:
            return queryset.filter(executor__isnull=False)
        elif value is False:
            return queryset.filter(executor__isnull=True)
        return queryset


# ========== Disposal Request Filter ==========

class DisposalRequestFilter(BaseModelFilter):
    """Filter for DisposalRequest queries"""

    request_no = filters.CharFilter(field_name='request_no', lookup_expr='icontains')
    status = filters.ChoiceFilter(field_name='status', choices=DisposalRequestStatus.choices)
    disposal_type = filters.ChoiceFilter(field_name='disposal_type', choices=DisposalType.choices)
    reason_type = filters.ChoiceFilter(field_name='reason_type')
    applicant_id = filters.UUIDFilter(field_name='applicant__id')
    applicant_name = filters.CharFilter(field_name='applicant__username', lookup_expr='icontains')
    department_id = filters.UUIDFilter(field_name='department__id')
    department_name = filters.CharFilter(field_name='department__name', lookup_expr='icontains')
    current_approver_id = filters.UUIDFilter(field_name='current_approver__id')

    # Date range filters
    request_date_from = filters.DateFilter(field_name='request_date', lookup_expr='gte')
    request_date_to = filters.DateFilter(field_name='request_date', lookup_expr='lte')

    class Meta:
        model = DisposalRequest
        fields = [
            'request_no', 'status', 'disposal_type', 'reason_type',
            'applicant_id', 'applicant_name', 'department_id',
            'department_name', 'current_approver_id',
        ]


class DisposalItemFilter(BaseModelFilter):
    """Filter for DisposalItem queries"""

    disposal_request_id = filters.UUIDFilter(field_name='disposal_request__id')
    asset_id = filters.UUIDFilter(field_name='asset__id')
    asset_code = filters.CharFilter(field_name='asset__asset_code', lookup_expr='icontains')
    asset_name = filters.CharFilter(field_name='asset__asset_name', lookup_expr='icontains')
    appraised_by_id = filters.UUIDFilter(field_name='appraised_by__id')

    # Value range filters
    original_value_min = filters.NumberFilter(field_name='original_value', lookup_expr='gte')
    original_value_max = filters.NumberFilter(field_name='original_value', lookup_expr='lte')
    net_value_min = filters.NumberFilter(field_name='net_value', lookup_expr='gte')
    net_value_max = filters.NumberFilter(field_name='net_value', lookup_expr='lte')
    residual_value_min = filters.NumberFilter(field_name='residual_value', lookup_expr='gte')
    residual_value_max = filters.NumberFilter(field_name='residual_value', lookup_expr='lte')

    # Appraisal status filter
    is_appraised = filters.BooleanFilter(field_name='appraised_by__isnull')

    # Execution status filter
    is_executed = filters.BooleanFilter(field_name='disposal_executed')

    class Meta:
        model = DisposalItem
        fields = [
            'disposal_request_id', 'asset_id', 'asset_code', 'asset_name',
            'appraised_by_id',
        ]
