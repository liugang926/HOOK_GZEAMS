"""Server-side snapshot service for the closed-loop operations dashboard."""

from __future__ import annotations

from typing import Any

from apps.common.services.base_crud import BaseCRUDService
from apps.system.models import ClosedLoopDashboardSnapshot
from apps.system.services.closed_loop_metrics_service import ClosedLoopMetricsService


class ClosedLoopDashboardSnapshotService(BaseCRUDService):
    """Create, query, and delete organization-scoped closed-loop snapshots."""

    def __init__(self):
        super().__init__(ClosedLoopDashboardSnapshot)
        self.metrics_service = ClosedLoopMetricsService()

    def list_snapshots(self, *, organization_id, user=None):
        queryset = self.model_class.objects.filter(
            dashboard_code='closed_loop',
        ).order_by('-created_at')
        return self._scope_queryset(queryset, organization_id=organization_id, user=user)

    def build_snapshot_payload(
        self,
        *,
        window_key: str,
        organization_id,
        user=None,
        object_codes: list[str] | None = None,
    ) -> dict[str, Any]:
        return {
            'overview': self.metrics_service.build_overview(
                window_key=window_key,
                organization_id=organization_id,
                user=user,
                object_codes=object_codes,
            ),
            'by_object_items': self.metrics_service.build_by_object(
                window_key=window_key,
                organization_id=organization_id,
                user=user,
                object_codes=object_codes,
            )['results'],
            'queues': self.metrics_service.build_queues(
                window_key=window_key,
                organization_id=organization_id,
                user=user,
                object_codes=object_codes,
            )['results'],
            'bottlenecks': self.metrics_service.build_bottlenecks(
                window_key=window_key,
                organization_id=organization_id,
                user=user,
                object_codes=object_codes,
            )['results'],
        }

    def create_snapshot(
        self,
        *,
        label: str,
        window_key: str,
        organization_id,
        user,
        object_codes: list[str] | None = None,
    ):
        normalized_object_codes = [
            str(code).strip()
            for code in (object_codes or [])
            if str(code).strip()
        ]
        payload = self.build_snapshot_payload(
            window_key=window_key,
            organization_id=organization_id,
            user=user,
            object_codes=normalized_object_codes,
        )
        return self.create(
            {
                'label': str(label).strip(),
                'dashboard_code': 'closed_loop',
                'window_key': window_key,
                'object_codes': normalized_object_codes,
                'overview_payload': payload['overview'],
                'by_object_payload': payload['by_object_items'],
                'queues_payload': payload['queues'],
                'bottlenecks_payload': payload['bottlenecks'],
            },
            user=user,
            organization_id=organization_id,
        )
