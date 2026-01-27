"""
Serializers for Maintenance and related models.

Provides serializers for:
- Maintenance: Maintenance record CRUD operations
- MaintenancePlan: Maintenance plan CRUD operations
- MaintenanceTask: Generated task CRUD operations
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.common.serializers.base import (
    BaseModelSerializer,
    BaseModelWithAuditSerializer,
    BaseListSerializer
)
from apps.lifecycle.models import (
    Maintenance,
    MaintenanceStatus,
    MaintenancePriority,
    MaintenancePlan,
    MaintenancePlanStatus,
    MaintenancePlanCycle,
    MaintenanceTask,
    MaintenanceTaskStatus,
)
from apps.assets.models import Asset

User = get_user_model()


# ========== Lightweight Nested Serializers ==========

class LightweightAssetSerializer(serializers.ModelSerializer):
    """Lightweight asset serializer for nested display."""

    class Meta:
        model = Asset
        fields = ['id', 'asset_code', 'asset_name']


# ========== Maintenance Serializers ==========

class MaintenanceSerializer(BaseModelSerializer):
    """Serializer for Maintenance CRUD operations."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    asset_code = serializers.CharField(
        source='asset.asset_code',
        read_only=True
    )
    asset_name = serializers.CharField(
        source='asset.asset_name',
        read_only=True
    )
    reporter_name = serializers.CharField(
        source='reporter.username',
        read_only=True
    )
    technician_name = serializers.CharField(
        source='technician.username',
        read_only=True,
        allow_null=True
    )
    verified_by_name = serializers.CharField(
        source='verified_by.username',
        read_only=True,
        allow_null=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = Maintenance
        fields = BaseModelSerializer.Meta.fields + [
            'maintenance_no',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'asset',
            'asset_code',
            'asset_name',
            'reporter',
            'reporter_name',
            'report_time',
            'fault_description',
            'fault_photo_urls',
            'technician',
            'technician_name',
            'assigned_at',
            'start_time',
            'end_time',
            'work_hours',
            'fault_cause',
            'repair_method',
            'replaced_parts',
            'repair_result',
            'labor_cost',
            'material_cost',
            'other_cost',
            'total_cost',
            'verified_by',
            'verified_by_name',
            'verified_at',
            'verification_result',
            'remark',
        ]
        read_only_fields = ['maintenance_no', 'status']


class MaintenanceListSerializer(BaseListSerializer):
    """Optimized serializer for maintenance list views."""

    maintenance_no = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    priority = serializers.CharField(read_only=True)
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    asset_code = serializers.CharField(
        source='asset.asset_code',
        read_only=True
    )
    asset_name = serializers.CharField(
        source='asset.asset_name',
        read_only=True
    )
    reporter_name = serializers.CharField(
        source='reporter.username',
        read_only=True
    )
    technician_name = serializers.CharField(
        source='technician.username',
        read_only=True,
        allow_null=True
    )
    report_time = serializers.DateTimeField(read_only=True)
    total_cost = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )

    class Meta(BaseListSerializer.Meta):
        model = Maintenance
        fields = BaseListSerializer.Meta.fields + [
            'maintenance_no',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'asset',
            'asset_code',
            'asset_name',
            'reporter',
            'reporter_name',
            'technician',
            'technician_name',
            'report_time',
            'total_cost',
        ]


