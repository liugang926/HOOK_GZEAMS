"""Runtime serializers for inventory manual follow-up tasks."""

from rest_framework import serializers

from apps.accounts.serializers import UserBasicSerializer
from apps.common.serializers.base import BaseModelSerializer
from apps.inventory.models import InventoryFollowUp
from apps.inventory.services import InventoryExceptionClosureService


class InventoryFollowUpSerializer(BaseModelSerializer):
    """Detail serializer for inventory follow-up tasks."""

    task_code = serializers.CharField(source='task.task_code', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    difference_type = serializers.CharField(source='difference.difference_type', read_only=True)
    difference_type_label = serializers.CharField(
        source='difference.get_difference_type_display',
        read_only=True,
    )
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    assignee = UserBasicSerializer(read_only=True)
    completed_by = UserBasicSerializer(read_only=True)
    closure_type_label = serializers.CharField(source='difference.get_closure_type_display', read_only=True)
    difference_detail_url = serializers.SerializerMethodField()
    closure_summary = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = InventoryFollowUp
        fields = BaseModelSerializer.Meta.fields + [
            'follow_up_code',
            'task',
            'task_code',
            'difference',
            'difference_detail_url',
            'asset',
            'asset_code',
            'asset_name',
            'title',
            'difference_type',
            'difference_type_label',
            'closure_type',
            'closure_type_label',
            'linked_action_code',
            'status',
            'status_label',
            'assignee',
            'assigned_at',
            'completed_at',
            'completed_by',
            'completion_notes',
            'evidence_refs',
            'follow_up_notification_id',
            'follow_up_notification_url',
            'last_notified_at',
            'reminder_count',
            'closure_summary',
        ]

    @staticmethod
    def get_difference_detail_url(instance: InventoryFollowUp) -> str:
        return f"/objects/InventoryItem/{instance.difference_id}"

    def get_closure_summary(self, instance: InventoryFollowUp):
        """Return a normalized closure summary for the follow-up workbench."""
        return InventoryExceptionClosureService().build_follow_up_summary(instance)


class InventoryFollowUpListSerializer(BaseModelSerializer):
    """List serializer for inventory follow-up tasks."""

    task_code = serializers.CharField(source='task.task_code', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    assignee = UserBasicSerializer(read_only=True)
    difference_type_label = serializers.CharField(
        source='difference.get_difference_type_display',
        read_only=True,
    )
    status_label = serializers.CharField(source='get_status_display', read_only=True)
    closure_summary = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = InventoryFollowUp
        fields = [
            'id',
            'follow_up_code',
            'task',
            'task_code',
            'difference',
            'asset',
            'asset_code',
            'asset_name',
            'title',
            'difference_type_label',
            'closure_type',
            'linked_action_code',
            'status',
            'status_label',
            'assignee',
            'assigned_at',
            'completed_at',
            'reminder_count',
            'closure_summary',
            'created_at',
        ]

    def get_closure_summary(self, instance: InventoryFollowUp):
        """Return a normalized closure summary for list rows and queues."""
        return InventoryExceptionClosureService().build_follow_up_summary(instance)


class InventoryFollowUpCompleteSerializer(serializers.Serializer):
    """Serializer for completing a follow-up task."""

    completion_notes = serializers.CharField(
        required=False,
        allow_blank=True,
    )
    evidence_refs = serializers.ListField(
        required=False,
        child=serializers.CharField(),
    )

    class Meta:
        fields = ['completion_notes', 'evidence_refs']


class InventoryFollowUpReopenSerializer(serializers.Serializer):
    """Serializer for reopening a completed follow-up task."""

    class Meta:
        fields = []
