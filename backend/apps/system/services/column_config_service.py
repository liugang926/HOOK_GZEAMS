"""
Column configuration service with priority-based merging.

Priority: User > Role > Organization > Default (PageLayout)

This service provides:
- get_column_config(): Get merged column configuration
- save_user_config(): Save user configuration
- reset_user_config(): Reset to default
"""
from typing import Dict, List, Optional, Any
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from apps.system.models import UserColumnPreference, PageLayout, BusinessObject


class ColumnConfigService:
    """
    Column configuration service with priority-based merging.

    Cache strategy: Results are cached for 1 hour to reduce database queries.
    Cache invalidation: Automatically cleared when user config is saved/reset.
    """

    CACHE_TIMEOUT = 3600  # 1 hour

    @classmethod
    def get_column_config(cls, user, object_code: str) -> Dict[str, Any]:
        """
        Get merged column configuration for a business object.

        Priority: User > Role > Organization > Default (PageLayout)

        Args:
            user: User instance
            object_code: Business object code (e.g., 'asset', 'procurement_request')

        Returns:
            Dict with merged column configuration:
            {
                'columns': [...],      # Merged column definitions
                'columnOrder': [...],   # Column display order
                'source': 'user' | 'default'  # Which config was used
            }
        """
        cache_key = f"column_config:{user.id}:{object_code}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        # 1. Get default config from PageLayout
        default_config = cls._get_default_config(object_code)

        # 2. Get user config
        user_config = cls._get_user_config(user, object_code)

        # 3. Merge configs (user overrides default)
        merged_config = cls._merge_configs(default_config, user_config)

        # Determine source for response
        merged_config['source'] = 'user' if user_config else 'default'

        # Cache result
        cache.set(cache_key, merged_config, cls.CACHE_TIMEOUT)

        return merged_config

    @classmethod
    def _get_default_config(cls, object_code: str) -> Dict[str, Any]:
        """Get default configuration from PageLayout."""
        try:
            # Get business object (use all_objects to include global)
            business_object = BusinessObject.all_objects.get(
                code=object_code,
                is_deleted=False
            )

            # Get default list layout
            layout = PageLayout.objects.filter(
                business_object=business_object,
                layout_type='list',
                is_default=True,
                is_active=True,
                is_deleted=False
            ).first()

            if layout:
                config = layout.layout_config or {}
                # Ensure columns key exists
                if 'columns' not in config:
                    config['columns'] = cls._get_columns_from_field_definitions(business_object)
                return config

            # Fallback to field definitions
            return {
                'columns': cls._get_columns_from_field_definitions(business_object)
            }

        except ObjectDoesNotExist:
            # No business object found, return empty config
            return {'columns': [], 'columnOrder': []}

    @classmethod
    def _get_columns_from_field_definitions(cls, business_object: BusinessObject) -> List[Dict]:
        """Generate column config from FieldDefinition or ModelFieldDefinition."""
        columns = []

        # Try FieldDefinition first (for low-code objects)
        if not business_object.is_hardcoded:
            field_defs = business_object.field_definitions.filter(
                show_in_list=True,
                is_deleted=False
            ).order_by('sort_order')

            for field in field_defs:
                columns.append({
                    'field_code': field.code,
                    'label': field.name,
                    'width': field.column_width,
                    'fixed': field.fixed or None,
                    'sortable': field.sortable,
                    'visible': True
                })
        else:
            # For hardcoded objects, use ModelFieldDefinition
            field_defs = business_object.model_fields.filter(
                show_in_list=True
            ).order_by('sort_order')

            for field in field_defs:
                columns.append({
                    'field_code': field.field_name,
                    'label': field.display_name,
                    'width': None,
                    'fixed': None,
                    'sortable': True,
                    'visible': True
                })

        return columns

    @classmethod
    def _get_user_config(cls, user, object_code: str) -> Dict[str, Any]:
        """Get user configuration."""
        try:
            pref = UserColumnPreference.objects.get(
                user=user,
                object_code=object_code,
                is_default=True
            )
            return pref.column_config
        except ObjectDoesNotExist:
            return {}

    @classmethod
    def _merge_configs(cls, default: Dict, user: Dict) -> Dict[str, Any]:
        """
        Merge configurations with user preference taking priority.

        Merge strategy:
        - User columns override default columns by field_code
        - User columnOrder overrides default
        - Default values used for missing user values
        """
        result = default.copy()

        # Build default column map for quick lookup
        default_columns = {col.get('field_code') or col.get('prop'): col for col in default.get('columns', [])}

        # Build user column map
        user_columns = {col.get('field_code') or col.get('prop'): col for col in user.get('columns', [])}

        # Merge columns: user overrides default for matching field_code
        merged_columns = []
        user_column_order = user.get('columnOrder', [])

        # Use user's order if specified, otherwise use default
        if user_column_order:
            for field_code in user_column_order:
                if field_code in user_columns:
                    merged_columns.append({**default_columns.get(field_code, {}), **user_columns[field_code]})
                elif field_code in default_columns:
                    merged_columns.append(default_columns[field_code])
        else:
            # Use default order, apply user overrides
            for field_code, col in default_columns.items():
                if field_code in user_columns:
                    merged_columns.append({**col, **user_columns[field_code]})
                else:
                    merged_columns.append(col)

        result['columns'] = merged_columns
        result['columnOrder'] = user_column_order or default.get('columnOrder', [])

        return result

    @classmethod
    def save_user_config(cls, user, object_code: str, config: Dict) -> UserColumnPreference:
        """
        Save user column configuration.

        Args:
            user: User instance
            object_code: Business object code
            config: Column configuration to save

        Returns:
            UserColumnPreference instance
        """
        pref, created = UserColumnPreference.objects.get_or_create(
            user=user,
            object_code=object_code,
            config_name='default',
            defaults={'column_config': config, 'organization': user.organization}
        )

        if not created:
            pref.column_config = config
            pref.save()

        # Clear cache
        cache_key = f"column_config:{user.id}:{object_code}"
        cache.delete(cache_key)

        return pref

    @classmethod
    def reset_user_config(cls, user, object_code: str) -> bool:
        """
        Reset user configuration to default.

        Args:
            user: User instance
            object_code: Business object code

        Returns:
            True if successful, False otherwise
        """
        try:
            UserColumnPreference.objects.filter(
                user=user,
                object_code=object_code
            ).delete()

            # Clear cache
            cache_key = f"column_config:{user.id}:{object_code}"
            cache.delete(cache_key)

            return True
        except Exception:
            return False