class MaintenanceDetailSerializer(BaseModelWithAuditSerializer):
    """Detailed serializer for maintenance with all related data."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    priority_display = serializers.CharField(
        source='get_priority_display',
        read_only=True
    )
    asset = LightweightAssetSerializer(read_only=True)
    reporter_name = serializers.CharField(
        source='reporter.username',
        read_only=True
    )
    technician_name = serializers.CharField(
        source='technician.username',
        read_only=True,
        allow_null=True
    )
    verified_by_name = serializers.CharField(
        source='verified_by.username',
        read_only=True,
        allow_null=True
    )

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = Maintenance
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'maintenance_no',
            'status',
            'status_display',
            'priority',
            'priority_display',
            'asset',
            'reporter',
            'reporter_name',
            'report_time',
            'fault_description',
            'fault_photo_urls',
            'technician',
            'technician_name',
            'assigned_at',
            'start_time',
            'end_time',
            'work_hours',
            'fault_cause',
            'repair_method',
            'replaced_parts',
            'repair_result',
            'labor_cost',
            'material_cost',
            'other_cost',
            'total_cost',
            'verified_by',
            'verified_by_name',
            'verified_at',
            'verification_result',
            'remark',
        ]
        read_only_fields = ['maintenance_no', 'status']


class MaintenanceCreateSerializer(BaseModelSerializer):
    """Serializer for creating maintenance records."""

    class Meta(BaseModelSerializer.Meta):
        model = Maintenance
        fields = BaseModelSerializer.Meta.fields + [
            'priority',
            'asset',
            'report_time',
            'fault_description',
            'fault_photo_urls',
            'remark',
        ]

    def create(self, validated_data):
        """Create maintenance record with reporter from context."""
        request = self.context.get('request')
        if request and request.user:
            validated_data['reporter'] = request.user
        return super().create(validated_data)


class MaintenanceAssignmentSerializer(BaseModelSerializer):
    """Serializer for assigning technician to maintenance."""

    class Meta(BaseModelSerializer.Meta):
        model = Maintenance
        fields = BaseModelSerializer.Meta.fields + [
            'technician',
            'assigned_at',
        ]

    def update(self, instance, validated_data):
        """Update maintenance with technician assignment."""
        instance.technician = validated_data.get('technician', instance.technician)
        instance.assigned_at = validated_data.get('assigned_at', instance.assigned_at)
        instance.status = MaintenanceStatus.ASSIGNED
        instance.save()
        return instance


class MaintenanceCompletionSerializer(BaseModelSerializer):
    """Serializer for completing maintenance record."""

    class Meta(BaseModelSerializer.Meta):
        model = Maintenance
        fields = BaseModelSerializer.Meta.fields + [
            'status',
            'start_time',
            'end_time',
            'work_hours',
            'fault_cause',
            'repair_method',
            'replaced_parts',
            'repair_result',
            'labor_cost',
            'material_cost',
            'other_cost',
            'total_cost',
            'remark',
        ]

    def update(self, instance, validated_data):
        """Update maintenance with completion data."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Calculate total cost if not provided
        if 'total_cost' not in validated_data:
            instance.total_cost = (
                instance.labor_cost + instance.material_cost + instance.other_cost
            )

        instance.status = MaintenanceStatus.COMPLETED
        instance.save()
        return instance


# ========== Maintenance Plan Serializers ==========

class MaintenancePlanSerializer(BaseModelSerializer):
    """Serializer for Maintenance Plan CRUD operations."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    cycle_type_display = serializers.CharField(
        source='get_cycle_type_display',
        read_only=True
    )
    target_type_display = serializers.CharField(
        source='get_target_type_display',
        read_only=True
    )
    asset_categories_count = serializers.SerializerMethodField()
    assets_count = serializers.SerializerMethodField()
    locations_count = serializers.SerializerMethodField()
    remind_users_count = serializers.SerializerMethodField()
    active_tasks_count = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = MaintenancePlan
        fields = BaseModelSerializer.Meta.fields + [
            'plan_name',
            'plan_code',
            'status',
            'status_display',
            'target_type',
            'target_type_display',
            'asset_categories',
            'asset_categories_count',
            'assets',
            'assets_count',
            'locations',
            'locations_count',
            'cycle_type',
            'cycle_type_display',
            'cycle_value',
            'start_date',
            'end_date',
            'remind_days_before',
            'remind_users',
            'remind_users_count',
            'maintenance_content',
            'estimated_hours',
            'remark',
            'active_tasks_count',
        ]
        extra_kwargs = {
            'asset_categories': {'required': False},
            'assets': {'required': False},
            'locations': {'required': False},
            'remind_users': {'required': False},
        }

    def get_asset_categories_count(self, obj):
        return obj.asset_categories.count()

    def get_assets_count(self, obj):
        return obj.assets.count()

    def get_locations_count(self, obj):
        return obj.locations.count()

    def get_remind_users_count(self, obj):
        return obj.remind_users.count()

    def get_active_tasks_count(self, obj):
        return obj.tasks.filter(status__in=[
            MaintenanceTaskStatus.PENDING,
            MaintenanceTaskStatus.IN_PROGRESS
        ]).count()


class MaintenancePlanListSerializer(BaseListSerializer):
    """Optimized serializer for maintenance plan list views."""

    plan_code = serializers.CharField(read_only=True)
    plan_name = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    cycle_type = serializers.CharField(read_only=True)
    cycle_type_display = serializers.CharField(
        source='get_cycle_type_display',
        read_only=True
    )
    target_type = serializers.CharField(read_only=True)
    start_date = serializers.DateField(read_only=True)
    end_date = serializers.DateField(read_only=True, allow_null=True)

    class Meta(BaseListSerializer.Meta):
        model = MaintenancePlan
        fields = BaseListSerializer.Meta.fields + [
            'plan_code',
            'plan_name',
            'status',
            'status_display',
            'target_type',
            'cycle_type',
            'cycle_type_display',
            'start_date',
            'end_date',
        ]


# ========== Maintenance Task Serializers ==========

class MaintenanceTaskSerializer(BaseModelSerializer):
    """Serializer for Maintenance Task CRUD operations."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    plan_code = serializers.CharField(
        source='plan.plan_code',
        read_only=True
    )
    plan_name = serializers.CharField(
        source='plan.plan_name',
        read_only=True
    )
    asset_code = serializers.CharField(
        source='asset.asset_code',
        read_only=True
    )
    asset_name = serializers.CharField(
        source='asset.asset_name',
        read_only=True
    )
    executor_name = serializers.CharField(
        source='executor.username',
        read_only=True,
        allow_null=True
    )
    verified_by_name = serializers.CharField(
        source='verified_by.username',
        read_only=True,
        allow_null=True
    )

    class Meta(BaseModelSerializer.Meta):
        model = MaintenanceTask
        fields = BaseModelSerializer.Meta.fields + [
            'task_no',
            'status',
            'status_display',
            'plan',
            'plan_code',
            'plan_name',
            'asset',
            'asset_code',
            'asset_name',
            'scheduled_date',
            'deadline_date',
            'executor',
            'executor_name',
            'start_time',
            'end_time',
            'execution_content',
            'execution_photo_urls',
            'finding',
            'next_maintenance_suggestion',
            'verified_by',
            'verified_by_name',
            'verified_at',
            'remark',
        ]


