"""
Error Tracking Service for Workflow System.

Provides comprehensive error tracking, exception logging, and alert generation.
Integrates with APM monitoring for comprehensive observability.
"""

import logging
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from django.conf import settings
from django.core.cache import cache
from django.db import DatabaseError, IntegrityError
from django.http import Http404, PermissionDenied
import json
import uuid

from apps.common.models import BaseModel
from apps.common.services.apm_monitoring import apm_monitor

logger = logging.getLogger(__name__)


class ErrorTracker:
    """
    Comprehensive error tracking service.
    
    Features:
    - Exception classification
    - Error rate monitoring
    - Automatic alert generation
    - Error correlation
    - Performance impact analysis
    """
    
    def __init__(self):
        self.enabled = getattr(settings, 'ERROR_TRACKING_ENABLED', True)
        self.cache_prefix = 'error_tracking'
        self._error_categories = {
            'database_error': DatabaseError,
            'integrity_error': IntegrityError,
            'http_404': Http404,
            'permission_denied': PermissionDenied,
            'validation_error': ValueError,
            'authentication_error': Exception,
            'network_error': ConnectionError,
            'system_error': Exception
        }
        self._correlation_id = str(uuid.uuid4())
    
    def classify_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Classify error and determine severity and impact.
        
        Args:
            error: The exception instance
            context: Additional context about the error
            
        Returns:
            Dictionary with error classification and metadata
        """
        error_type = type(error).__name__
        error_class = type(error)
        
        # Determine category
        category = 'system_error'  # Default
        for cat_name, cat_type in self._error_categories.items():
            if isinstance(error, cat_type):
                category = cat_name
                break
        
        # Determine severity
        severity = self._determine_severity(error, category)
        
        # Determine impact
        impact = self._determine_impact(error, category, context)
        
        # Determine root cause
        root_cause = self._identify_root_cause(error, category)
        
        return {
            'error_id': str(uuid.uuid4()),
            'category': category,
            'type': error_type,
            'message': str(error),
            'severity': severity,
            'impact': impact,
            'root_cause': root_cause,
            'timestamp': datetime.now().isoformat(),
            'context': context or {},
            'correlation_id': self._correlation_id,
            'traceback': traceback.format_exc(),
            'affected_component': self._identify_affected_component(context)
        }
    
    def _determine_severity(self, error: Exception, category: str) -> str:
        """Determine error severity level."""
        # Database errors are critical
        if category == 'database_error':
            return 'critical'
        
        # Authentication/permission errors are high
        if category in ['authentication_error', 'permission_denied']:
            return 'high'
        
        # Validation errors are medium
        if category == 'validation_error':
            return 'medium'
        
        # Network errors are high
        if category == 'network_error':
            return 'high'
        
        # System errors are critical
        if category == 'system_error':
            return 'critical'
        
        return 'medium'
    
    def _determine_impact(self, error: Exception, category: str, context: Dict[str, Any]) -> str:
        """Determine business impact of error."""
        if context:
            # Check if it's an API error
            if context.get('endpoint'):
                if 'workflows' in context['endpoint']:
                    return 'high'  # Workflow errors affect business processes
                elif 'statistics' in context['endpoint']:
                    return 'medium'  # Statistics errors are less critical
            
            # Check if it affects multiple users
            if context.get('affected_users', 0) > 10:
                return 'high'
            
            # Check if it affects critical operations
            if context.get('is_critical_operation', False):
                return 'high'
        
        return 'medium' if category == 'validation_error' else 'low'
    
    def _identify_root_cause(self, error: Exception, category: str) -> str:
        """Identify potential root cause."""
        error_message = str(error).lower()
        
        # Check for common root causes
        if 'connection' in error_message or 'timeout' in error_message:
            return 'network_connectivity'
        elif 'constraint' in error_message or 'unique' in error_message:
            return 'data_integrity'
        elif 'authentication' in error_message or 'authorization' in error_message:
            return 'security'
        elif 'validation' in error_message or 'invalid' in error_message:
            return 'input_validation'
        elif 'resource' in error_message or 'memory' in error_message:
            return 'resource_exhaustion'
        else:
            return 'unknown'
    
    def _identify_affected_component(self, context: Dict[str, Any]) -> str:
        """Identify the affected component."""
        if context.get('endpoint'):
            if '/api/workflows/' in context['endpoint']:
                return 'workflow_engine'
            elif '/api/statistics/' in context['endpoint']:
                return 'statistics_service'
            elif '/api/tasks/' in context['endpoint']:
                return 'task_service'
            else:
                return 'api_layer'
        
        if context.get('component'):
            return context['component']
        
        return 'unknown'
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None) -> str:
        """
        Log error and return error ID for correlation.
        
        Args:
            error: Exception instance
            context: Additional context
            
        Returns:
            Error ID for tracking
        """
        if not self.enabled:
            return str(uuid.uuid4())
        
        # Classify error
        classification = self.classify_error(error, context)
        error_id = classification['error_id']
        
        # Log to database (using cache for now, could be replaced with proper logging)
        cache_key = f"{self.cache_prefix}_errors"
        recent_errors = cache.get(cache_key, [])
        recent_errors.append(classification)
        
        # Keep only last 1000 errors
        if len(recent_errors) > 1000:
            recent_errors = recent_errors[-1000:]
        
        cache.set(cache_key, recent_errors, 86400)  # 24 hours TTL
        
        # Log to standard logger
        if classification['severity'] == 'critical':
            logger.critical(f"CRITICAL ERROR [{classification['category']}]: {classification['message']}")
        elif classification['severity'] == 'high':
            logger.error(f"HIGH ERROR [{classification['category']}]: {classification['message']}")
        else:
            logger.warning(f"MEDIUM ERROR [{classification['category']}]: {classification['message']}")
        
        # Trigger alerts for critical errors
        self._handle_error_alert(classification)
        
        # Update APM metrics
        apm_monitor.track_api_response_time(
            context.get('endpoint', 'unknown'),
            context.get('method', 'unknown'),
            classification.get('response_time', 0),
            500  # Error status
        )
        
        return error_id
    
    def _handle_error_alert(self, classification: Dict[str, Any]) -> None:
        """Handle alert generation for errors."""
        severity = classification['severity']
        category = classification['category']
        
        # Only alert on critical and high severity errors
        if severity not in ['critical', 'high']:
            return
        
        alert_message = f"{severity.upper()} ERROR in {classification['affected_component']}: {classification['message']}"
        
        # Create alert
        from apps.common.services.apm_monitoring import APMMonitor
        apm_instance = APMMonitor()
        
        apm_instance._create_alert(
            alert_type=category,
            severity=severity,
            message=alert_message,
            metadata={
                'error_id': classification['error_id'],
                'category': category,
                'component': classification['affected_component'],
                'timestamp': classification['timestamp']
            }
        )
    
    def get_error_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get error statistics for the last N hours."""
        cache_key = f"{self.cache_prefix}_errors"
        all_errors = cache.get(cache_key, [])
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter by time
        recent_errors = [
            error for error in all_errors
            if datetime.fromisoformat(error['timestamp'].replace('Z', '+00:00')) >= cutoff_time
        ]
        
        if not recent_errors:
            return {
                'time_period_hours': hours,
                'total_errors': 0,
                'by_category': {},
                'by_severity': {},
                'by_component': {},
                'error_rate': 0,
                'top_errors': []
            }
        
        # Analyze by category
        by_category = {}
        for error in recent_errors:
            cat = error['category']
            by_category[cat] = by_category.get(cat, 0) + 1
        
        # Analyze by severity
        by_severity = {}
        for error in recent_errors:
            sev = error['severity']
            by_severity[sev] = by_severity.get(sev, 0) + 1
        
        # Analyze by component
        by_component = {}
        for error in recent_errors:
            comp = error['affected_component']
            by_component[comp] = by_component.get(comp, 0) + 1
        
        # Top errors by message
        error_messages = {}
        for error in recent_errors:
            msg = error['message']
            error_messages[msg] = error_messages.get(msg, 0) + 1
        
        top_errors = sorted(error_messages.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            'time_period_hours': hours,
            'total_errors': len(recent_errors),
            'by_category': by_category,
            'by_severity': by_severity,
            'by_component': by_component,
            'error_rate': len(recent_errors) / hours if hours > 0 else 0,  # errors per hour
            'top_errors': top_errors,
            'last_error': recent_errors[-1] if recent_errors else None
        }
    
    def get_error_trend(self, hours: int = 24, interval_minutes: int = 60) -> List[Dict[str, Any]]:
        """Get error trend over time."""
        cache_key = f"{self.cache_prefix}_errors"
        all_errors = cache.get(cache_key, [])
        
        trend_data = []
        current_time = datetime.now()
        
        # Generate time buckets
        for i in range(0, hours * 60, interval_minutes):
            bucket_start = current_time - timedelta(hours=hours) + timedelta(minutes=i)
            bucket_end = bucket_start + timedelta(minutes=interval_minutes)
            
            # Count errors in this bucket
            bucket_errors = [
                error for error in all_errors
                if bucket_start <= datetime.fromisoformat(error['timestamp'].replace('Z', '+00:00')) < bucket_end
            ]
            
            # Aggregate by category
            by_category = {}
            for error in bucket_errors:
                cat = error['category']
                by_category[cat] = by_category.get(cat, 0) + 1
            
            trend_data.append({
                'timestamp': bucket_start.isoformat(),
                'total_errors': len(bucket_errors),
                'by_category': by_category,
                'max_severity': max([e['severity'] for e in bucket_errors], default='low') if bucket_errors else 'low'
            })
        
        return trend_data
    
    def cleanup_old_errors(self, hours: int = 48) -> None:
        """Clean up old error data."""
        cache_key = f"{self.cache_prefix}_errors"
        all_errors = cache.get(cache_key, [])
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter old errors
        recent_errors = [
            error for error in all_errors
            if datetime.fromisoformat(error['timestamp'].replace('Z', '+00:00')) >= cutoff_time
        ]
        
        cache.set(cache_key, recent_errors, 86400)
        logger.info(f"Cleaned up errors older than {hours} hours. Remaining: {len(recent_errors)}")


# Global error tracker instance
error_tracker = ErrorTracker()


def track_error(error: Exception, context: Dict[str, Any] = None) -> str:
    """Track an error using the global tracker."""
    return error_tracker.log_error(error, context)


def get_error_stats(hours: int = 24) -> Dict[str, Any]:
    """Get error statistics using the global tracker."""
    return error_tracker.get_error_stats(hours)


def get_error_trend(hours: int = 24, interval_minutes: int = 60) -> List[Dict[str, Any]]:
    """Get error trend using the global tracker."""
    return error_tracker.get_error_trend(hours, interval_minutes)


# Decorator for error tracking
def track_errors(func):
    """Decorator to track errors in functions."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            context = {
                'function': func.__name__,
                'module': func.__module__,
                'args': str(args),
                'kwargs': str(kwargs)
            }
            track_error(e, context)
            raise  # Re-raise the exception
    return wrapper


# Context manager for error tracking
def error_context(context: Dict[str, Any]):
    """Context manager for tracking errors with context."""
    return ErrorTrackingContext(context)


class ErrorTrackingContext:
    """Context manager for error tracking."""
    
    def __init__(self, context: Dict[str, Any]):
        self.context = context
        self.error_id = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.error_id = track_error(exc_val, self.context)