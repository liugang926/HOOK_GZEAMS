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
    def _cache_key(cls, user, object_code: str) -> str:
        return f"column_config:{user.id}:{object_code.lower()}"

    @classmethod
    def _resolve_field_code(cls, column: Dict[str, Any]) -> str:
        if not isinstance(column, dict):
            return ''
        return str(
            column.get('field_code')
            or column.get('fieldCode')
            or column.get('prop')
            or ''
        ).strip()

    @classmethod
    def _resolve_column_order(cls, config: Dict[str, Any]) -> List[str]:
        if not isinstance(config, dict):
            return []
        raw_order = config.get('columnOrder')
        if not isinstance(raw_order, list):
            raw_order = config.get('column_order')
        if not isinstance(raw_order, list):
            return []
        return [str(item).strip() for item in raw_order if str(item).strip()]

    @classmethod
    def _normalize_config(cls, config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if not isinstance(config, dict):
            return {'columns': [], 'columnOrder': []}

        normalized_columns: List[Dict[str, Any]] = []
        for column in config.get('columns', []) or []:
            if not isinstance(column, dict):
                continue
            field_code = cls._resolve_field_code(column)
            if not field_code:
                continue
            normalized_columns.append({
                **column,
                'field_code': field_code,
            })

        column_order = cls._resolve_column_order(config)
        if not column_order:
            column_order = [col['field_code'] for col in normalized_columns]

        return {
            **config,
            'columns': normalized_columns,
            'columnOrder': column_order,
        }

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
        cache_key = cls._cache_key(user, object_code)
        cached = cache.get(cache_key)
        if cached:
            return cached

        # 1. Get default config from PageLayout
        default_config = cls._normalize_config(cls._get_default_config(object_code))

        # 2. Get user config
        user_config = cls._normalize_config(cls._get_user_config(user, object_code))

        # 3. Merge configs (user overrides default)
        merged_config = cls._merge_configs(default_config, user_config)

        # Determine source for response
        merged_config['source'] = 'user' if user_config.get('columns') else 'default'

        # Cache result
        cache.set(cache_key, merged_config, cls.CACHE_TIMEOUT)

        return merged_config

    @classmethod
    def _get_default_config(cls, object_code: str) -> Dict[str, Any]:
        """
        Get default list configuration from the shared field model.

        Single-layout policy:
        - List columns should be derived from FieldDefinition/ModelFieldDefinition
          (`show_in_list` + `sort_order`) instead of dedicated list PageLayout rows.
        - Legacy list PageLayout is only a last-resort fallback when no fields exist.
        """
        try:
            # BusinessObject uses GlobalMetadataManager (no org filtering)
            business_object = BusinessObject.objects.get(code=object_code)

            field_columns = cls._get_columns_from_field_definitions(business_object)
            if field_columns:
                return {'columns': field_columns, 'columnOrder': [col['field_code'] for col in field_columns]}

            # Compatibility fallback for legacy data sets with missing field metadata.
            layout = PageLayout.objects.filter(
                business_object=business_object,
                layout_type='list',
                is_default=True,
                is_active=True
            ).first()
            if layout:
                config = layout.layout_config or {}
                if isinstance(config.get('columns'), list):
                    return cls._normalize_config(config)
                return {'columns': [], 'columnOrder': []}

            return {'columns': [], 'columnOrder': []}

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
        pref = (
            UserColumnPreference.all_objects
            .filter(
                user=user,
                object_code__iexact=object_code,
                is_deleted=False,
                is_default=True
            )
            .order_by('-updated_at', '-created_at')
            .first()
        )
        if not pref:
            pref = (
                UserColumnPreference.all_objects
                .filter(
                    user=user,
                    object_code__iexact=object_code,
                    is_deleted=False,
                )
                .order_by('-is_default', '-updated_at', '-created_at')
                .first()
            )
        return cls._normalize_config(pref.column_config if pref else {})

    @classmethod
    def _merge_configs(cls, default: Dict, user: Dict) -> Dict[str, Any]:
        """
        Merge configurations with user preference taking priority.

        Merge strategy:
        - User columns override default columns by field_code
        - User columnOrder overrides default
        - Default values used for missing user values
        """
        default = cls._normalize_config(default)
        user = cls._normalize_config(user)
        result = default.copy()

        # Build default column map for quick lookup
        default_columns = {cls._resolve_field_code(col): col for col in default.get('columns', []) if cls._resolve_field_code(col)}

        # Build user column map
        user_columns = {cls._resolve_field_code(col): col for col in user.get('columns', []) if cls._resolve_field_code(col)}

        # Merge columns: user overrides default for matching field_code
        merged_columns = []
        user_column_order = cls._resolve_column_order(user)
        seen = set()

        # Use user's order if specified, otherwise use default
        if user_column_order:
            for field_code in user_column_order:
                if field_code in user_columns:
                    merged_columns.append({**default_columns.get(field_code, {}), **user_columns[field_code]})
                    seen.add(field_code)
                elif field_code in default_columns:
                    merged_columns.append(default_columns[field_code])
                    seen.add(field_code)
        else:
            # Use default order, apply user overrides
            for field_code, col in default_columns.items():
                if field_code in user_columns:
                    merged_columns.append({**col, **user_columns[field_code]})
                else:
                    merged_columns.append(col)
                seen.add(field_code)

        for field_code, col in default_columns.items():
            if field_code in seen:
                continue
            merged_columns.append({**col, **user_columns.get(field_code, {})})
            seen.add(field_code)

        for field_code, col in user_columns.items():
            if field_code in seen:
                continue
            merged_columns.append(col)
            seen.add(field_code)

        result['columns'] = merged_columns
        result['columnOrder'] = user_column_order or cls._resolve_column_order(default)

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
        # Use all_objects (unscoped manager) to bypass TenantManager's org
        # filtering. The unique_together constraint is (user, object_code,
        # config_name) and does not include organization, so the tenant-scoped
        # manager may miss the existing record and cause IntegrityError.
        normalized_config = cls._normalize_config(config)

        pref, created = UserColumnPreference.all_objects.update_or_create(
            user=user,
            object_code=object_code,
            config_name='default',
            defaults={
                'column_config': normalized_config,
                'organization': getattr(user, 'organization', None),
                'is_deleted': False,
            }
        )

        # Clear cache
        cache_key = cls._cache_key(user, object_code)
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
            UserColumnPreference.all_objects.filter(
                user=user,
                object_code__iexact=object_code,
                is_deleted=False,
            ).delete()

            # Clear cache
            cache_key = cls._cache_key(user, object_code)
            cache.delete(cache_key)

            return True
        except Exception:
            return False