class MaintenanceTaskListSerializer(BaseListSerializer):
    """Optimized serializer for maintenance task list views."""

    task_no = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    plan_code = serializers.CharField(
        source='plan.plan_code',
        read_only=True
    )
    asset_code = serializers.CharField(
        source='asset.asset_code',
        read_only=True
    )
    asset_name = serializers.CharField(
        source='asset.asset_name',
        read_only=True
    )
    executor_name = serializers.CharField(
        source='executor.username',
        read_only=True,
        allow_null=True
    )
    scheduled_date = serializers.DateField(read_only=True)
    deadline_date = serializers.DateField(read_only=True)

    class Meta(BaseListSerializer.Meta):
        model = MaintenanceTask
        fields = BaseListSerializer.Meta.fields + [
            'task_no',
            'status',
            'status_display',
            'plan',
            'plan_code',
            'asset',
            'asset_code',
            'asset_name',
            'executor',
            'executor_name',
            'scheduled_date',
            'deadline_date',
        ]


class MaintenanceTaskDetailSerializer(BaseModelWithAuditSerializer):
    """Detailed serializer for maintenance task with all related data."""

    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    plan = MaintenancePlanSerializer(read_only=True)
    asset = LightweightAssetSerializer(read_only=True)
    executor_name = serializers.CharField(
        source='executor.username',
        read_only=True,
        allow_null=True
    )
    verified_by_name = serializers.CharField(
        source='verified_by.username',
        read_only=True,
        allow_null=True
    )

    class Meta(BaseModelWithAuditSerializer.Meta):
        model = MaintenanceTask
        fields = BaseModelWithAuditSerializer.Meta.fields + [
            'task_no',
            'status',
            'status_display',
            'plan',
            'asset',
            'scheduled_date',
            'deadline_date',
            'executor',
            'executor_name',
            'start_time',
            'end_time',
            'execution_content',
            'execution_photo_urls',
            'finding',
            'next_maintenance_suggestion',
            'verified_by',
            'verified_by_name',
            'verified_at',
            'remark',
        ]
        read_only_fields = ['task_no', 'status']


class MaintenanceTaskExecutionSerializer(BaseModelSerializer):
    """Serializer for executing maintenance task."""

    class Meta(BaseModelSerializer.Meta):
        model = MaintenanceTask
        fields = BaseModelSerializer.Meta.fields + [
            'status',
            'start_time',
            'end_time',
            'execution_content',
            'execution_photo_urls',
            'finding',
            'next_maintenance_suggestion',
            'remark',
        ]

    def update(self, instance, validated_data):
        """Update task with execution data."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # If completing the task, set status to completed
        if validated_data.get('end_time'):
            instance.status = MaintenanceTaskStatus.COMPLETED

        instance.save()
        return instance
