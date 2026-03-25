"""
Serializers for Inventory Task model.
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from apps.common.serializers.base import BaseModelSerializer, BaseModelWithAuditSerializer
from apps.accounts.serializers import UserBasicSerializer
from apps.organizations.serializers import DepartmentSerializer
from apps.assets.serializers.category import AssetCategorySerializer
from apps.inventory.models import InventoryTask, InventoryTaskExecutor


class InventoryTaskExecutorSerializer(serializers.ModelSerializer):
    """Serializer for InventoryTaskExecutor (M2M through model)."""

    executor_id = serializers.CharField(source='executor.id', read_only=True)
    executor_name = serializers.CharField(source='executor.get_full_name', read_only=True)
    executor_username = serializers.CharField(source='executor.username', read_only=True)

    class Meta:
        model = InventoryTaskExecutor
        fields = [
            'id',
            'executor_id',
            'executor_name',
            'executor_username',
            'is_primary',
            'completed_count',
        ]


class InventoryTaskListSerializer(BaseModelSerializer):
    """Serializer for inventory task list view."""

    progress_percentage = serializers.ReadOnlyField()
    status_label = serializers.CharField(source='get_status_label', read_only=True)
    inventory_type_label = serializers.CharField(source='get_inventory_type_label', read_only=True)

    # Nested relationships (simplified)
    executors = InventoryTaskExecutorSerializer(
        source='executors_relation',
        many=True,
        read_only=True
    )
    department_name = serializers.CharField(source='department.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = InventoryTask
        fields = BaseModelSerializer.Meta.fields + [
            'task_code',
            'task_name',
            'description',
            'inventory_type',
            'inventory_type_label',
            'department',
            'department_name',
            'category',
            'category_name',
            'sample_ratio',
            'status',
            'status_label',
            'planned_date',
            'started_at',
            'completed_at',
            'total_count',
            'scanned_count',
            'normal_count',
            'surplus_count',
            'missing_count',
            'damaged_count',
            'location_changed_count',
            'progress_percentage',
            'notes',
            'executors',
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + [
            'task_code',
            'progress_percentage',
            'status_label',
            'inventory_type_label',
        ]


class InventoryTaskDetailSerializer(BaseModelSerializer):
    """Serializer for inventory task detail view."""

    progress_percentage = serializers.ReadOnlyField()
    status_label = serializers.CharField(source='get_status_label', read_only=True)
    inventory_type_label = serializers.CharField(source='get_inventory_type_label', read_only=True)

    # Full nested relationships
    executors = InventoryTaskExecutorSerializer(
        source='executors_relation',
        many=True,
        read_only=True
    )
    department = DepartmentSerializer(read_only=True)
    category = AssetCategorySerializer(read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = InventoryTask
        fields = BaseModelSerializer.Meta.fields + [
            'task_code',
            'task_name',
            'description',
            'inventory_type',
            'inventory_type_label',
            'department',
            'category',
            'sample_ratio',
            'status',
            'status_label',
            'planned_date',
            'started_at',
            'completed_at',
            'total_count',
            'scanned_count',
            'normal_count',
            'surplus_count',
            'missing_count',
            'damaged_count',
            'location_changed_count',
            'progress_percentage',
            'notes',
            'executors',
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + [
            'task_code',
            'progress_percentage',
            'status_label',
            'inventory_type_label',
        ]


class InventoryTaskCreateSerializer(BaseModelSerializer):
    """Serializer for creating inventory tasks."""

    executor_ids = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text=_('List of executor user IDs')
    )
    primary_executor_id = serializers.CharField(
        required=False,
        help_text=_('Primary executor user ID')
    )

    class Meta(BaseModelSerializer.Meta):
        model = InventoryTask
        fields = BaseModelSerializer.Meta.fields + [
            'task_name',
            'description',
            'inventory_type',
            'department',
            'category',
            'sample_ratio',
            'planned_date',
            'notes',
            'executor_ids',
            'primary_executor_id',
        ]
        write_only_fields = ['executor_ids', 'primary_executor_id']

    def validate(self, attrs):
        """Validate inventory task configuration."""
        inventory_type = attrs.get('inventory_type')

        # Validate department is provided for department inventory
        if inventory_type == 'department' and not attrs.get('department'):
            raise serializers.ValidationError({
                'department': _('Department is required for department inventory.')
            })

        # Validate category is provided for category inventory
        if inventory_type == 'category' and not attrs.get('category'):
            raise serializers.ValidationError({
                'category': _('Category is required for category inventory.')
            })

        # Validate sample_ratio is provided for partial inventory
        if inventory_type == 'partial' and not attrs.get('sample_ratio'):
            raise serializers.ValidationError({
                'sample_ratio': _('Sample ratio is required for partial inventory.')
            })

        return attrs


class InventoryTaskUpdateSerializer(BaseModelSerializer):
    """Serializer for updating inventory tasks."""

    class Meta(BaseModelSerializer.Meta):
        model = InventoryTask
        fields = [
            'task_name',
            'description',
            'planned_date',
            'notes',
        ]


class InventoryTaskStartSerializer(serializers.Serializer):
    """Serializer for starting an inventory task."""

    class Meta:
        fields = []

    def validate(self, attrs):
        """Validate that task can be started."""
        # Validation happens in ViewSet
        return attrs


class InventoryTaskCompleteSerializer(serializers.Serializer):
    """Serializer for completing an inventory task."""

    notes = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Completion notes')
    )

    class Meta:
        fields = ['notes']
