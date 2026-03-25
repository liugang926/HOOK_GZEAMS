import copy
from typing import List, Tuple, Dict, Any

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.system.services.activity_log_service import ActivityLogService


class TrackableMixin:
    """
    Mixin to automatically track field changes and create Activity Logs.
    
    Usage:
        class Asset(BaseModel, TrackableMixin):
            # Fields that should trigger a log when modified
            tracked_fields = ['status', 'location', 'assigned_to']
            
            # Optional map of field name to human readable label
            tracked_field_labels = {
                'status': _('Status'),
                'location': _('Location'),
                'assigned_to': _('Assigned To')
            }
    """
    
    tracked_fields = []
    tracked_field_labels = {}
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_state = {}
        if self.pk:
            self._cache_original_state()

    def _cache_original_state(self):
        """Cache the current state of tracked fields."""
        if not hasattr(self, 'tracked_fields') or not self.tracked_fields:
            return
            
        for field in self.tracked_fields:
            if hasattr(self, field):
                # Use copy to avoid reference issues, specifically if relations or JSON are tracked
                # Note: deep tracking of relations requires specialized handling. Here we track IDs usually.
                val = getattr(self, field)
                if isinstance(val, models.Model):
                    self._original_state[field] = str(val) if val else None
                else:
                    self._original_state[field] = copy.copy(val)

    def _get_field_label(self, field_name: str) -> str:
        """Get the human-readable label for a field."""
        if hasattr(self, 'tracked_field_labels') and field_name in self.tracked_field_labels:
            return unicode(self.tracked_field_labels[field_name]) if callable(self.tracked_field_labels[field_name]) else str(self.tracked_field_labels[field_name])
            
        # Try to get from meta
        try:
            django_field = self._meta.get_field(field_name)
            return str(django_field.verbose_name)
        except Exception:
            # Fallback to Title Cased field name
            return field_name.replace('_', ' ').title()

    def get_tracked_changes(self) -> List[Dict[str, Any]]:
        """Determine what tracked fields have changed."""
        changes = []
        if not self.pk or not self._original_state:
            return changes
            
        for field in self.tracked_fields:
            if not hasattr(self, field):
                continue
                
            old_val = self._original_state.get(field)
            current_raw = getattr(self, field)
            
            # Stringify model instances for comparison 
            if isinstance(current_raw, models.Model):
                new_val = str(current_raw) if current_raw else None
            else:
                new_val = current_raw
                
            if old_val != new_val:
                # Handle display values for choices
                display_method = f'get_{field}_display'
                if hasattr(self, display_method):
                    # We need the previous display value somehow, this is tricky. 
                    # For simplicity, we just store raw new/old if we can't easily map old_val back.
                    pass 
                    
                changes.append({
                    'fieldLabel': self._get_field_label(field),
                    'fieldCode': field,
                    'oldValue': str(old_val) if old_val is not None else '',
                    'newValue': str(new_val) if new_val is not None else ''
                })
                
        return changes

    def save(self, *args, **kwargs):
        """Override save to intercept and log changes."""
        actor = getattr(self, '_current_user', None) # Assumes _current_user is injected by a middleware or viewset
        
        is_creation = self.pk is None
        
        # Calculate changes before super().save()
        changes = []
        if not is_creation:
            changes = self.get_tracked_changes()
            
        super().save(*args, **kwargs)
        
        # Log after successful save
        if hasattr(self, 'tracked_fields') and self.tracked_fields and actor:
            if is_creation:
                ActivityLogService.log_action(
                    actor=actor,
                    action='create',
                    instance=self,
                    description=f"{self._meta.verbose_name} created."
                )
            elif changes:
                ActivityLogService.log_action(
                    actor=actor,
                    action='update',
                    instance=self,
                    changes=changes
                )
        
        # Re-cache state
        self._cache_original_state()
