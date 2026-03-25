"""
SLA Monitoring Dashboard API.

Provides real-time SLA compliance metrics, alert configuration, and historical trend views.
Integrates with workflow engine and notification system.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Count, Avg, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.common.responses.base import BaseResponse
from apps.workflows.models import WorkflowInstance, WorkflowTask, WorkflowDefinition
from apps.workflows.serializers.sla_dashboard_serializers import SLAAlertConfigSerializer
from apps.workflows.configs.alert_rules import load_alert_rules
from apps.workflows.services.sla_service import SLATracker
from apps.common.services.apm_monitoring import get_api_stats
from apps.workflows.services.error_tracking import get_error_stats

logger = logging.getLogger(__name__)


class SLADashboardView(APIView):
    """
    SLA Monitoring Dashboard API.
    
    Provides:
    - Real-time compliance metrics
    - Alert configuration
    - Historical trend views
    - Performance insights
    """
    
    def get(self, request):
        """Get comprehensive SLA dashboard data."""
        try:
            # Get query parameters
            time_range = request.query_params.get('time_range', '24h')
            include_trends = request.query_params.get('include_trends', 'true').lower() == 'true'
            
            # Calculate time range
            now = timezone.now()
            if time_range == '7d':
                start_time = now - timedelta(days=7)
            elif time_range == '30d':
                start_time = now - timedelta(days=30)
            else:  # Default 24h
                start_time = now - timedelta(hours=24)
            
            # Get SLA metrics
            sla_metrics = self._get_sla_metrics(start_time, now)
            
            # Get performance metrics
            performance_metrics = self._get_performance_metrics(start_time, now)
            
            # Get alert summary
            alert_summary = self._get_alert_summary()
            
            # Get trend data if requested
            trends = None
            if include_trends:
                trends = self._get_trend_data(start_time, now)
            
            # Get top issues
            top_issues = self._get_top_issues(start_time, now)
            
            dashboard_data = {
                'timestamp': now.isoformat(),
                'time_range': time_range,
                'sla_metrics': sla_metrics,
                'performance_metrics': performance_metrics,
                'alert_summary': alert_summary,
                'trends': trends,
                'top_issues': top_issues,
                'health_score': self._calculate_health_score(sla_metrics, performance_metrics)
            }
            
            return Response({
                'success': True,
                'data': dashboard_data
            })
            
        except Exception as e:
            logger.error(f"Failed to generate SLA dashboard: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_sla_metrics(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get SLA compliance metrics."""
        # Get workflow instances in time range
        instances = WorkflowInstance.objects.filter(
            created_at__gte=start_time,
            created_at__lte=end_time
        )
        
        total_instances = instances.count()
        completed_instances = instances.filter(
            status__in=[WorkflowInstance.STATUS_APPROVED, WorkflowInstance.STATUS_REJECTED]
        ).count()
        
        # Calculate SLA compliance
        sla_compliant = 0
        sla_violations = 0
        
        for instance in instances.filter(status=WorkflowInstance.STATUS_APPROVED):
            if instance.completed_at and instance.started_at:
                duration = (instance.completed_at - instance.started_at).total_seconds() / 3600
                # Assume 24-hour SLA for now (could be configurable)
                if duration <= 24:
                    sla_compliant += 1
                else:
                    sla_violations += 1
        
        # Get task SLA metrics
        tasks = WorkflowTask.objects.filter(
            created_at__gte=start_time,
            created_at__lte=end_time
        )
        
        total_tasks = tasks.count()
        overdue_tasks = tasks.filter(
            status=WorkflowTask.STATUS_PENDING,
            due_date__lt=end_time
        ).count()
        
        completed_tasks = tasks.filter(
            status=WorkflowTask.STATUS_APPROVED
        ).count()
        
        return {
            'workflow_sla': {
                'total_instances': total_instances,
                'completed_instances': completed_instances,
                'sla_compliant': sla_compliant,
                'sla_violations': sla_violations,
                'compliance_rate': (sla_compliant / completed_instances * 100) if completed_instances > 0 else 0,
                'avg_completion_time_hours': self._calculate_avg_completion_time(instances.filter(
                    status=WorkflowInstance.STATUS_APPROVED
                ))
            },
            'task_sla': {
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'overdue_tasks': overdue_tasks,
                'on_time_rate': ((completed_tasks - overdue_tasks) / total_tasks * 100) if total_tasks > 0 else 0
            }
        }
    
    def _calculate_avg_completion_time(self, instances) -> float:
        """Calculate average workflow completion time in hours."""
        completion_times = []
        for instance in instances:
            if instance.completed_at and instance.started_at:
                duration = (instance.completed_at - instance.started_at).total_seconds() / 3600
                completion_times.append(duration)
        
        return sum(completion_times) / len(completion_times) if completion_times else 0
    
    def _get_performance_metrics(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get performance metrics."""
        # Get API stats
        api_stats = get_api_stats(hours=24)
        
        # Get error stats
        error_stats = get_error_stats(hours=24)
        
        # Get cache stats
        cache_stats = self._get_cache_stats()
        
        return {
            'api_performance': {
                'total_requests': api_stats.get('total_requests', 0),
                'avg_response_time_ms': api_stats.get('avg_response_time', 0),
                'max_response_time_ms': api_stats.get('max_response_time', 0),
                'error_rate': api_stats.get('error_rate', 0)
            },
            'error_metrics': {
                'total_errors': error_stats.get('total_errors', 0),
                'error_rate_per_hour': error_stats.get('error_rate', 0),
                'by_severity': error_stats.get('by_severity', {})
            },
            'cache_performance': cache_stats
        }
    
    def _get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            from apps.common.services.redis_service import RedisService
            redis_service = RedisService()
            return redis_service.get_cache_stats()
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {
                'enabled': False,
                'error': str(e)
            }
    
    def _get_alert_summary(self) -> Dict[str, Any]:
        """Get current alert summary."""
        # Get recent alerts from cache
        alerts = cache.get('apm_stats_alerts', [])
        
        # Filter for last 24 hours
        now = timezone.now()
        recent_alerts = [
            alert for alert in alerts
            if datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00')) >= now - timedelta(hours=24)
        ]
        
        # Categorize by severity
        by_severity = {}
        for alert in recent_alerts:
            severity = alert.get('severity', 'unknown')
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        return {
            'total_alerts': len(recent_alerts),
            'by_severity': by_severity,
            'active_critical': by_severity.get('critical', 0),
            'active_warnings': by_severity.get('warning', 0),
            'last_alert': recent_alerts[-1] if recent_alerts else None
        }
    
    def _get_trend_data(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get trend data over time."""
        # Generate hourly buckets
        trends = []
        current = start_time
        while current < end_time:
            bucket_end = min(current + timedelta(hours=1), end_time)
            
            # Get metrics for this hour
            instances = WorkflowInstance.objects.filter(
                created_at__gte=current,
                created_at__lt=bucket_end
            )
            
            tasks = WorkflowTask.objects.filter(
                created_at__gte=current,
                created_at__lt=bucket_end
            )
            
            trends.append({
                'timestamp': current.isoformat(),
                'workflow_count': instances.count(),
                'task_count': tasks.count(),
                'overdue_count': tasks.filter(
                    status=WorkflowTask.STATUS_PENDING,
                    due_date__lt=bucket_end
                ).count()
            })
            
            current = bucket_end
        
        return {
            'interval': 'hourly',
            'data': trends
        }
    
    def _get_top_issues(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Get top issues affecting SLA."""
        issues = []
        
        # Get workflows with SLA violations
        violated_instances = []
        for instance in WorkflowInstance.objects.filter(
            status=WorkflowInstance.STATUS_APPROVED,
            completed_at__gte=start_time,
            completed_at__lte=end_time
        ):
            if instance.completed_at and instance.started_at:
                duration = (instance.completed_at - instance.started_at).total_seconds() / 3600
                if duration > 24:  # SLA violation
                    violated_instances.append({
                        'instance_id': str(instance.id),
                        'duration_hours': duration,
                        'definition': instance.definition.name if instance.definition else 'Unknown'
                    })
        
        if violated_instances:
            issues.append({
                'type': 'sla_violation',
                'count': len(violated_instances),
                'severity': 'high',
                'examples': violated_instances[:5]  # Top 5 examples
            })
        
        # Get overdue tasks
        overdue_tasks = WorkflowTask.objects.filter(
            status=WorkflowTask.STATUS_PENDING,
            due_date__lt=end_time,
            created_at__gte=start_time
        ).count()
        
        if overdue_tasks > 0:
            issues.append({
                'type': 'overdue_tasks',
                'count': overdue_tasks,
                'severity': 'medium',
                'impact': 'Workflow delays'
            })
        
        # Get error patterns
        error_stats = get_error_stats(hours=24)
        if error_stats.get('total_errors', 0) > 10:
            issues.append({
                'type': 'high_error_rate',
                'count': error_stats['total_errors'],
                'severity': 'high',
                'top_errors': error_stats.get('top_errors', [])[:3]
            })
        
        return issues
    
    def _calculate_health_score(self, sla_metrics: Dict, performance_metrics: Dict) -> Dict[str, Any]:
        """Calculate overall system health score."""
        score = 100
        factors = []
        
        # SLA compliance factor (40 points)
        compliance_rate = sla_metrics['workflow_sla']['compliance_rate']
        if compliance_rate < 80:
            score -= 40
            factors.append('Low SLA compliance')
        elif compliance_rate < 90:
            score -= 20
            factors.append('SLA compliance below target')
        
        # Error rate factor (30 points)
        error_rate = performance_metrics['error_metrics'].get('error_rate_per_hour', 0)
        if error_rate > 5:
            score -= 30
            factors.append('High error rate')
        elif error_rate > 2:
            score -= 15
            factors.append('Elevated error rate')
        
        # Response time factor (20 points)
        avg_response = performance_metrics['api_performance']['avg_response_time_ms']
        if avg_response > 500:
            score -= 20
            factors.append('Slow API response')
        elif avg_response > 300:
            score -= 10
            factors.append('API response above target')
        
        # Cache performance factor (10 points)
        cache_stats = performance_metrics.get('cache_performance', {})
        if cache_stats.get('enabled'):
            hit_rate = cache_stats.get('hit_rate', 0)
            if hit_rate < 80:
                score -= 10
                factors.append('Low cache hit rate')
        
        return {
            'score': max(0, score),
            'status': 'healthy' if score >= 80 else 'warning' if score >= 60 else 'critical',
            'factors': factors
        }


class SLAAlertConfigViewSet(APIView):
    """
    SLA Alert Configuration API.
    
    Manage alert thresholds and notification settings.
    """

    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current alert configuration."""
        try:
            return BaseResponse.success(data=load_alert_rules())
        except Exception as e:
            logger.error(f"Failed to load SLA alert configuration: {e}", exc_info=True)
            return BaseResponse.server_error('Failed to load alert configuration.')
    
    def post(self, request):
        """Handle POST updates for alert configuration."""
        return self.update(request)

    def update(self, request):
        """Update alert configuration thresholds."""
        serializer = SLAAlertConfigSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_configuration = serializer.update_alert_rules()
            return BaseResponse.success(
                data=updated_configuration,
                message='Alert configuration updated successfully.'
            )
        except Exception as e:
            logger.error(f"Failed to update SLA alert configuration: {e}", exc_info=True)
            return BaseResponse.server_error('Failed to update alert configuration.')


class SLAAlertConfigView(SLAAlertConfigViewSet):
    """Backward-compatible alias for the SLA alert configuration API view."""


class SLATrendView(APIView):
    """
    SLA Historical Trend API.
    
    Provide historical SLA compliance trends.
    """
    
    def get(self, request):
        """Get historical SLA trends."""
        try:
            days = int(request.query_params.get('days', 7))
            interval = request.query_params.get('interval', 'daily')
            
            end_time = timezone.now()
            start_time = end_time - timedelta(days=days)
            
            trends = []
            current = start_time
            
            if interval == 'hourly':
                delta = timedelta(hours=1)
            else:  # daily
                delta = timedelta(days=1)
            
            while current < end_time:
                bucket_end = min(current + delta, end_time)
                
                instances = WorkflowInstance.objects.filter(
                    created_at__gte=current,
                    created_at__lt=bucket_end
                )
                
                total = instances.count()
                compliant = 0
                
                for instance in instances.filter(status=WorkflowInstance.STATUS_APPROVED):
                    if instance.completed_at and instance.started_at:
                        duration = (instance.completed_at - instance.started_at).total_seconds() / 3600
                        if duration <= 24:
                            compliant += 1
                
                trends.append({
                    'timestamp': current.isoformat(),
                    'total_workflows': total,
                    'compliant_workflows': compliant,
                    'compliance_rate': (compliant / total * 100) if total > 0 else 0
                })
                
                current = bucket_end
            
            return Response({
                'success': True,
                'data': {
                    'interval': interval,
                    'period_days': days,
                    'trends': trends
                }
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
