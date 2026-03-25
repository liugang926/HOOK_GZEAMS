"""
Application Performance Monitoring (APM) Service.

Provides real-time performance monitoring, error tracking, and SLA compliance monitoring.
Includes automatic alert generation based on configurable thresholds.
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.core.cache import cache
from django.db import connection
import psutil
import threading

from apps.common.models import BaseModel

logger = logging.getLogger(__name__)


class APMMonitor:
    """
    Application Performance Monitoring Service.
    
    Monitors:
    - API response times
    - Error rates
    - Memory usage
    - Database performance
    """
    
    def __init__(self):
        self.enabled = getattr(settings, 'APM_ENABLED', True)
        self.cache_prefix = 'apm_stats'
        self.alert_thresholds = self._load_alert_thresholds()
        self._metrics_buffer = []
        self._lock = threading.Lock()
        
    def _load_alert_thresholds(self) -> Dict[str, Any]:
        """Load alert thresholds from configuration."""
        try:
            from apps.workflows.configs.alert_rules import alert_rules
            return alert_rules.get('alert_rules', {})
        except ImportError:
            # Fallback to defaults
            return {
                'workflow_performance': {
                    'api_response_time': {'warning': 300, 'critical': 500},
                    'error_rate': {'warning': 2, 'critical': 5}
                }
            }
    
    def track_api_response_time(self, endpoint: str, method: str, duration_ms: int, 
                              status_code: int = 200) -> None:
        """Track API response time and check for thresholds."""
        if not self.enabled:
            return
            
        metric_data = {
            'timestamp': datetime.now().isoformat(),
            'endpoint': endpoint,
            'method': method,
            'duration_ms': duration_ms,
            'status_code': status_code,
            'type': 'api_response_time'
        }
        
        with self._lock:
            self._metrics_buffer.append(metric_data)
            
        # Check if this violates thresholds
        self._check_response_time_threshold(endpoint, duration_ms)
        self._check_error_rate_threshold(status_code)
    
    def _check_response_time_threshold(self, endpoint: str, duration_ms: int) -> None:
        """Check if response time exceeds thresholds."""
        thresholds = self.alert_thresholds.get('workflow_performance', {})
        response_time_config = thresholds.get('api_response_time', {})
        
        if duration_ms > response_time_config.get('critical', 500):
            self._create_alert(
                'workflow_performance',
                'critical',
                f'High response time on {endpoint}: {duration_ms}ms',
                {'endpoint': endpoint, 'duration_ms': duration_ms}
            )
        elif duration_ms > response_time_config.get('warning', 300):
            self._create_alert(
                'workflow_performance',
                'warning', 
                f'Elevated response time on {endpoint}: {duration_ms}ms',
                {'endpoint': endpoint, 'duration_ms': duration_ms}
            )
    
    def _check_error_rate_threshold(self, status_code: int) -> None:
        """Check if error rate exceeds thresholds."""
        if status_code >= 400:
            thresholds = self.alert_thresholds.get('workflow_performance', {})
            error_rate_config = thresholds.get('error_rate', {})
            
            # Get recent error rate
            error_rate = self._get_recent_error_rate()
            
            if error_rate > error_rate_config.get('critical', 5):
                self._create_alert(
                    'workflow_performance',
                    'critical',
                    f'High error rate: {error_rate}%',
                    {'error_rate': error_rate, 'status_code': status_code}
                )
            elif error_rate > error_rate_config.get('warning', 2):
                self._create_alert(
                    'workflow_performance',
                    'warning',
                    f'Elevated error rate: {error_rate}%',
                    {'error_rate': error_rate, 'status_code': status_code}
                )
    
    def _get_recent_error_rate(self) -> float:
        """Calculate error rate from recent requests."""
        now = datetime.now()
        five_minutes_ago = now - timedelta(minutes=5)
        
        recent_errors = 0
        total_requests = 0
        
        with self._lock:
            for metric in self._metrics_buffer:
                try:
                    metric_time = datetime.fromisoformat(metric['timestamp'].replace('Z', '+00:00'))
                    if metric_time >= five_minutes_ago:
                        total_requests += 1
                        if metric['status_code'] >= 400:
                            recent_errors += 1
                except (ValueError, KeyError):
                    continue
        
        return (recent_errors / total_requests * 100) if total_requests > 0 else 0.0
    
    def _create_alert(self, alert_type: str, severity: str, message: str, 
                     metadata: Dict[str, Any]) -> None:
        """Create and send alert based on severity."""
        alert = {
            'type': alert_type,
            'severity': severity,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata,
            'resolved': False
        }
        
        # Cache the alert for dashboard display
        alert_key = f"{self.cache_prefix}_alerts"
        alerts = cache.get(alert_key, [])
        alerts.append(alert)
        cache.set(alert_key, alerts, 3600)  # 1 hour TTL
        
        # Log the alert
        logger.warning(f"ALERT [{severity.upper()}] {alert_type}: {message}")
        
        # Send notifications based on severity
        if severity == 'critical':
            self._send_critical_alert(alert)
        elif severity == 'warning':
            self._send_warning_alert(alert)
    
    def _send_critical_alert(self, alert: Dict[str, Any]) -> None:
        """Send critical alert notifications."""
        # TODO: Implement email/Slack notifications
        pass
    
    def _send_warning_alert(self, alert: Dict[str, Any]) -> None:
        """Send warning alert notifications."""  
        # TODO: Implement email/Slack notifications
        pass
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system performance metrics."""
        return {
            'cpu_usage': psutil.cpu_percent(interval=1),
            'memory_usage': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent
            },
            'disk_usage': {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'percent': psutil.disk_usage('/').percent
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def get_database_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics."""
        with connection.cursor() as cursor:
            try:
                # Query database metrics
                cursor.execute("""
                    SELECT query, calls, total_time, mean_time 
                    FROM pg_stat_statements 
                    ORDER BY total_time DESC 
                    LIMIT 10
                """)
                slow_queries = cursor.fetchall()
                
                # Get connection pool stats
                cursor.execute("""
                    SELECT count(*) FROM pg_stat_activity 
                    WHERE state = 'active'
                """)
                active_connections = cursor.fetchone()[0]
                
                return {
                    'slow_queries': slow_queries,
                    'active_connections': active_connections,
                    'total_queries': sum(row[1] for row in slow_queries),
                    'query_metrics': {
                        'avg_query_time': sum(row[3] for row in slow_queries) / len(slow_queries) if slow_queries else 0,
                        'total_queries': sum(row[1] for row in slow_queries)
                    }
                }
            except Exception as e:
                logger.error(f"Failed to get database metrics: {e}")
                return {'error': str(e)}
    
    def get_api_stats(self, hours: int = 1) -> Dict[str, Any]:
        """Get API performance statistics for the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            recent_metrics = [
                metric for metric in self._metrics_buffer
                if datetime.fromisoformat(metric['timestamp'].replace('Z', '+00:00')) >= cutoff_time
            ]
        
        if not recent_metrics:
            return {'message': 'No metrics available for the specified time period'}
        
        # Calculate statistics
        response_times = [m['duration_ms'] for m in recent_metrics]
        total_requests = len(recent_metrics)
        error_count = sum(1 for m in recent_metrics if m['status_code'] >= 400)
        
        # Group by endpoint
        endpoint_stats = {}
        for metric in recent_metrics:
            endpoint = metric['endpoint']
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {
                    'count': 0,
                    'total_time': 0,
                    'errors': 0
                }
            endpoint_stats[endpoint]['count'] += 1
            endpoint_stats[endpoint]['total_time'] += metric['duration_ms']
            if metric['status_code'] >= 400:
                endpoint_stats[endpoint]['errors'] += 1
        
        return {
            'time_period_hours': hours,
            'total_requests': total_requests,
            'error_count': error_count,
            'error_rate': (error_count / total_requests * 100) if total_requests > 0 else 0,
            'avg_response_time': sum(response_times) / len(response_times),
            'max_response_time': max(response_times),
            'min_response_time': min(response_times),
            'endpoint_stats': {
                endpoint: {
                    'requests': stats['count'],
                    'avg_time': stats['total_time'] / stats['count'],
                    'error_rate': (stats['errors'] / stats['count'] * 100) if stats['count'] > 0 else 0
                }
                for endpoint, stats in endpoint_stats.items()
            }
        }
    
    def cleanup_old_metrics(self, hours: int = 24) -> None:
        """Clean up old metrics data."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            self._metrics_buffer = [
                metric for metric in self._metrics_buffer
                if datetime.fromisoformat(metric['timestamp'].replace('Z', '+00:00')) >= cutoff_time
            ]
        
        logger.info(f"Cleaned up metrics older than {hours} hours. Remaining: {len(self._metrics_buffer)}")


# Global APM monitor instance
apm_monitor = APMMonitor()


def track_api_response_time(endpoint: str, method: str, duration_ms: int, status_code: int = 200) -> None:
    """Track API response time using the global monitor."""
    apm_monitor.track_api_response_time(endpoint, method, duration_ms, status_code)


def get_api_stats(hours: int = 1) -> Dict[str, Any]:
    """Get API statistics using the global monitor."""
    return apm_monitor.get_api_stats(hours)


def get_system_metrics() -> Dict[str, Any]:
    """Get system metrics using the global monitor."""
    return apm_monitor.get_system_metrics()