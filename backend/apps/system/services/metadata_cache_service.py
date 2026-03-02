"""
Metadata Cache Service - centralized caching for metadata-driven operations.

Provides caching for:
- Field definitions
- Page layouts
- Business rules
- Business object metadata
"""
from typing import Dict, List, Optional, Any
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class MetadataCacheService:
    """
    Centralized caching service for metadata.
    
    Provides efficient caching with:
    - Automatic invalidation on updates
    - Fallback to database when cache misses
    - Configurable TTL
    """

    # Cache TTL in seconds (default 1 hour)
    DEFAULT_TTL = getattr(settings, 'METADATA_CACHE_TTL', 3600)
    
    # Cache key prefixes
    PREFIX_FIELDS = 'fields'
    PREFIX_LAYOUT = 'layout'
    PREFIX_RULES = 'rules'
    PREFIX_META = 'meta'

    @classmethod
    def _cache_key(cls, prefix: str, object_code: str, *args) -> str:
        """Build cache key."""
        key_parts = [prefix, object_code] + list(args)
        return ':'.join(str(p) for p in key_parts)

    # =========================================================================
    # Field Definitions
    # =========================================================================

    @classmethod
    def get_field_definitions(cls, object_code: str, organization_id: str = None) -> Optional[List[Dict]]:
        """
        Get cached field definitions for a business object.
        
        Args:
            object_code: Business object code
            organization_id: Optional organization ID for tenant isolation
        
        Returns:
            List of field definition dicts or None if not cached
        """
        cache_key = cls._cache_key(cls.PREFIX_FIELDS, object_code, organization_id or 'global')
        try:
            return cache.get(cache_key)
        except Exception as e:
            logger.warning(f"Cache get failed for {cache_key}: {e}")
            return None

    @classmethod
    def set_field_definitions(cls, object_code: str, fields: List[Dict], organization_id: str = None):
        """Cache field definitions."""
        cache_key = cls._cache_key(cls.PREFIX_FIELDS, object_code, organization_id or 'global')
        try:
            cache.set(cache_key, fields, cls.DEFAULT_TTL)
        except Exception as e:
            logger.warning(f"Cache set failed for {cache_key}: {e}")

    @classmethod
    def invalidate_field_definitions(cls, object_code: str, organization_id: str = None):
        """Invalidate cached field definitions."""
        cache_key = cls._cache_key(cls.PREFIX_FIELDS, object_code, organization_id or 'global')
        try:
            cache.delete(cache_key)
            # Also invalidate global if org-specific
            if organization_id:
                cache.delete(cls._cache_key(cls.PREFIX_FIELDS, object_code, 'global'))
        except Exception as e:
            logger.warning(f"Cache delete failed for {cache_key}: {e}")

    # =========================================================================
    # Page Layouts
    # =========================================================================

    @classmethod
    def get_page_layout(cls, object_code: str, layout_code: str = None, layout_type: str = None) -> Optional[Dict]:
        """Get cached page layout."""
        cache_key = cls._cache_key(cls.PREFIX_LAYOUT, object_code, layout_code or 'default', layout_type or 'form')
        try:
            return cache.get(cache_key)
        except Exception:
            return None

    @classmethod
    def set_page_layout(cls, object_code: str, layout: Dict, layout_code: str = None, layout_type: str = None):
        """Cache page layout."""
        cache_key = cls._cache_key(cls.PREFIX_LAYOUT, object_code, layout_code or 'default', layout_type or 'form')
        try:
            cache.set(cache_key, layout, cls.DEFAULT_TTL)
        except Exception as e:
            logger.warning(f"Cache set failed for {cache_key}: {e}")

    @classmethod
    def invalidate_page_layout(cls, object_code: str, layout_code: str = None, layout_type: str = None):
        """Invalidate cached page layout."""
        if layout_code:
            cache_key = cls._cache_key(cls.PREFIX_LAYOUT, object_code, layout_code, layout_type or 'form')
            cache.delete(cache_key)
        else:
            # Invalidate all layouts for this object (pattern delete)
            try:
                cache.delete_pattern(f"{cls.PREFIX_LAYOUT}:{object_code}:*")
            except AttributeError:
                # Redis pattern delete not available, skip
                pass

    # =========================================================================
    # Business Rules
    # =========================================================================

    @classmethod
    def get_business_rules(cls, object_code: str, rule_type: str = None) -> Optional[List[Dict]]:
        """Get cached business rules."""
        cache_key = cls._cache_key(cls.PREFIX_RULES, object_code, rule_type or 'all')
        try:
            return cache.get(cache_key)
        except Exception:
            return None

    @classmethod
    def set_business_rules(cls, object_code: str, rules: List[Dict], rule_type: str = None):
        """Cache business rules."""
        cache_key = cls._cache_key(cls.PREFIX_RULES, object_code, rule_type or 'all')
        try:
            cache.set(cache_key, rules, cls.DEFAULT_TTL)
        except Exception as e:
            logger.warning(f"Cache set failed for {cache_key}: {e}")

    @classmethod
    def invalidate_business_rules(cls, object_code: str):
        """Invalidate all cached rules for an object."""
        try:
            cache.delete_pattern(f"{cls.PREFIX_RULES}:{object_code}:*")
        except AttributeError:
            # Fallback: delete known keys
            for rule_type in ['all', 'validation', 'visibility', 'computed', 'linkage', 'trigger']:
                cache.delete(cls._cache_key(cls.PREFIX_RULES, object_code, rule_type))

    # =========================================================================
    # Batch Operations
    # =========================================================================

    @classmethod
    def invalidate_object_cache(cls, object_code: str):
        """Invalidate all caches for a business object."""
        cls.invalidate_field_definitions(object_code)
        cls.invalidate_page_layout(object_code)
        cls.invalidate_business_rules(object_code)

    @classmethod
    def warm_cache(cls, object_code: str, organization=None):
        """
        Pre-warm cache for a business object.
        
        This should be called after metadata updates to ensure
        fast first access.
        """
        from apps.system.models import BusinessObject, FieldDefinition, PageLayout, BusinessRule

        try:
            org_filter = {'organization': organization} if organization else {}
            
            bo = BusinessObject.objects.get(code=object_code, is_deleted=False, **org_filter)
            
            # Cache field definitions
            fields = list(FieldDefinition.objects.filter(
                business_object=bo, is_deleted=False
            ).values(
                'code', 'name', 'field_type', 'is_required', 'is_readonly',
                'is_searchable', 'show_in_list', 'show_in_detail', 'sort_order',
                'options', 'default_value'
            ).order_by('sort_order'))
            cls.set_field_definitions(object_code, fields, str(organization.id) if organization else None)
            
            # Cache default form layout
            try:
                layout = PageLayout.objects.get(
                    business_object=bo, is_default=True, layout_type='form', is_deleted=False
                )
                cls.set_page_layout(object_code, {
                    'layout_code': layout.layout_code,
                    'layout_config': layout.layout_config
                }, 'default', 'form')
            except PageLayout.DoesNotExist:
                pass
            
            # Cache active rules
            rules = list(BusinessRule.objects.filter(
                business_object=bo, is_active=True, is_deleted=False
            ).values(
                'rule_code', 'rule_name', 'rule_type', 'priority',
                'condition', 'action', 'target_field', 'trigger_events'
            ).order_by('-priority'))
            cls.set_business_rules(object_code, rules)
            
            logger.info(f"Cache warmed for {object_code}: {len(fields)} fields, {len(rules)} rules")
            return True
            
        except BusinessObject.DoesNotExist:
            logger.warning(f"Cannot warm cache: BusinessObject {object_code} not found")
            return False
        except Exception as e:
            logger.error(f"Cache warming failed for {object_code}: {e}")
            return False
