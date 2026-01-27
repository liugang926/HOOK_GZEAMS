"""
Service for integration log management.

Provides business logic for querying and analyzing IntegrationLog instances.
"""
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from django.db.models import Count, Avg, Q, F
from django.db.models.functions import TruncDate

from apps.common.services.base_crud import BaseCRUDService
from apps.integration.models import IntegrationLog

logger = logging.getLogger(__name__)


class IntegrationLogService(BaseCRUDService):
    """Service for IntegrationLog management."""

    def __init__(self):
        """Initialize service with IntegrationLog model."""
        super().__init__(IntegrationLog)

    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get log statistics for the specified period.

        Args:
            days: Number of days to look back

        Returns:
            Dict with statistics
        """
        since_date = datetime.now() - timedelta(days=days)

        queryset = self.query().filter(created_at__gte=since_date)

        total = queryset.count()
        success = queryset.filter(success=True).count()
        failed = queryset.filter(success=False).count()

        # Calculate success rate
        success_rate = (success / total * 100) if total > 0 else 0

        # Calculate average duration
        avg_duration = queryset.aggregate(
            avg_dur=Avg('duration_ms')
        )['avg_dur'] or 0

        # Group by system type
        by_system = list(
            queryset.values('system_type').annotate(
                count=Count('id')
            ).order_by('-count')
        )

        # Group by action
        by_action = list(
            queryset.values('action').annotate(
                count=Count('id')
            ).order_by('-count')
        )

        return {
            'total': total,
            'success': success,
            'failed': failed,
            'success_rate': round(success_rate, 2),
            'avg_duration_ms': round(avg_duration, 2),
            'by_system': by_system,
            'by_action': by_action,
        }

    def get_error_logs(
        self,
        limit: int = 100
    ) -> List[IntegrationLog]:
        """
        Get recent error logs.

        Args:
            limit: Maximum number of logs to return

        Returns:
            List of failed IntegrationLog instances
        """
        return list(self.query(
            filters={'success': False},
            order_by='-created_at'
        ))[:limit]

    def get_logs_by_task(self, task_id: str) -> List[IntegrationLog]:
        """
        Get logs for a specific sync task.

        Args:
            task_id: Sync task ID

        Returns:
            List of IntegrationLog instances
        """
        return list(self.query(
            filters={'sync_task__task_id': task_id},
            order_by='created_at'
        ))

    def get_logs_by_system_type(
        self,
        system_type: str,
        limit: int = 50
    ) -> List[IntegrationLog]:
        """
        Get recent logs for a specific system type.

        Args:
            system_type: System type identifier
            limit: Maximum number of logs to return

        Returns:
            List of IntegrationLog instances
        """
        return list(self.query(
            filters={'system_type': system_type},
            order_by='-created_at'
        ))[:limit]

    def get_slow_requests(
        self,
        threshold_ms: int = 5000,
        limit: int = 50
    ) -> List[IntegrationLog]:
        """
        Get slow requests (above threshold).

        Args:
            threshold_ms: Duration threshold in milliseconds
            limit: Maximum number of logs to return

        Returns:
            List of slow IntegrationLog instances
        """
        return list(self.query(
            filters={'duration_ms__gte': threshold_ms},
            order_by='-duration_ms'
        ))[:limit]

    def get_daily_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Get daily statistics for the specified period.

        Args:
            days: Number of days to look back

        Returns:
            List of daily statistics
        """
        since_date = datetime.now() - timedelta(days=days)

        queryset = self.query().filter(
            created_at__gte=since_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            total=Count('id'),
            success=Count('id', filter=Q(success=True)),
            failed=Count('id', filter=Q(success=False)),
            avg_duration=Avg('duration_ms')
        ).order_by('-date')

        return list(queryset)

    def cleanup_old_logs(self, days_to_keep: int = 90) -> int:
        """
        Soft delete old logs beyond retention period.

        Args:
            days_to_keep: Number of days to keep logs

        Returns:
            Number of logs deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)

        old_logs = self.query().filter(
            created_at__lt=cutoff_date
        )

        count = old_logs.count()

        for log in old_logs:
            log.soft_delete()

        logger.info(f"Cleaned up {count} old integration logs (older than {days_to_keep} days)")

        return count
