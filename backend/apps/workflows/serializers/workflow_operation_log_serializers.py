"""
Serializers for WorkflowOperationLog model.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.common.serializers.base import BaseModelSerializer
from apps.workflows.models.workflow_operation_log import WorkflowOperationLog


class WorkflowOperationLogSerializer(BaseModelSerializer):
    """
    Serializer for WorkflowOperationLog.

    Provides audit trail information for workflow operations.
    """

    # Read-only fields
    operation_type_display = serializers.CharField(
        source='get_operation_type_display',
        read_only=True
    )
    target_type_display = serializers.CharField(
        source='get_target_type_display',
        read_only=True
    )
    result_display = serializers.CharField(
        source='get_result_display',
        read_only=True
    )

    # Actor info
    actor_username = serializers.CharField(source='actor.username', read_only=True)
    actor_full_name = serializers.CharField(source='actor.get_full_name', read_only=True)

    # Workflow info
    workflow_name = serializers.CharField(source='workflow_definition.name', read_only=True)
    workflow_code = serializers.CharField(source='workflow_definition.code', read_only=True)
    template_name = serializers.CharField(source='workflow_template.name', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = WorkflowOperationLog
        fields = BaseModelSerializer.Meta.fields + [
            'actor',
            'actor_username',
            'actor_full_name',
            'operation_type',
            'operation_type_display',
            'target_type',
            'target_type_display',
            'workflow_definition',
            'workflow_template',
            'target_name',
            'target_code',
            'workflow_name',
            'workflow_code',
            'template_name',
            'operation_details',
            'previous_state',
            'result',
            'result_display',
            'error_message',
            'ip_address',
            'user_agent',
        ]


class WorkflowOperationLogListSerializer(WorkflowOperationLogSerializer):
    """
    Lightweight serializer for operation log list views.
    """

    class Meta(WorkflowOperationLogSerializer.Meta):
        fields = [
            'id',
            'operation_type',
            'operation_type_display',
            'target_type',
            'target_name',
            'target_code',
            'result',
            'result_display',
            'actor_username',
            'created_at',
        ]
