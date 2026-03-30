"""
Serializers for Inventory Difference model.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.common.serializers.base import BaseModelSerializer
from apps.accounts.serializers import UserBasicSerializer
from apps.inventory.models import InventoryDifference
from apps.inventory.services import InventoryExceptionClosureService


class InventoryDifferenceSerializer(BaseModelSerializer):
    """Serializer for inventory difference."""

    difference_type_label = serializers.CharField(source='get_difference_type_display', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    task_code = serializers.CharField(source='task.task_code', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)

    closure_type_label = serializers.CharField(source='get_closure_type_display', read_only=True)
    owner = UserBasicSerializer(read_only=True)
    reviewed_by = UserBasicSerializer(read_only=True)
    approved_by = UserBasicSerializer(read_only=True)
    closed_by = UserBasicSerializer(read_only=True)
    resolved_by = UserBasicSerializer(read_only=True)
    closure_summary = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = InventoryDifference
        fields = BaseModelSerializer.Meta.fields + [
            'task',
            'task_code',
            'asset',
            'asset_code',
            'asset_name',
            'difference_type',
            'difference_type_label',
            'description',
            'expected_quantity',
            'actual_quantity',
            'quantity_difference',
            'expected_location',
            'actual_location',
            'expected_custodian',
            'actual_custodian',
            'status',
            'status_label',
            'resolution',
            'owner',
            'reviewed_by',
            'reviewed_at',
            'approved_by',
            'approved_at',
            'resolved_by',
            'resolved_at',
            'closed_by',
            'closure_type',
            'closure_type_label',
            'closure_notes',
            'closure_completed_at',
            'evidence_refs',
            'linked_action_code',
            'closure_summary',
        ]

    def get_closure_summary(self, instance: InventoryDifference):
        """Return a normalized closure summary for workbench rendering."""
        return InventoryExceptionClosureService().build_difference_summary(instance)


class InventoryDifferenceListSerializer(BaseModelSerializer):
    """Serializer for inventory difference list view."""

    difference_type_label = serializers.CharField(source='get_difference_type_display', read_only=True)
    status_label = serializers.CharField(source='get_status_display', read_only=True)

    task_code = serializers.CharField(source='task.task_code', read_only=True)
    asset_code = serializers.CharField(source='asset.asset_code', read_only=True)
    asset_name = serializers.CharField(source='asset.asset_name', read_only=True)
    owner = UserBasicSerializer(read_only=True)
    closure_summary = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = InventoryDifference
        fields = [
            'id',
            'task',
            'task_code',
            'asset',
            'asset_code',
            'asset_name',
            'difference_type',
            'difference_type_label',
            'description',
            'expected_quantity',
            'actual_quantity',
            'quantity_difference',
            'expected_location',
            'actual_location',
            'expected_custodian',
            'actual_custodian',
            'status',
            'status_label',
            'owner',
            'closure_summary',
            'created_at',
        ]

    def get_closure_summary(self, instance: InventoryDifference):
        """Return a normalized closure summary for list rows and workbench queues."""
        return InventoryExceptionClosureService().build_difference_summary(instance)


class InventoryDifferenceResolveSerializer(serializers.Serializer):
    """Serializer for resolving inventory differences."""

    status = serializers.ChoiceField(
        choices=['resolved', 'ignored'],
        help_text=_('New status for the difference')
    )
    resolution = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Resolution description')
    )

    class Meta:
        fields = ['status', 'resolution']


class InventoryDifferenceAssignOwnerSerializer(serializers.Serializer):
    """Serializer for assigning an owner to a difference."""

    owner_id = serializers.CharField(
        help_text=_('Owner user ID')
    )

    class Meta:
        fields = ['owner_id']


class InventoryDifferenceSubmitReviewSerializer(serializers.Serializer):
    """Serializer for submitting a difference resolution for review."""

    resolution = serializers.CharField(
        required=False,
        allow_blank=False,
        help_text=_('Resolution description')
    )
    closure_type = serializers.ChoiceField(
        required=False,
        choices=InventoryDifference.CLOSURE_TYPE_CHOICES,
        help_text=_('Closure type')
    )
    linked_action_code = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Linked downstream action code')
    )
    evidence_refs = serializers.ListField(
        required=False,
        child=serializers.CharField(),
        help_text=_('Evidence reference list')
    )

    class Meta:
        fields = ['resolution', 'closure_type', 'linked_action_code', 'evidence_refs']


class InventoryDifferenceDraftSerializer(serializers.Serializer):
    """Serializer for saving draft handling data on a difference."""

    resolution = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Draft resolution description')
    )
    closure_type = serializers.ChoiceField(
        required=False,
        allow_blank=True,
        choices=InventoryDifference.CLOSURE_TYPE_CHOICES,
        help_text=_('Draft closure type')
    )
    linked_action_code = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Draft linked downstream action code')
    )
    evidence_refs = serializers.ListField(
        required=False,
        child=serializers.CharField(),
        help_text=_('Draft evidence reference list')
    )
    closure_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Draft closure notes')
    )

    class Meta:
        fields = ['resolution', 'closure_type', 'linked_action_code', 'evidence_refs', 'closure_notes']


class InventoryDifferenceDecisionSerializer(serializers.Serializer):
    """Serializer for approval and rejection decisions."""

    closure_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Decision notes')
    )

    class Meta:
        fields = ['closure_notes']


class InventoryDifferenceExecuteSerializer(serializers.Serializer):
    """Serializer for execution of a difference resolution."""

    resolution = serializers.CharField(
        required=False,
        allow_blank=False,
        help_text=_('Resolution description')
    )
    sync_asset = serializers.BooleanField(
        required=False,
        default=True,
        help_text=_('Whether to sync asset data during execution')
    )
    linked_action_code = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Linked downstream action code')
    )

    class Meta:
        fields = ['resolution', 'sync_asset', 'linked_action_code']


class InventoryDifferenceFollowUpSerializer(serializers.Serializer):
    """Serializer for manual follow-up reminder actions."""

    class Meta:
        fields = []


class InventoryDifferenceCompleteFollowUpSerializer(serializers.Serializer):
    """Serializer for completing a manual follow-up task from the difference detail page."""

    completion_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Completion notes for the manual follow-up')
    )
    evidence_refs = serializers.ListField(
        required=False,
        child=serializers.CharField(),
        help_text=_('Evidence references for the follow-up completion')
    )

    class Meta:
        fields = ['completion_notes', 'evidence_refs']


class InventoryDifferenceReopenFollowUpSerializer(serializers.Serializer):
    """Serializer for reopening a manual follow-up task from the difference detail page."""

    class Meta:
        fields = []


class InventoryDifferenceIgnoreSerializer(serializers.Serializer):
    """Serializer for ignoring a difference."""

    resolution = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Ignore reason')
    )
    closure_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Ignore notes')
    )

    class Meta:
        fields = ['resolution', 'closure_notes']


class InventoryDifferenceCloseSerializer(serializers.Serializer):
    """Serializer for closing a resolved or ignored difference."""

    closure_notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Closure notes')
    )
    evidence_refs = serializers.ListField(
        required=False,
        child=serializers.CharField(),
        help_text=_('Evidence reference list')
    )

    class Meta:
        fields = ['closure_notes', 'evidence_refs']
