"""
Public System Services for Dictionary, Sequence, and Config management.

These services provide the core functionality for the Public Models,
enabling dynamic configuration without code changes.
"""
from typing import Dict, List, Optional, Any
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from apps.common.services.base_crud import BaseCRUDService


class DictionaryService(BaseCRUDService):
    """
    Dictionary Service - manages dictionary types and items.

    Provides methods for:
    - Getting dictionary items by type code
    - Validating values against dictionary
    - Caching for performance
    """

    def __init__(self):
        from apps.system.models import DictionaryType
        super().__init__(DictionaryType)

    @classmethod
    def get_items(cls, type_code: str, organization_id=None, active_only: bool = True) -> List[Dict]:
        """
        Get all items for a dictionary type.

        Args:
            type_code: Dictionary type code (e.g., 'ASSET_STATUS')
            organization_id: Organization ID for multi-tenant filtering
            active_only: Only return active items

        Returns:
            List of dictionary items as dicts
        """
        from apps.system.models import DictionaryType, DictionaryItem

        try:
            # Look for organization-specific or global dictionary
            q_filter = Q(code=type_code, is_deleted=False)
            if organization_id:
                q_filter &= (Q(organization_id=organization_id) | Q(organization_id__isnull=True))
            else:
                q_filter &= Q(organization_id__isnull=True)

            # Order by organization_id (not null first) to prioritize org-specific override
            # But in Django, nulls sort order depends on DB. safer to sort by -created_at or manual check?
            # Actually, if we have both, we want the org specific one.
            # If we simply filter, we might get two.
            # Let's simple check:
            
            candidates = DictionaryType.all_objects.filter(q_filter)
            
            # Prioritize organization specific match
            dict_type = None
            for dt in candidates:
                if dt.organization_id == organization_id:
                    dict_type = dt
                    break
            
            if not dict_type:
                # Fallback to global
                for dt in candidates:
                    if dt.organization_id is None:
                        dict_type = dt
                        break
            
            if not dict_type:
                return []

            item_filters = {'dictionary_type': dict_type, 'is_deleted': False}
            if active_only:
                item_filters['is_active'] = True

            items = DictionaryItem.all_objects.filter(**item_filters).order_by('sort_order', 'code')

            return [
                {
                    'code': item.code,
                    'name': item.name,
                    'name_en': item.name_en,
                    'color': item.color,
                    'icon': item.icon,
                    'is_default': item.is_default,
                    'extra_data': item.extra_data,
                }
                for item in items
            ]
        except Exception:
            return []

    @classmethod
    def get_item(cls, type_code: str, item_code: str, organization_id=None) -> Optional[Dict]:
        """
        Get a single dictionary item.

        Args:
            type_code: Dictionary type code
            item_code: Item code within the type
            organization_id: Organization ID

        Returns:
            Dictionary item as dict or None
        """
        items = cls.get_items(type_code, organization_id, active_only=False)
        for item in items:
            if item['code'] == item_code:
                return item
        return None

    @classmethod
    def get_label(cls, type_code: str, item_code: str, organization_id=None, lang: str = None) -> str:
        """
        Get display label for a dictionary item.

        Args:
            type_code: Dictionary type code
            item_code: Item code
            organization_id: Organization ID
            lang: Language code ('zh' or 'en')

        Returns:
            Display label or the item_code if not found
        """
        item = cls.get_item(type_code, item_code, organization_id)
        if item:
            # Since names are now in English, we use gettext to allow translation
            # dictionary items should have entries in .po files if translation is needed
            from django.utils.translation import gettext
            return gettext(item['name'])
        return item_code

    @classmethod
    def validate_value(cls, type_code: str, value: str, organization_id=None) -> bool:
        """
        Validate if a value exists in the dictionary.

        Args:
            type_code: Dictionary type code
            value: Value to validate
            organization_id: Organization ID

        Returns:
            True if valid, False otherwise
        """
        items = cls.get_items(type_code, organization_id)
        return any(item['code'] == value for item in items)

    @classmethod
    def get_default(cls, type_code: str, organization_id=None) -> Optional[str]:
        """
        Get the default item code for a dictionary type.

        Args:
            type_code: Dictionary type code
            organization_id: Organization ID

        Returns:
            Default item code or None
        """
        items = cls.get_items(type_code, organization_id)
        for item in items:
            if item.get('is_default'):
                return item['code']
        return items[0]['code'] if items else None


