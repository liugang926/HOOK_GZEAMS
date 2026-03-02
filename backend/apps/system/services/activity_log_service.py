from typing import List, Dict, Any, Optional
from django.contrib.contenttypes.models import ContentType

class ActivityLogService:
    """Service for handling Activity Timeline logging."""

    @staticmethod
    def log_action(
        actor,
        action: str,
        instance,
        changes: Optional[List[Dict[str, Any]]] = None,
        description: Optional[str] = None,
        organization=None
    ):
        """
        Log an action for a specific instance.
        
        Args:
            actor: User instance performing the action.
            action: String matching ActivityLog.ACTION_CHOICES.
            instance: The Django model instance the action was performed on.
            changes: Optional list of dicts: {'fieldLabel': str, 'oldValue': any, 'newValue': any}
            description: Optional human-readable description.
            organization: Optional organization reference. Falls back to instance.organization.
        """
        from apps.system.models import ActivityLog
        
        content_type = ContentType.objects.get_for_model(instance)
        org = organization or getattr(instance, 'organization', None)

        log = ActivityLog.objects.create(
            actor=actor,
            action=action,
            content_type=content_type,
            object_id=str(instance.pk),
            changes=changes,
            description=description,
            organization=org,
            created_by=actor
        )
        return log

    @staticmethod
    def get_object_timeline(instance):
        """Retrieve the timeline logs for a given object instance."""
        from apps.system.models import ActivityLog
        content_type = ContentType.objects.get_for_model(instance)
        
        return ActivityLog.objects.filter(
            content_type=content_type,
            object_id=str(instance.pk),
            is_deleted=False
        ).select_related('actor').order_by('-created_at')
