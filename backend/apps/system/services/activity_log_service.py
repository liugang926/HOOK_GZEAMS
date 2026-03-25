import copy
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional

from django.contrib.contenttypes.models import ContentType
from django.db import models


class ActivityLogService:
    """Service for creating and diffing object activity logs."""

    SYSTEM_FIELDS = {
        'id',
        'pk',
        'created_at',
        'created_by',
        'updated_at',
        'updated_by',
        'deleted_at',
        'deleted_by',
        'is_deleted',
        'organization',
        'organization_id',
        'version',
    }

    @classmethod
    def log_action(
        cls,
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
        from apps.system.activity_log import ActivityLog

        content_type = ContentType.objects.get_for_model(instance)
        org = organization or getattr(instance, 'organization', None)

        return ActivityLog.objects.create(
            actor=actor,
            action=action,
            content_type=content_type,
            object_id=str(instance.pk),
            changes=changes,
            description=description,
            organization=org,
            created_by=actor
        )

    @classmethod
    def log_create(cls, *, actor, instance, organization=None):
        if not actor or instance is None:
            return None
        return cls.log_action(
            actor=actor,
            action='create',
            instance=instance,
            organization=organization,
        )

    @classmethod
    def log_update(
        cls,
        *,
        actor,
        before_snapshot: Dict[str, Any],
        instance,
        changed_fields: Optional[Iterable[str]] = None,
        organization=None
    ):
        if not actor or instance is None:
            return None

        changes = cls.build_changes(
            before_snapshot=before_snapshot,
            after_snapshot=cls.snapshot_instance(instance, fields=changed_fields),
            field_labels=cls.get_field_labels(instance),
            changed_fields=changed_fields,
        )
        if not changes:
            return None

        return cls.log_action(
            actor=actor,
            action='update',
            instance=instance,
            changes=changes,
            organization=organization,
        )

    @classmethod
    def log_delete(cls, *, actor, instance, organization=None):
        if not actor or instance is None:
            return None
        return cls.log_action(
            actor=actor,
            action='delete',
            instance=instance,
            organization=organization,
        )

    @classmethod
    def snapshot_instance(cls, instance, fields: Optional[Iterable[str]] = None) -> Dict[str, Any]:
        if instance is None:
            return {}

        allowed = {str(field).strip() for field in (fields or []) if str(field).strip()}

        if hasattr(instance, 'dynamic_fields') and hasattr(instance, 'business_object'):
            snapshot: Dict[str, Any] = {}
            if isinstance(getattr(instance, 'dynamic_fields', None), dict):
                for key, value in instance.dynamic_fields.items():
                    if cls._should_include_field(key, allowed):
                        snapshot[key] = cls.normalize_value(value)

            for field_name in ('status', 'data_no'):
                if cls._should_include_field(field_name, allowed):
                    snapshot[field_name] = cls.normalize_value(getattr(instance, field_name, None))
            return snapshot

        snapshot = {}
        for field in instance._meta.concrete_fields:
            field_name = field.name
            if not cls._should_include_field(field_name, allowed):
                continue
            snapshot[field_name] = cls.normalize_value(cls._read_model_field_value(instance, field))
        return snapshot

    @classmethod
    def get_field_labels(cls, instance) -> Dict[str, str]:
        if instance is None:
            return {}

        if hasattr(instance, 'dynamic_fields') and hasattr(instance, 'business_object'):
            labels = {}
            try:
                for field in instance.business_object.field_definitions.filter(is_deleted=False):
                    labels[field.code] = str(field.name)
            except Exception:
                pass
            for field_name in ('status', 'data_no'):
                try:
                    labels.setdefault(field_name, str(instance._meta.get_field(field_name).verbose_name))
                except Exception:
                    labels.setdefault(field_name, field_name)
            return labels

        labels: Dict[str, str] = {}
        for field in instance._meta.concrete_fields:
            if field.name in cls.SYSTEM_FIELDS:
                continue
            labels[field.name] = str(field.verbose_name)
        return labels

    @classmethod
    def build_changes(
        cls,
        *,
        before_snapshot: Dict[str, Any],
        after_snapshot: Dict[str, Any],
        field_labels: Dict[str, str],
        changed_fields: Optional[Iterable[str]] = None
    ) -> List[Dict[str, Any]]:
        allowed = {str(field).strip() for field in (changed_fields or []) if str(field).strip()}
        candidate_fields = set(before_snapshot.keys()) | set(after_snapshot.keys())
        if allowed:
            candidate_fields &= allowed

        changes: List[Dict[str, Any]] = []
        for field_name in sorted(candidate_fields):
            if field_name in cls.SYSTEM_FIELDS:
                continue

            old_value = before_snapshot.get(field_name)
            new_value = after_snapshot.get(field_name)
            if old_value == new_value:
                continue

            changes.append({
                'fieldLabel': field_labels.get(field_name, field_name),
                'fieldCode': field_name,
                'oldValue': old_value,
                'newValue': new_value,
            })
        return changes

    @classmethod
    def get_object_timeline(cls, instance):
        """Retrieve the timeline logs for a given object instance."""
        from apps.system.activity_log import ActivityLog

        content_type = ContentType.objects.get_for_model(instance)
        return ActivityLog.objects.filter(
            content_type=content_type,
            object_id=str(instance.pk),
            is_deleted=False
        ).select_related('actor').order_by('-created_at')

    @classmethod
    def normalize_value(cls, value: Any) -> Any:
        if isinstance(value, models.Model):
            return str(value)
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, Decimal):
            return str(value)
        if isinstance(value, list):
            return [cls.normalize_value(item) for item in value]
        if isinstance(value, dict):
            return {str(key): cls.normalize_value(val) for key, val in value.items()}
        return copy.deepcopy(value)

    @classmethod
    def _read_model_field_value(cls, instance, field) -> Any:
        try:
            if field.is_relation and getattr(field, 'many_to_one', False):
                related = getattr(instance, field.name, None)
                return related if related is not None else getattr(instance, field.attname, None)
            return getattr(instance, field.name, None)
        except Exception:
            return getattr(instance, field.attname, None)

    @classmethod
    def _should_include_field(cls, field_name: str, allowed: set[str]) -> bool:
        if field_name in cls.SYSTEM_FIELDS:
            return False
        if not allowed:
            return True
        if field_name in allowed:
            return True
        snake_name = cls._camel_to_snake(field_name)
        return snake_name in allowed

    @staticmethod
    def _camel_to_snake(value: str) -> str:
        normalized = []
        for char in value:
            if char.isupper():
                normalized.append('_')
                normalized.append(char.lower())
            else:
                normalized.append(char)
        return ''.join(normalized).lstrip('_')
