"""
Dashboard API viewset.

Provides aggregated data for the frontend dashboard page,
including asset summary, user task counts, alert notices,
quick action links, and recent activity timeline.
"""
import logging

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

logger = logging.getLogger(__name__)


class DashboardViewSet(ViewSet):
    """
    Aggregated dashboard data for the authenticated user.

    Endpoint:
        GET /api/dashboard/summary/
    """

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """
        Return aggregated dashboard data.

        Response sections:
        - asset_summary: total/in_use/idle/maintenance counts
        - my_tasks: pending approvals, pickups, overdue
        - alerts: actionable warning/info notices
        - quick_actions: shortcut buttons for common operations
        - recent_activities: latest operations timeline
        """
        user = request.user
        org_id = getattr(user, 'current_organization_id', None)

        data = {
            'asset_summary': self._get_asset_summary(org_id),
            'my_tasks': self._get_my_tasks(user, org_id),
            'alerts': self._get_alerts(org_id),
            'quick_actions': self._get_quick_actions(),
            'recent_activities': self._get_recent_activities(org_id),
        }
        return Response({'success': True, 'data': data}, status=status.HTTP_200_OK)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_asset_summary(self, org_id):
        """Aggregate asset counts by status."""
        try:
            from apps.assets.models import Asset
            qs = Asset.objects.all()
            if org_id:
                qs = qs.filter(organization_id=org_id)

            status_counts = qs.values('asset_status').annotate(
                count=Count('id')
            )
            summary = {
                'total_assets': 0,
                'in_use': 0,
                'idle': 0,
                'maintenance': 0,
                'disposed': 0,
            }
            for row in status_counts:
                s = row['asset_status']
                c = row['count']
                summary['total_assets'] += c
                if s == 'in_use':
                    summary['in_use'] = c
                elif s in ('idle', 'pending'):
                    summary['idle'] += c
                elif s == 'maintenance':
                    summary['maintenance'] = c
                elif s in ('scrapped', 'disposed'):
                    summary['disposed'] += c
            return summary
        except Exception as exc:
            logger.warning("Failed to get asset summary: %s", exc)
            return {'total_assets': 0, 'in_use': 0, 'idle': 0, 'maintenance': 0, 'disposed': 0}

    def _get_my_tasks(self, user, org_id):
        """Count pending tasks for the current user."""
        result = {'pending_approvals': 0, 'pending_pickups': 0, 'overdue_tasks': 0}
        try:
            from apps.workflows.models import WorkflowTask
            pending = WorkflowTask.objects.filter(
                assignee=user,
                status='pending',
            )
            if org_id:
                pending = pending.filter(
                    workflow_instance__organization_id=org_id,
                )
            result['pending_approvals'] = pending.count()

            overdue = pending.filter(
                deadline__lt=timezone.now(),
            )
            result['overdue_tasks'] = overdue.count()
        except Exception as exc:
            logger.warning("Failed to get my tasks: %s", exc)

        try:
            from apps.assets.models import AssetPickup
            pickups = AssetPickup.objects.filter(
                applicant=user,
                status='pending',
            )
            if org_id:
                pickups = pickups.filter(organization_id=org_id)
            result['pending_pickups'] = pickups.count()
        except Exception as exc:
            logger.warning("Failed to get pending pickups: %s", exc)

        return result

    def _get_alerts(self, org_id):
        """Generate alert notices based on current data state."""
        alerts = []
        try:
            from apps.assets.models import Asset
            qs = Asset.objects.all()
            if org_id:
                qs = qs.filter(organization_id=org_id)

            maintenance_count = qs.filter(asset_status='maintenance').count()
            if maintenance_count > 0:
                alerts.append({
                    'type': 'warning',
                    'title': f'{maintenance_count} asset(s) currently under maintenance',
                    'link': '/objects/Asset?asset_status=maintenance',
                })

            idle_count = qs.filter(asset_status__in=['idle', 'pending']).count()
            if idle_count > 10:
                alerts.append({
                    'type': 'info',
                    'title': f'{idle_count} idle assets available for allocation',
                    'link': '/objects/Asset?asset_status=idle',
                })
        except Exception as exc:
            logger.warning("Failed to get alerts: %s", exc)

        try:
            from apps.inventory.models import InventoryTask
            qs = InventoryTask.objects.filter(status='in_progress')
            if org_id:
                qs = qs.filter(organization_id=org_id)
            active_count = qs.count()
            if active_count > 0:
                alerts.append({
                    'type': 'info',
                    'title': f'{active_count} inventory task(s) in progress',
                    'link': '/objects/InventoryTask',
                })
        except Exception:
            pass  # Inventory module may not have data yet

        return alerts

    def _get_quick_actions(self):
        """Return shortcut action buttons for the dashboard."""
        return [
            {
                'code': 'create_pickup',
                'label': 'New Asset Pickup',
                'icon': 'box',
                'route': '/objects/AssetPickup/create',
            },
            {
                'code': 'create_transfer',
                'label': 'New Transfer',
                'icon': 'sort',
                'route': '/objects/AssetTransfer/create',
            },
            {
                'code': 'my_approvals',
                'label': 'My Approvals',
                'icon': 'check',
                'route': '/workflow/my-approvals',
            },
            {
                'code': 'asset_list',
                'label': 'Asset List',
                'icon': 'list',
                'route': '/objects/Asset',
            },
        ]

    def _get_recent_activities(self, org_id):
        """Get up to 10 recent activities from workflow and asset logs."""
        activities = []
        try:
            from apps.workflows.models import WorkflowOperationLog
            logs = WorkflowOperationLog.objects.select_related(
                'operator'
            ).order_by('-created_at')[:10]

            for log in logs:
                actor_name = ''
                if log.operator:
                    actor_name = getattr(log.operator, 'username', str(log.operator))
                activities.append({
                    'action': str(log.action or log.operation_type),
                    'actor': actor_name,
                    'target': str(getattr(log, 'workflow_instance_id', '')),
                    'timestamp': log.created_at.isoformat() if log.created_at else '',
                })
        except Exception as exc:
            logger.warning("Failed to get recent activities: %s", exc)

        return activities[:10]
