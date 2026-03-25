"""
ViewSets for asset project management models.
"""
from django.core.exceptions import ValidationError
from django.db.models import Prefetch
from rest_framework.decorators import action

from apps.assets.models import ReturnItem
from apps.common.responses.base import BaseResponse
from apps.common.viewsets.base import BaseModelViewSetWithBatch

from .filters import AssetProjectFilter, ProjectAssetFilter, ProjectMemberFilter
from .models import AssetProject, ProjectAsset, ProjectMember
from .serializers import AssetProjectSerializer, ProjectAssetSerializer, ProjectMemberSerializer
from .services import AssetProjectService, ProjectAssetService, ProjectMemberService


class AssetProjectViewSet(BaseModelViewSetWithBatch):
    """ViewSet for project definition records."""

    queryset = AssetProject.objects.select_related(
        "project_manager",
        "department",
        "organization",
        "created_by",
        "updated_by",
    ).all()
    serializer_class = AssetProjectSerializer
    filterset_class = AssetProjectFilter
    service = AssetProjectService()
    search_fields = [
        "project_code",
        "project_name",
        "project_alias",
        "project_manager__username",
        "department__name",
    ]
    ordering_fields = [
        "project_code",
        "project_name",
        "status",
        "project_type",
        "start_date",
        "end_date",
        "planned_budget",
        "actual_cost",
        "asset_cost",
        "created_at",
    ]

    @action(detail=True, methods=["post"])
    def refresh_rollups(self, request, pk=None):
        """Refresh denormalized project metrics."""
        project = self.get_object()
        project.refresh_rollups()
        serializer = self.get_serializer(project)
        return BaseResponse.success(
            serializer.data,
            message="Project summary refreshed successfully.",
        )

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        """Close a project after active assets have been processed."""
        try:
            project = self.service.close_project(
                pk,
                organization_id=getattr(request, "organization_id", None),
                user=request.user,
            )
        except ValidationError as exc:
            return BaseResponse.validation_error(
                getattr(exc, "message_dict", {"non_field_errors": exc.messages}),
                message="Project cannot be closed.",
            )

        serializer = self.get_serializer(project)
        return BaseResponse.success(
            serializer.data,
            message="Project closed successfully.",
        )

    @action(detail=True, methods=["get"])
    def workspace_dashboard(self, request, pk=None):
        """Return a unified project workspace overview payload."""
        payload = self.service.get_workspace_dashboard(
            pk,
            organization_id=getattr(request, "organization_id", None),
            user=request.user,
        )
        return BaseResponse.success(
            payload,
            message="Project workspace dashboard loaded successfully.",
        )

    @action(detail=True, methods=["get"])
    def return_dashboard(self, request, pk=None):
        """Return aggregated project-scoped AssetReturn dashboard data."""
        payload = self.service.get_return_dashboard(
            pk,
            range_key=request.query_params.get("range_key", "30d"),
            organization_id=getattr(request, "organization_id", None),
            user=request.user,
        )
        return BaseResponse.success(
            payload,
            message="Project return dashboard loaded successfully.",
        )


class ProjectAssetViewSet(BaseModelViewSetWithBatch):
    """ViewSet for project asset allocation records."""

    queryset = ProjectAsset.objects.select_related(
        "project",
        "asset",
        "allocated_by",
        "custodian",
        "organization",
        "created_by",
        "updated_by",
    ).prefetch_related(
        Prefetch(
            "return_items",
            queryset=ReturnItem.objects.select_related("asset_return"),
            to_attr="_prefetched_return_items",
        ),
    ).all()
    serializer_class = ProjectAssetSerializer
    filterset_class = ProjectAssetFilter
    service = ProjectAssetService()
    search_fields = [
        "allocation_no",
        "project__project_code",
        "project__project_name",
        "asset__asset_code",
        "asset__asset_name",
        "purpose",
        "usage_location",
    ]
    ordering_fields = [
        "allocation_no",
        "allocation_date",
        "return_date",
        "allocation_cost",
        "monthly_depreciation",
        "created_at",
    ]

    @action(detail=True, methods=["post"])
    def transfer(self, request, pk=None):
        """Transfer a project asset allocation into another project."""
        target_project_id = request.data.get("target_project_id")
        reason = request.data.get("reason", "")

        if not target_project_id:
            return BaseResponse.validation_error(
                {"target_project_id": ["This field is required."]},
                message="Target project is required.",
            )

        try:
            allocation = self.service.transfer_to_project(
                pk,
                target_project_id=target_project_id,
                reason=reason,
                organization_id=getattr(request, "organization_id", None),
                user=request.user,
            )
        except ValidationError as exc:
            return BaseResponse.validation_error(
                getattr(exc, "message_dict", {"non_field_errors": exc.messages}),
                message="Project asset transfer failed.",
            )

        serializer = self.get_serializer(allocation)
        return BaseResponse.success(
            serializer.data,
            message="Project asset transferred successfully.",
        )


class ProjectMemberViewSet(BaseModelViewSetWithBatch):
    """ViewSet for project membership records."""

    queryset = ProjectMember.objects.select_related(
        "project",
        "user",
        "organization",
        "created_by",
        "updated_by",
    ).all()
    serializer_class = ProjectMemberSerializer
    filterset_class = ProjectMemberFilter
    service = ProjectMemberService()
    search_fields = [
        "project__project_code",
        "project__project_name",
        "user__username",
        "user__first_name",
        "user__last_name",
        "responsibilities",
    ]
    ordering_fields = [
        "role",
        "is_primary",
        "join_date",
        "leave_date",
        "created_at",
    ]
