"""Closed-loop operational metrics API views."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.common.middleware import normalize_organization_id
from apps.common.responses.base import BaseResponse
from apps.common.services.organization_service import BaseOrganizationService
from apps.system.serializers import (
    ClosedLoopDashboardSnapshotCreateSerializer,
    ClosedLoopDashboardSnapshotDetailSerializer,
    ClosedLoopDashboardSnapshotListSerializer,
)
from apps.system.services.closed_loop_metrics_service import ClosedLoopMetricsService
from apps.system.services.closed_loop_snapshot_service import ClosedLoopDashboardSnapshotService


class BaseClosedLoopMetricsAPIView(APIView):
    """Shared behavior for closed-loop metrics endpoints."""

    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.service = ClosedLoopMetricsService()
        self.snapshot_service = ClosedLoopDashboardSnapshotService()

    def _get_window_key(self, request) -> str:
        return (
            request.query_params.get("window")
            or request.query_params.get("range_key")
            or "30d"
        )

    def _get_object_codes(self, request) -> list[str] | None:
        raw_value = request.query_params.get("object_codes", "")
        object_codes = [value.strip() for value in raw_value.split(",") if value.strip()]
        return object_codes or None

    def _resolve_organization_id(self, request):
        requested_organization_id = self._read_requested_organization_id(request)
        if requested_organization_id:
            if not BaseOrganizationService.check_organization_access(
                request.user,
                requested_organization_id,
            ):
                return None
            return requested_organization_id

        if getattr(request, "organization_id", None):
            return normalize_organization_id(request.organization_id)

        default_organization = request.user.ensure_default_organization()
        if default_organization:
            return normalize_organization_id(default_organization.id)
        return None

    def _read_requested_organization_id(self, request):
        requested_organization_id = normalize_organization_id(
            request.query_params.get("organization_id")
        )
        if requested_organization_id:
            return requested_organization_id

        if request.method.upper() in {"POST", "PUT", "PATCH"}:
            raw_body_org_id = request.data.get("organization_id") if isinstance(request.data, dict) else None
            return normalize_organization_id(raw_body_org_id)

        return None


class ClosedLoopMetricsOverviewAPIView(BaseClosedLoopMetricsAPIView):
    """Return aggregated cross-domain closed-loop overview metrics."""

    def get(self, request, *args, **kwargs):
        organization_id = self._resolve_organization_id(request)
        if not organization_id:
            return BaseResponse.permission_denied("Organization context is required.")

        payload = self.service.build_overview(
            window_key=self._get_window_key(request),
            organization_id=organization_id,
            user=request.user,
            object_codes=self._get_object_codes(request),
        )
        return BaseResponse.success(
            data=payload,
            message="Closed-loop overview loaded successfully.",
        )


class ClosedLoopMetricsByObjectAPIView(BaseClosedLoopMetricsAPIView):
    """Return normalized closed-loop metrics grouped by business object."""

    def get(self, request, *args, **kwargs):
        organization_id = self._resolve_organization_id(request)
        if not organization_id:
            return BaseResponse.permission_denied("Organization context is required.")

        payload = self.service.build_by_object(
            window_key=self._get_window_key(request),
            organization_id=organization_id,
            user=request.user,
            object_codes=self._get_object_codes(request),
        )
        return BaseResponse.success(
            data=payload,
            message="Closed-loop object metrics loaded successfully.",
        )


class ClosedLoopMetricsQueuesAPIView(BaseClosedLoopMetricsAPIView):
    """Return normalized closed-loop operational queues across domains."""

    def get(self, request, *args, **kwargs):
        organization_id = self._resolve_organization_id(request)
        if not organization_id:
            return BaseResponse.permission_denied("Organization context is required.")

        payload = self.service.build_queues(
            window_key=self._get_window_key(request),
            organization_id=organization_id,
            user=request.user,
            object_codes=self._get_object_codes(request),
        )
        return BaseResponse.success(
            data=payload,
            message="Closed-loop queues loaded successfully.",
        )


class ClosedLoopMetricsBottlenecksAPIView(BaseClosedLoopMetricsAPIView):
    """Return normalized closed-loop bottleneck rankings."""

    def get(self, request, *args, **kwargs):
        organization_id = self._resolve_organization_id(request)
        if not organization_id:
            return BaseResponse.permission_denied("Organization context is required.")

        payload = self.service.build_bottlenecks(
            window_key=self._get_window_key(request),
            organization_id=organization_id,
            user=request.user,
            object_codes=self._get_object_codes(request),
        )
        return BaseResponse.success(
            data=payload,
            message="Closed-loop bottlenecks loaded successfully.",
        )


class ClosedLoopDashboardSnapshotListCreateAPIView(BaseClosedLoopMetricsAPIView):
    """List or create shared closed-loop dashboard snapshots."""

    def get(self, request, *args, **kwargs):
        organization_id = self._resolve_organization_id(request)
        if not organization_id:
            return BaseResponse.permission_denied("Organization context is required.")

        queryset = self.snapshot_service.list_snapshots(
            organization_id=organization_id,
            user=request.user,
        )
        serializer = ClosedLoopDashboardSnapshotListSerializer(queryset, many=True)
        return BaseResponse.success(
            data={"results": serializer.data},
            message="Closed-loop snapshots loaded successfully.",
        )

    def post(self, request, *args, **kwargs):
        organization_id = self._resolve_organization_id(request)
        if not organization_id:
            return BaseResponse.permission_denied("Organization context is required.")

        serializer = ClosedLoopDashboardSnapshotCreateSerializer(
            data=self._normalize_snapshot_create_payload(request)
        )
        serializer.is_valid(raise_exception=True)
        snapshot = self.snapshot_service.create_snapshot(
            label=serializer.validated_data["label"],
            window_key=serializer.validated_data["window_key"],
            organization_id=organization_id,
            user=request.user,
            object_codes=serializer.validated_data.get("object_codes") or [],
        )
        response_serializer = ClosedLoopDashboardSnapshotDetailSerializer(snapshot)
        return BaseResponse.created(
            data=response_serializer.data,
            message="Closed-loop snapshot created successfully.",
        )

    def _normalize_snapshot_create_payload(self, request):
        payload = dict(request.data or {})
        if "window_key" not in payload and "window" in payload:
            payload["window_key"] = payload.get("window")
        return payload


class ClosedLoopDashboardSnapshotDetailAPIView(BaseClosedLoopMetricsAPIView):
    """Retrieve or delete a shared closed-loop dashboard snapshot."""

    def get(self, request, snapshot_id, *args, **kwargs):
        organization_id = self._resolve_organization_id(request)
        if not organization_id:
            return BaseResponse.permission_denied("Organization context is required.")

        snapshot = self._get_snapshot(snapshot_id=snapshot_id, organization_id=organization_id, user=request.user)
        if snapshot is None:
            return BaseResponse.not_found("Closed-loop snapshot")
        serializer = ClosedLoopDashboardSnapshotDetailSerializer(snapshot)
        return BaseResponse.success(
            data=serializer.data,
            message="Closed-loop snapshot loaded successfully.",
        )

    def delete(self, request, snapshot_id, *args, **kwargs):
        organization_id = self._resolve_organization_id(request)
        if not organization_id:
            return BaseResponse.permission_denied("Organization context is required.")

        snapshot = self._get_snapshot(snapshot_id=snapshot_id, organization_id=organization_id, user=request.user)
        if snapshot is None:
            return BaseResponse.not_found("Closed-loop snapshot")
        self.snapshot_service.delete(snapshot.id, user=request.user, organization_id=organization_id)
        return BaseResponse.success(message="Closed-loop snapshot deleted successfully.")

    def _get_snapshot(self, *, snapshot_id, organization_id, user):
        try:
            return self.snapshot_service.get(
                snapshot_id,
                organization_id=organization_id,
                user=user,
            )
        except self.snapshot_service.model_class.DoesNotExist:
            return None
