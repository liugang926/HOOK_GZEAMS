"""
Serializers for inventory reconciliation and report objects.
"""
from rest_framework import serializers

from apps.accounts.serializers import UserBasicSerializer
from apps.common.middleware import get_current_organization
from apps.common.serializers.base import BaseModelSerializer
from apps.inventory.models import (
    InventoryReconciliation,
    InventoryReport,
    InventoryTask,
)


def _build_task_queryset():
    """Build a task queryset from the current organization context."""
    queryset = InventoryTask.all_objects.filter(is_deleted=False)
    organization_id = get_current_organization()
    if organization_id:
        queryset = queryset.filter(organization_id=organization_id)
    return queryset


class InventoryTaskReferenceSerializer(serializers.ModelSerializer):
    """Lightweight task serializer for nested reconciliation/report payloads."""

    task_no = serializers.CharField(source='task_code', read_only=True)
    task_name = serializers.CharField(read_only=True)
    name = serializers.CharField(source='task_name', read_only=True)
    start_date = serializers.DateTimeField(source='started_at', read_only=True)
    end_date = serializers.DateTimeField(source='completed_at', read_only=True)

    class Meta:
        model = InventoryTask
        fields = ['id', 'task_no', 'task_name', 'name', 'start_date', 'end_date']


class InventoryReconciliationSerializer(BaseModelSerializer):
    """Detail serializer for inventory reconciliation records."""

    task = InventoryTaskReferenceSerializer(read_only=True)
    task_no = serializers.CharField(source='task.task_code', read_only=True)
    task_name = serializers.CharField(source='task.task_name', read_only=True)
    reconciled_by = UserBasicSerializer(read_only=True)
    reconciled_by_name = serializers.SerializerMethodField()
    current_approver = UserBasicSerializer(read_only=True)
    current_approver_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = InventoryReconciliation
        fields = BaseModelSerializer.Meta.fields + [
            'reconciliation_no',
            'task',
            'task_no',
            'task_name',
            'reconciled_at',
            'reconciled_by',
            'reconciled_by_name',
            'normal_count',
            'abnormal_count',
            'difference_count',
            'adjustment_count',
            'adjustments',
            'status',
            'status_display',
            'current_approver',
            'current_approver_name',
            'note',
            'submitted_at',
            'approved_at',
            'rejected_at',
        ]

    @staticmethod
    def get_reconciled_by_name(instance: InventoryReconciliation) -> str:
        return (
            instance.reconciled_by.get_full_name()
            if instance.reconciled_by and instance.reconciled_by.get_full_name()
            else getattr(instance.reconciled_by, 'username', '')
        )

    @staticmethod
    def get_current_approver_name(instance: InventoryReconciliation) -> str:
        return (
            instance.current_approver.get_full_name()
            if instance.current_approver and instance.current_approver.get_full_name()
            else getattr(instance.current_approver, 'username', '')
        )


class InventoryReconciliationListSerializer(BaseModelSerializer):
    """List serializer for inventory reconciliation records."""

    task = InventoryTaskReferenceSerializer(read_only=True)
    task_no = serializers.CharField(source='task.task_code', read_only=True)
    task_name = serializers.CharField(source='task.task_name', read_only=True)
    reconciled_by_name = serializers.SerializerMethodField()
    current_approver_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = InventoryReconciliation
        fields = [
            'id',
            'task',
            'task_no',
            'task_name',
            'reconciliation_no',
            'reconciled_at',
            'reconciled_by_name',
            'normal_count',
            'abnormal_count',
            'difference_count',
            'adjustment_count',
            'status',
            'status_display',
            'current_approver_name',
            'submitted_at',
            'approved_at',
            'rejected_at',
            'created_at',
        ]

    @staticmethod
    def get_reconciled_by_name(instance: InventoryReconciliation) -> str:
        if not instance.reconciled_by:
            return ''
        return instance.reconciled_by.get_full_name() or instance.reconciled_by.username

    @staticmethod
    def get_current_approver_name(instance: InventoryReconciliation) -> str:
        if not instance.current_approver:
            return ''
        return instance.current_approver.get_full_name() or instance.current_approver.username


class InventoryReconciliationCreateSerializer(serializers.Serializer):
    """Serializer for reconciliation creation requests."""

    task = serializers.PrimaryKeyRelatedField(queryset=InventoryTask.all_objects.none())
    note = serializers.CharField(required=False, allow_blank=True)

    def __init__(self, *args, **kwargs):
        """Bind the task queryset at request time to avoid stale tenant context."""
        super().__init__(*args, **kwargs)
        self.fields['task'].queryset = _build_task_queryset()

    class Meta:
        fields = ['task', 'note']


class InventoryReconciliationDecisionSerializer(serializers.Serializer):
    """Serializer for reconciliation approval decisions."""

    comment = serializers.CharField(required=False, allow_blank=True)
    reason = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        fields = ['comment', 'reason']


class InventoryReportSerializer(BaseModelSerializer):
    """Detail serializer for inventory reports."""

    task = InventoryTaskReferenceSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    generated_by = UserBasicSerializer(read_only=True)
    current_approver = UserBasicSerializer(read_only=True)
    current_approver_name = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = InventoryReport
        fields = BaseModelSerializer.Meta.fields + [
            'report_no',
            'task',
            'template_id',
            'status',
            'status_display',
            'summary',
            'report_data',
            'generated_by',
            'generated_at',
            'current_approver',
            'current_approver_name',
            'approvals',
            'submitted_at',
            'approved_at',
            'rejected_at',
        ]

    @staticmethod
    def get_current_approver_name(instance: InventoryReport) -> str:
        if not instance.current_approver:
            return ''
        return instance.current_approver.get_full_name() or instance.current_approver.username


class InventoryReportListSerializer(BaseModelSerializer):
    """List serializer for inventory reports."""

    task = InventoryTaskReferenceSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    generated_by = UserBasicSerializer(read_only=True)
    current_approver = UserBasicSerializer(read_only=True)
    current_approver_name = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = InventoryReport
        fields = [
            'id',
            'report_no',
            'task',
            'status',
            'status_display',
            'summary',
            'generated_by',
            'generated_at',
            'current_approver',
            'current_approver_name',
            'created_at',
        ]

    @staticmethod
    def get_current_approver_name(instance: InventoryReport) -> str:
        if not instance.current_approver:
            return ''
        return instance.current_approver.get_full_name() or instance.current_approver.username


class InventoryReportCreateSerializer(serializers.Serializer):
    """Serializer for report generation requests."""

    task = serializers.PrimaryKeyRelatedField(queryset=InventoryTask.all_objects.none())
    template_id = serializers.CharField(required=False, allow_blank=True)

    def __init__(self, *args, **kwargs):
        """Bind the task queryset at request time to avoid stale tenant context."""
        super().__init__(*args, **kwargs)
        self.fields['task'].queryset = _build_task_queryset()

    class Meta:
        fields = ['task', 'template_id']


class InventoryReportDecisionSerializer(serializers.Serializer):
    """Serializer for report approval transitions."""

    opinion = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        fields = ['opinion']
