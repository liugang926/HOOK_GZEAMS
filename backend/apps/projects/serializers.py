"""
Serializers for asset project management models.
"""
from rest_framework import serializers

from apps.common.serializers.base import BaseModelSerializer, UserSerializer
from apps.organizations.serializers import DepartmentSerializer

from .models import AssetProject, ProjectAsset, ProjectMember


class AssetProjectSerializer(BaseModelSerializer):
    """Serializer for asset project CRUD and detail views."""

    project_manager_detail = UserSerializer(source="project_manager", read_only=True)
    department_detail = DepartmentSerializer(source="department", read_only=True)
    asset_count = serializers.SerializerMethodField()
    active_asset_count = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = AssetProject
        fields = BaseModelSerializer.Meta.fields + [
            "project_code",
            "project_name",
            "project_alias",
            "project_manager",
            "project_manager_detail",
            "department",
            "department_detail",
            "project_type",
            "status",
            "start_date",
            "end_date",
            "actual_start_date",
            "actual_end_date",
            "planned_budget",
            "actual_cost",
            "asset_cost",
            "description",
            "technical_requirements",
            "total_assets",
            "active_assets",
            "completed_milestones",
            "total_milestones",
            "asset_count",
            "active_asset_count",
            "member_count",
            "progress",
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + ["project_code", "asset_cost", "total_assets", "active_assets"]

    def get_asset_count(self, obj):
        return obj.project_assets.filter(is_deleted=False).count()

    def get_active_asset_count(self, obj):
        return obj.project_assets.filter(is_deleted=False, return_status="in_use").count()

    def get_member_count(self, obj):
        return obj.members.filter(is_deleted=False, is_active=True).count()

    def get_progress(self, obj):
        if not obj.total_milestones:
            return 0
        return round((obj.completed_milestones / obj.total_milestones) * 100, 2)


class ProjectAssetSerializer(BaseModelSerializer):
    """Serializer for project asset allocations."""

    project_code = serializers.CharField(source="project.project_code", read_only=True)
    project_name = serializers.CharField(source="project.project_name", read_only=True)
    asset_code = serializers.CharField(source="asset.asset_code", read_only=True)
    asset_name = serializers.CharField(source="asset.asset_name", read_only=True)
    asset_status = serializers.CharField(source="asset.asset_status", read_only=True)
    allocated_by_detail = UserSerializer(source="allocated_by", read_only=True)
    custodian_detail = UserSerializer(source="custodian", read_only=True)
    latest_return_summary = serializers.SerializerMethodField()

    class Meta(BaseModelSerializer.Meta):
        model = ProjectAsset
        fields = BaseModelSerializer.Meta.fields + [
            "project",
            "project_code",
            "project_name",
            "asset",
            "asset_code",
            "asset_name",
            "asset_status",
            "allocation_no",
            "allocation_date",
            "allocation_type",
            "allocated_by",
            "allocated_by_detail",
            "custodian",
            "custodian_detail",
            "return_date",
            "actual_return_date",
            "return_status",
            "latest_return_summary",
            "allocation_cost",
            "depreciation_rate",
            "monthly_depreciation",
            "purpose",
            "usage_location",
            "asset_snapshot",
            "notes",
        ]
        read_only_fields = BaseModelSerializer.Meta.read_only_fields + [
            "allocation_no",
            "asset_snapshot",
        ]

    def validate(self, attrs):
        project = attrs.get("project") or getattr(self.instance, "project", None)
        asset = attrs.get("asset") or getattr(self.instance, "asset", None)

        if project and asset and project.organization_id and asset.organization_id:
            if str(project.organization_id) != str(asset.organization_id):
                raise serializers.ValidationError({
                    "asset": "Asset and project must belong to the same organization."
                })

        return attrs

    def get_latest_return_summary(self, obj):
        latest_return = self._resolve_latest_return_order(obj)
        if latest_return is None:
            return None

        return {
            "return_id": str(latest_return.id),
            "return_no": latest_return.return_no,
            "status": latest_return.status,
            "status_label": latest_return.get_status_label(),
            "return_date": latest_return.return_date,
            "return_reason": latest_return.return_reason,
            "reject_reason": latest_return.reject_reason,
            "event_at": (
                latest_return.completed_at
                or latest_return.confirmed_at
                or latest_return.updated_at
                or latest_return.created_at
            ),
        }

    @staticmethod
    def _resolve_latest_return_order(obj):
        prefetched_items = getattr(obj, "_prefetched_return_items", None)
        if prefetched_items is None:
            items = obj.return_items.select_related("asset_return").all()
        else:
            items = prefetched_items

        latest_return = None
        latest_rank = None
        for item in items:
            return_order = getattr(item, "asset_return", None)
            if return_order is None or getattr(return_order, "is_deleted", False):
                continue
            rank = return_order.updated_at or return_order.created_at
            if latest_rank is None or (rank is not None and rank >= latest_rank):
                latest_return = return_order
                latest_rank = rank
        return latest_return


class ProjectMemberSerializer(BaseModelSerializer):
    """Serializer for project members."""

    project_code = serializers.CharField(source="project.project_code", read_only=True)
    project_name = serializers.CharField(source="project.project_name", read_only=True)
    user_detail = UserSerializer(source="user", read_only=True)

    class Meta(BaseModelSerializer.Meta):
        model = ProjectMember
        fields = BaseModelSerializer.Meta.fields + [
            "project",
            "project_code",
            "project_name",
            "user",
            "user_detail",
            "role",
            "is_primary",
            "join_date",
            "leave_date",
            "is_active",
            "responsibilities",
            "can_allocate_asset",
            "can_view_cost",
        ]