class SequenceService(BaseCRUDService):
    """
    Sequence Service - generates unique sequential codes.

    Provides thread-safe sequence generation with:
    - Configurable patterns
    - Automatic period-based reset
    - Database-level locking to prevent duplicates
    """

    def __init__(self):
        from apps.system.models import SequenceRule
        super().__init__(SequenceRule)

    @classmethod
    def get_next_value(cls, rule_code: str, organization_id=None) -> str:
        """
        Get the next value in a sequence.

        Uses database-level locking (select_for_update) to ensure
        thread-safety and prevent duplicate numbers.

        Args:
            rule_code: Sequence rule code (e.g., 'ASSET_CODE')
            organization_id: Organization ID

        Returns:
            Generated sequence string (e.g., 'ZC2026010001')
        """
        from apps.system.models import SequenceRule

        with transaction.atomic():
            # Lock the row for update
            filters = {'code': rule_code, 'is_deleted': False, 'is_active': True}
            if organization_id:
                filters['organization_id'] = organization_id

            rule = SequenceRule.all_objects.select_for_update().filter(**filters).first()

            if not rule:
                raise ValueError(f"Sequence rule '{rule_code}' not found")

            # Check if reset is needed
            today = timezone.now().date()
            should_reset = cls._should_reset(rule, today)

            if should_reset:
                rule.current_value = 0
                rule.last_reset_date = today

            # Increment value
            rule.current_value += 1
            rule.save(update_fields=['current_value', 'last_reset_date', 'updated_at'])

            # Generate the formatted value
            return cls._format_sequence(rule)

    @classmethod
    def _should_reset(cls, rule, today) -> bool:
        """Check if the sequence should be reset based on reset_period."""
        if rule.reset_period == 'never':
            return False

        if not rule.last_reset_date:
            return True

        last_date = rule.last_reset_date

        if rule.reset_period == 'daily':
            return today > last_date
        elif rule.reset_period == 'monthly':
            return today.year > last_date.year or today.month > last_date.month
        elif rule.reset_period == 'yearly':
            return today.year > last_date.year

        return False

    @classmethod
    def _format_sequence(cls, rule) -> str:
        """Format the sequence value according to the pattern."""
        now = timezone.now()
        pattern = rule.pattern

        # Replace pattern variables
        replacements = {
            '{PREFIX}': rule.prefix or '',
            '{YYYY}': now.strftime('%Y'),
            '{YY}': now.strftime('%y'),
            '{MM}': now.strftime('%m'),
            '{DD}': now.strftime('%d'),
            '{SEQ}': str(rule.current_value).zfill(rule.seq_length),
        }

        result = pattern
        for key, value in replacements.items():
            result = result.replace(key, value)

        return result

    @classmethod
    def preview_next(cls, rule_code: str, organization_id=None) -> str:
        """
        Preview what the next sequence value would be (without incrementing).

        Args:
            rule_code: Sequence rule code
            organization_id: Organization ID

        Returns:
            Preview of next sequence string
        """
        from apps.system.models import SequenceRule

        filters = {'code': rule_code, 'is_deleted': False, 'is_active': True}
        if organization_id:
            filters['organization_id'] = organization_id

        rule = SequenceRule.all_objects.filter(**filters).first()

        if not rule:
            raise ValueError(f"Sequence rule '{rule_code}' not found")

        # Temporarily increment for preview
        today = timezone.now().date()
        if cls._should_reset(rule, today):
            preview_value = 1
        else:
            preview_value = rule.current_value + 1

        # Create a temporary copy for formatting
        class TempRule:
            pass

        temp = TempRule()
        temp.prefix = rule.prefix
        temp.pattern = rule.pattern
        temp.seq_length = rule.seq_length
        temp.current_value = preview_value

        return cls._format_sequence(temp)

    # Alias for backwards compatibility
    @classmethod
    def get_next_sequence_value(cls, rule_code: str, organization_id=None) -> str:
        """
        Alias for get_next_value for backwards compatibility.

        Args:
            rule_code: Sequence rule code
            organization_id: Organization ID

        Returns:
            Generated sequence string
        """
        return cls.get_next_value(rule_code, organization_id)


class SystemConfigService(BaseCRUDService):
    """
    System Configuration Service - manages key-value configuration.

    Provides methods for:
    - Getting/setting configuration values
    - Type-safe value retrieval
    - Defaults for missing keys
    """

    def __init__(self):
        from apps.system.models import SystemConfig
        super().__init__(SystemConfig)

    @classmethod
    def get(cls, key: str, default: Any = None, organization_id=None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found
            organization_id: Organization ID

        Returns:
            Typed configuration value or default
        """
        from apps.system.models import SystemConfig

        filters = {'config_key': key, 'is_deleted': False}
        if organization_id:
            filters['organization_id'] = organization_id

        config = SystemConfig.all_objects.filter(**filters).first()

        if config:
            return config.get_typed_value()
        return default

    @classmethod
    def set(cls, key: str, value: Any, organization_id=None, name: str = None,
            value_type: str = 'string', category: str = '', user=None) -> None:
        """
        Set a configuration value.

        Args:
            key: Configuration key
            value: Value to set
            organization_id: Organization ID
            name: Display name (defaults to key)
            value_type: Value type ('string', 'integer', 'float', 'boolean', 'json')
            category: Configuration category
            user: User making the change

        Returns:
            None
        """
        from apps.system.models import SystemConfig
        import json

        # Convert value to string for storage
        if value_type == 'json':
            str_value = json.dumps(value)
        elif value_type == 'boolean':
            str_value = 'true' if value else 'false'
        else:
            str_value = str(value)

        filters = {'config_key': key, 'is_deleted': False}
        if organization_id:
            filters['organization_id'] = organization_id

        config = SystemConfig.all_objects.filter(**filters).first()

        if config:
            config.config_value = str_value
            config.value_type = value_type
            if category:
                config.category = category
            config.save()
        else:
            SystemConfig.objects.create(
                config_key=key,
                config_value=str_value,
                value_type=value_type,
                name=name or key,
                category=category,
                organization_id=organization_id,
                created_by=user,
            )

    @classmethod
    def get_by_category(cls, category: str, organization_id=None) -> Dict[str, Any]:
        """
        Get all configurations in a category.

        Args:
            category: Configuration category
            organization_id: Organization ID

        Returns:
            Dict of key -> typed value
        """
        from apps.system.models import SystemConfig

        filters = {'category': category, 'is_deleted': False}
        if organization_id:
            filters['organization_id'] = organization_id

        configs = SystemConfig.all_objects.filter(**filters)

        return {
            config.config_key: config.get_typed_value()
            for config in configs
        }
