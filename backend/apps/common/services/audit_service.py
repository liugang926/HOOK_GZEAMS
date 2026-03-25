"""
Audit Logging Service.

Comprehensive audit logging for compliance and security.
Tracks all system actions, user activities, and data changes.
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)

User = get_user_model()


class AuditLogger:
    """
    Comprehensive audit logging service.
    
    Features:
    - Action logging
    - Data change tracking
    - Compliance reporting
    - Security event logging
    - Audit trail management
    """
    
    # Audit event types
    EVENT_TYPES = {
        'user_login': 'User Login',
        'user_logout': 'User Logout',
        'user_created': 'User Created',
        'user_updated': 'User Updated',
        'user_deleted': 'User Deleted',
        'workflow_created': 'Workflow Created',
        'workflow_updated': 'Workflow Updated',
        'workflow_deleted': 'Workflow Deleted',
        'workflow_submitted': 'Workflow Submitted',
        'workflow_approved': 'Workflow Approved',
        'workflow_rejected': 'Workflow Rejected',
        'task_assigned': 'Task Assigned',
        'task_completed': 'Task Completed',
        'permission_changed': 'Permission Changed',
        'role_changed': 'Role Changed',
        'data_exported': 'Data Exported',
        'data_imported': 'Data Imported',
        'security_event': 'Security Event',
        'system_config': 'System Configuration Changed',
        'api_access': 'API Access',
        'rate_limit_exceeded': 'Rate Limit Exceeded',
        'validation_failed': 'Validation Failed'
    }
    
    def __init__(self):
        self.enabled = getattr(settings, 'AUDIT_LOGGING_ENABLED', True)
        self.cache_prefix = 'audit_log'
        self.retention_days = getattr(settings, 'AUDIT_LOG_RETENTION_DAYS', 90)
    
    def log(self, event_type: str, actor_id: Any, actor_type: str,
            action: str, details: Dict[str, Any] = None,
            ip_address: str = None, user_agent: str = None,
            object_type: str = None, object_id: Any = None,
            timestamp: datetime = None) -> str:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event (from EVENT_TYPES)
            actor_id: ID of the actor performing the action
            actor_type: Type of actor (user, system, api)
            action: Description of the action performed
            details: Additional event details
            ip_address: IP address of the actor
            user_agent: User agent string
            object_type: Type of object affected
            object_id: ID of object affected
            timestamp: Event timestamp (default: now)
            
        Returns:
            Event ID for tracking
        """
        if not self.enabled:
            return None
        
        import uuid
        event_id = str(uuid.uuid4())
        
        event = {
            'event_id': event_id,
            'event_type': event_type,
            'event_name': self.EVENT_TYPES.get(event_type, event_type),
            'actor_id': str(actor_id) if actor_id else None,
            'actor_type': actor_type,
            'action': action,
            'details': details or {},
            'ip_address': ip_address,
            'user_agent': user_agent,
            'object_type': object_type,
            'object_id': str(object_id) if object_id else None,
            'timestamp': (timestamp or datetime.now()).isoformat(),
            'severity': self._get_event_severity(event_type)
        }
        
        # Store in cache (in production, this would go to a database or log service)
        cache_key = f"{self.cache_prefix}_events"
        events = cache.get(cache_key, [])
        events.append(event)
        
        # Keep only last 10000 events in cache
        if len(events) > 10000:
            events = events[-10000:]
        
        cache.set(cache_key, events, 86400 * self.retention_days)
        
        # Log to standard logger for immediate visibility
        log_level = self._get_log_level(event['severity'])
        getattr(logger, log_level)(
            f"AUDIT: {actor_type} {actor_id} - {action} - {event_type}"
        )
        
        # Trigger alerts for security events
        if event_type == 'security_event' or event_type == 'rate_limit_exceeded':
            self._handle_security_event(event)
        
        return event_id
    
    def _get_event_severity(self, event_type: str) -> str:
        """Determine event severity."""
        high_severity = [
            'user_deleted', 'security_event', 'rate_limit_exceeded',
            'permission_changed', 'role_changed'
        ]
        
        medium_severity = [
            'workflow_rejected', 'validation_failed'
        ]
        
        if event_type in high_severity:
            return 'high'
        elif event_type in medium_severity:
            return 'medium'
        else:
            return 'low'
    
    def _get_log_level(self, severity: str) -> str:
        """Get Python logging level from severity."""
        return {
            'high': 'error',
            'medium': 'warning',
            'low': 'info'
        }.get(severity, 'info')
    
    def _handle_security_event(self, event: Dict[str, Any]) -> None:
        """Handle security event logging and alerting."""
        # Store in dedicated security events cache
        security_key = f"{self.cache_prefix}_security_events"
        security_events = cache.get(security_key, [])
        security_events.append(event)
        cache.set(security_key, security_events, 86400 * 30)  # 30 days
        
        # Could trigger additional alerting here
        logger.error(f"SECURITY EVENT: {event['action']}")
    
    def log_workflow_action(self, event_type: str, workflow_instance: Any,
                           actor_id: Any, action: str, details: Dict = None) -> str:
        """Log workflow-related action."""
        return self.log(
            event_type=event_type,
            actor_id=actor_id,
            actor_type='user',
            action=action,
            details=details,
            object_type='workflow_instance',
            object_id=workflow_instance.id if hasattr(workflow_instance, 'id') else None
        )
    
    def log_user_action(self, event_type: str, user_id: Any, action: str,
                       ip_address: str = None, user_agent: str = None) -> str:
        """Log user-related action."""
        return self.log(
            event_type=event_type,
            actor_id=user_id,
            actor_type='user',
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            object_type='user',
            object_id=user_id
        )
    
    def log_security_event(self, action: str, details: Dict = None,
                          ip_address: str = None, user_agent: str = None) -> str:
        """Log security event."""
        return self.log(
            event_type='security_event',
            actor_id='system',
            actor_type='system',
            action=action,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def get_audit_trail(self, object_type: str, object_id: Any,
                       hours: int = 24) -> List[Dict[str, Any]]:
        """
        Get audit trail for a specific object.
        
        Args:
            object_type: Type of object
            object_id: ID of object
            hours: Number of hours to look back
            
        Returns:
            List of audit events
        """
        cache_key = f"{self.cache_prefix}_events"
        all_events = cache.get(cache_key, [])
        
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        filtered_events = []
        for event in all_events:
            try:
                event_time = datetime.fromisoformat(event['timestamp']).timestamp()
                if event_time >= cutoff_time:
                    if event.get('object_type') == object_type and \
                       event.get('object_id') == str(object_id):
                        filtered_events.append(event)
            except (ValueError, KeyError):
                continue
        
        return filtered_events
    
    def get_user_activity(self, user_id: Any, hours: int = 24) -> List[Dict[str, Any]]:
        """Get audit trail for a specific user."""
        cache_key = f"{self.cache_prefix}_events"
        all_events = cache.get(cache_key, [])
        
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        user_events = []
        for event in all_events:
            try:
                event_time = datetime.fromisoformat(event['timestamp']).timestamp()
                if event_time >= cutoff_time and event.get('actor_id') == str(user_id):
                    user_events.append(event)
            except (ValueError, KeyError):
                continue
        
        return user_events
    
    def get_security_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get security events."""
        security_key = f"{self.cache_prefix}_security_events"
        all_events = cache.get(security_key, [])
        
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        filtered_events = []
        for event in all_events:
            try:
                event_time = datetime.fromisoformat(event['timestamp']).timestamp()
                if event_time >= cutoff_time:
                    filtered_events.append(event)
            except (ValueError, KeyError):
                continue
        
        return filtered_events
    
    def generate_compliance_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """
        Generate compliance report for audit.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Compliance report data
        """
        cache_key = f"{self.cache_prefix}_events"
        all_events = cache.get(cache_key, [])
        
        # Filter by date range
        filtered_events = []
        for event in all_events:
            try:
                event_time = datetime.fromisoformat(event['timestamp'])
                if start_date <= event_time <= end_date:
                    filtered_events.append(event)
            except (ValueError, KeyError):
                continue
        
        # Generate statistics
        event_types = {}
        actors = {}
        objects = {}
        
        for event in filtered_events:
            # Count by event type
            event_type = event['event_type']
            event_types[event_type] = event_types.get(event_type, 0) + 1
            
            # Count by actor
            actor = f"{event['actor_type']}:{event['actor_id']}"
            actors[actor] = actors.get(actor, 0) + 1
            
            # Count by object type
            if event.get('object_type'):
                obj = f"{event['object_type']}:{event.get('object_id', 'unknown')}"
                objects[obj] = objects.get(obj, 0) + 1
        
        return {
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'total_events': len(filtered_events),
            'by_event_type': event_types,
            'by_actor': actors,
            'by_object': objects,
            'security_events': len([e for e in filtered_events if e['severity'] == 'high']),
            'high_severity_events': len([e for e in filtered_events if e['severity'] == 'high']),
            'medium_severity_events': len([e for e in filtered_events if e['severity'] == 'medium'])
        }
    
    def cleanup_old_logs(self) -> int:
        """Clean up audit logs older than retention period."""
        cache_key = f"{self.cache_prefix}_events"
        all_events = cache.get(cache_key, [])
        
        cutoff_time = datetime.now().timestamp() - (self.retention_days * 86400)
        
        cleaned_events = []
        for event in all_events:
            try:
                event_time = datetime.fromisoformat(event['timestamp']).timestamp()
                if event_time >= cutoff_time:
                    cleaned_events.append(event)
            except (ValueError, KeyError):
                continue
        
        removed_count = len(all_events) - len(cleaned_events)
        cache.set(cache_key, cleaned_events, 86400 * self.retention_days)
        
        logger.info(f"Cleaned up {removed_count} old audit log entries")
        
        return removed_count


# Global audit logger instance
audit_logger = AuditLogger()


def log_event(event_type: str, actor_id: Any, actor_type: str,
              action: str, details: Dict = None, **kwargs) -> str:
    """Log audit event using global logger."""
    return audit_logger.log(event_type, actor_id, actor_type, action, details, **kwargs)


def log_workflow_action(event_type: str, workflow_instance: Any,
                       actor_id: Any, action: str, details: Dict = None) -> str:
    """Log workflow action using global logger."""
    return audit_logger.log_workflow_action(event_type, workflow_instance, actor_id, action, details)


def log_user_action(event_type: str, user_id: Any, action: str,
                   ip_address: str = None, user_agent: str = None) -> str:
    """Log user action using global logger."""
    return audit_logger.log_user_action(event_type, user_id, action, ip_address, user_agent)


def log_security_event(action: str, details: Dict = None,
                      ip_address: str = None, user_agent: str = None) -> str:
    """Log security event using global logger."""
    return audit_logger.log_security_event(action, details, ip_address, user_agent)


def get_audit_trail(object_type: str, object_id: Any, hours: int = 24) -> List[Dict[str, Any]]:
    """Get audit trail using global logger."""
    return audit_logger.get_audit_trail(object_type, object_id, hours)


def generate_compliance_report(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Generate compliance report using global logger."""
    return audit_logger.generate_compliance_report(start_date, end_date)