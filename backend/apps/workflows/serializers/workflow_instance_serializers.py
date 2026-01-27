"""
Serializers for workflow instance execution.

Provides serializers for WorkflowInstance, WorkflowTask, and WorkflowApproval models.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.common.serializers.base import BaseModelSerializer
from apps.workflows.models import (
    WorkflowInstance, WorkflowTask, WorkflowApproval, WorkflowDefinition
)
from apps.accounts.serializers import UserSerializer


# === WorkflowInstance Serializers ===

class WorkflowInstanceListSerializer(BaseModelSerializer):
    """Lightweight serializer for list views."""

    definition_name = serializers.CharField(source='definition.name', read_only=True)
    definition_code = serializers.CharField(source='definition.code', read_only=True)
    initiator_name = serializers.CharField(source='initiator.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    progress_percentage = serializers.IntegerField(read_only=True)
    is_overdue = serializers.SerializerMethodField()
    pending_tasks_count = serializers.IntegerField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = WorkflowInstance
        fields = BaseModelSerializer.Meta.fields + [
            'instance_no',
            'definition_name',
            'definition_code',
            'business_object_code',
            'business_id',
            'business_no',
            'status',
            'status_display',
            'current_node_id',
            'current_node_name',
            'initiator',
            'initiator_name',
            'title',
            'description',
            'priority',
            'priority_display',
            'progress_percentage',
            'total_tasks',
            'completed_tasks',
            'pending_tasks_count',
            'started_at',
            'completed_at',
            'is_overdue',
        ]

    def get_is_overdue(self, obj):
        """Check if instance has overdue tasks."""
        return obj.tasks.filter(
            status='pending',
            due_date__lt=timezone.now()
        ).exists()


class WorkflowInstanceDetailSerializer(BaseModelSerializer):
    """Detailed serializer for single instance view."""

    definition = serializers.SerializerMethodField()
    definition_code = serializers.CharField(source='definition.code', read_only=True)
    initiator = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    progress_percentage = serializers.IntegerField(read_only=True)
    duration_hours = serializers.FloatField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_terminal = serializers.BooleanField(read_only=True)
    pending_tasks_count = serializers.IntegerField(read_only=True)
    approval_chain = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = WorkflowInstance
        fields = BaseModelSerializer.Meta.fields + [
            'instance_no',
            'definition',
            'definition_code',
            'business_object_code',
            'business_id',
            'business_no',
            'status',
            'status_display',
            'current_node_id',
            'current_node_name',
            'initiator',
            'title',
            'description',
            'priority',
            'priority_display',
            'variables',
            'total_tasks',
            'completed_tasks',
            'progress_percentage',
            'pending_tasks_count',
            'started_at',
            'completed_at',
            'terminated_at',
            'terminated_by',
            'termination_reason',
            'duration_hours',
            'is_active',
            'is_terminal',
            'estimated_hours',
            'approval_chain',
            'graph_snapshot',
        ]

    def get_definition(self, obj):
        """Get simplified definition info."""
        return {
            'id': str(obj.definition.id),
            'code': obj.definition.code,
            'name': obj.definition.name,
            'version': obj.definition.version,
        }

    def get_approval_chain(self, obj):
        """Get approval chain."""
        return obj.get_approval_chain()


class WorkflowInstanceCreateSerializer(BaseModelSerializer):
    """Serializer for creating workflow instances."""

    definition_id = serializers.UUIDField(write_only=True)
    variables = serializers.JSONField(required=False, default=dict)

    class Meta(BaseModelSerializer.Meta):
        model = WorkflowInstance
        fields = BaseModelSerializer.Meta.fields + [
            'definition_id',
            'business_object_code',
            'business_id',
            'business_no',
            'variables',
            'title',
            'description',
            'priority',
            'estimated_hours',
        ]

    def validate_definition_id(self, value):
        """Validate definition exists and is published."""
        try:
            definition = WorkflowDefinition.objects.get(id=value, is_deleted=False)
            if definition.status != 'published':
                raise serializers.ValidationError(
                    _('Workflow definition must be published to start instances.')
                )
            return definition
        except WorkflowDefinition.DoesNotExist:
            raise serializers.ValidationError(
                _('Workflow definition not found.')
            )


class WorkflowInstanceUpdateSerializer(BaseModelSerializer):
    """Serializer for updating workflow instances."""

    class Meta(BaseModelSerializer.Meta):
        model = WorkflowInstance
        fields = [
            'title',
            'description',
            'priority',
            'estimated_hours',
            'variables',
        ]


class WorkflowInstanceStartSerializer(serializers.Serializer):
    """Serializer for starting a workflow instance."""

    definition_id = serializers.UUIDField(required=True)
    business_object_code = serializers.CharField(max_length=50, required=True)
    business_id = serializers.CharField(max_length=100, required=True)
    business_no = serializers.CharField(max_length=100, required=False, allow_blank=True)
    variables = serializers.JSONField(required=False, default=dict)
    title = serializers.CharField(max_length=200, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    priority = serializers.ChoiceField(
        choices=['low', 'normal', 'high', 'urgent'],
        default='normal',
        required=False
    )

    def validate_definition_id(self, value):
        """Validate definition exists and is published."""
        try:
            definition = WorkflowDefinition.objects.get(id=value, is_deleted=False)
            if definition.status != 'published':
                raise serializers.ValidationError(
                    _('Workflow definition must be published to start instances.')
                )
            return definition
        except WorkflowDefinition.DoesNotExist:
            raise serializers.ValidationError(
                _('Workflow definition not found.')
            )


# === WorkflowTask Serializers ===

class WorkflowTaskListSerializer(BaseModelSerializer):
    """Lightweight serializer for task list views."""

    instance_no = serializers.CharField(source='instance.instance_no', read_only=True)
    instance_title = serializers.CharField(source='instance.title', read_only=True)
    business_object_code = serializers.CharField(
        source='instance.business_object_code', read_only=True
    )
    business_id = serializers.CharField(source='instance.business_id', read_only=True)
    assignee_name = serializers.CharField(
        source='assignee.get_full_name', read_only=True
    )
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    remaining_hours = serializers.FloatField(read_only=True)
    duration_hours = serializers.FloatField(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = WorkflowTask
        fields = [
            'id',
            'instance_no',
            'instance_title',
            'business_object_code',
            'business_id',
            'node_id',
            'node_name',
            'node_type',
            'approve_type',
            'assignee',
            'assignee_name',
            'status',
            'status_display',
            'sequence',
            'due_date',
            'is_overdue',
            'remaining_hours',
            'duration_hours',
            'priority',
            'created_at',
        ]


class WorkflowTaskDetailSerializer(BaseModelSerializer):
    """Detailed serializer for single task view."""

    instance = WorkflowInstanceListSerializer(read_only=True)
    assignee = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_pending = serializers.BooleanField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    remaining_hours = serializers.FloatField(read_only=True)
    duration_hours = serializers.FloatField(read_only=True)
    approvals_summary = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = WorkflowTask
        fields = [
            'id',
            'instance',
            'node_id',
            'node_name',
            'node_type',
            'approve_type',
            'assignee',
            'status',
            'status_display',
            'sequence',
            'due_date',
            'completed_at',
            'completed_by',
            'is_pending',
            'is_completed',
            'is_overdue',
            'remaining_hours',
            'duration_hours',
            'priority',
            'node_properties',
            'delegated_to',
            'delegated_from',
            'delegated_at',
            'delegation_reason',
            'approvals_summary',
            'created_at',
            'updated_at',
        ]

    def get_approvals_summary(self, obj):
        """Get approvals summary with serialized latest approval."""
        summary = obj.get_approvals_summary()
        # Serialize the latest approval object if it exists
        if summary.get('latest'):
            summary['latest'] = WorkflowApprovalSerializer(summary['latest']).data
        return summary


class WorkflowTaskActionSerializer(serializers.Serializer):
    """Serializer for task actions (approve, reject, return).

    The action is determined by the endpoint being called, so this field
    is not required in the request payload.
    """

    action = serializers.ChoiceField(
        choices=['approve', 'reject', 'return'],
        required=False  # Action is implicit from the endpoint
    )
    comment = serializers.CharField(required=False, allow_blank=True)


class WorkflowTaskDelegateSerializer(serializers.Serializer):
    """Serializer for task delegation."""

    to_user_id = serializers.UUIDField(required=True)
    reason = serializers.CharField(required=False, allow_blank=True)


class WorkflowTaskReassignSerializer(serializers.Serializer):
    """Serializer for task reassignment (admin action)."""

    assignee_id = serializers.UUIDField(required=True)
    reason = serializers.CharField(required=False, allow_blank=True)


# === WorkflowApproval Serializers ===

class WorkflowApprovalSerializer(BaseModelSerializer):
    """Serializer for workflow approval records."""

    task_node_name = serializers.CharField(source='task.node_name', read_only=True)
    approver_name = serializers.CharField(
        source='approver.get_full_name', read_only=True
    )
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = WorkflowApproval
        fields = [
            'id',
            'task',
            'task_node_name',
            'approver',
            'approver_name',
            'action',
            'action_display',
            'comment',
            'attachment',
            'ip_address',
            'previous_status',
            'new_status',
            'created_at',
        ]


# === Combined Serializers ===

class MyTasksSerializer(serializers.Serializer):
    """Serializer for 'my tasks' endpoint."""

    pending = WorkflowTaskListSerializer(many=True, read_only=True)
    overdue = WorkflowTaskListSerializer(many=True, read_only=True)
    completed_today = WorkflowTaskListSerializer(many=True, read_only=True)
    summary = serializers.DictField(read_only=True)


class TaskDetailWithInstanceSerializer(serializers.Serializer):
    """Combined serializer for task detail with instance info."""

    task = WorkflowTaskDetailSerializer(read_only=True)
    instance = WorkflowInstanceDetailSerializer(read_only=True)
    definition = serializers.SerializerMethodField()
    next_tasks = serializers.SerializerMethodField()
    previous_tasks = serializers.SerializerMethodField()

    def get_definition(self, obj):
        """Get definition info."""
        return {
            'id': str(obj['task'].instance.definition.id),
            'code': obj['task'].instance.definition.code,
            'name': obj['task'].instance.definition.name,
        }

    def get_next_tasks(self, obj):
        """Get next tasks in workflow."""
        instance = obj['task'].instance
        current_sequence = obj['task'].sequence
        return list(
            instance.tasks.filter(
                sequence__gt=current_sequence,
                status='pending'
            ).values_list('id', flat=True)
        )

    def get_previous_tasks(self, obj):
        """Get previous tasks in workflow."""
        instance = obj['task'].instance
        current_sequence = obj['task'].sequence
        return list(
            instance.tasks.filter(
                sequence__lt=current_sequence
            ).values_list('id', flat=True)
        )


# === Statistics Serializers ===

class WorkflowStatisticsSerializer(serializers.Serializer):
    """Serializer for workflow statistics."""

    total_instances = serializers.IntegerField(read_only=True)
    pending_instances = serializers.IntegerField(read_only=True)
    completed_instances = serializers.IntegerField(read_only=True)
    my_pending_tasks = serializers.IntegerField(read_only=True)
    my_completed_tasks = serializers.IntegerField(read_only=True)
    my_overdue_tasks = serializers.IntegerField(read_only=True)
    average_completion_hours = serializers.FloatField(read_only=True)
    instances_by_status = serializers.DictField(read_only=True)
    instances_by_definition = serializers.DictField(read_only=True)


# Import timezone for is_overdue calculation
from django.utils import timezone
