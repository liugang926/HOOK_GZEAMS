"""
Permission cache management.

Provides Redis/Django cache support for:
- User permissions
- User roles
- Field permissions
"""
from typing import Optional, Set, List, Dict, Any
from django.core.cache import cache
import json


class PermissionCache:
    """
    Cache manager for permission data.

    Caches:
    - User permissions (Set[str])
    - User roles (List[Dict])
    - Field permissions (Dict[str, Dict[str, bool]])
    """

    CACHE_PREFIX = 'gzeams:permission'
    CACHE_TIMEOUT = 3600  # 1 hour

    @classmethod
    def _make_key(cls, *parts: str) -> str:
        """Generate cache key from parts."""
        return f'{cls.CACHE_PREFIX}:{":".join(str(p) for p in parts)}'

    # User permissions cache
    @classmethod
    def get_user_permissions(cls, user_id: str) -> Optional[Set[str]]:
        """
        Get cached user permissions.

        Args:
            user_id: User ID

        Returns:
            Set of permission codes or None if not cached
        """
        key = cls._make_key('user_perms', user_id)
        data = cache.get(key)
        if data is not None:
            return set(data)
        return None

    @classmethod
    def set_user_permissions(cls, user_id: str, permissions: Set[str]) -> None:
        """
        Cache user permissions.

        Args:
            user_id: User ID
            permissions: Set of permission codes
        """
        key = cls._make_key('user_perms', user_id)
        cache.set(key, list(permissions), cls.CACHE_TIMEOUT)

    @classmethod
    def invalidate_user(cls, user_id: str) -> None:
        """
        Clear user permission cache.

        Args:
            user_id: User ID
        """
        cache.delete(cls._make_key('user_perms', user_id))

    # User roles cache
    @classmethod
    def get_user_roles(cls, user_id: str) -> Optional[List[Dict]]:
        """
        Get cached user roles.

        Args:
            user_id: User ID

        Returns:
            List of role dicts or None if not cached
        """
        key = cls._make_key('user_roles', user_id)
        return cache.get(key)

    @classmethod
    def set_user_roles(cls, user_id: str, roles: List[Dict]) -> None:
        """
        Cache user roles.

        Args:
            user_id: User ID
            roles: List of role dicts
        """
        key = cls._make_key('user_roles', user_id)
        cache.set(key, roles, cls.CACHE_TIMEOUT)

    @classmethod
    def invalidate_user_roles(cls, user_id: str) -> None:
        """
        Clear user roles cache.

        Args:
            user_id: User ID
        """
        cache.delete(cls._make_key('user_roles', user_id))

    # Field permissions cache
    @classmethod
    def get_field_permissions(
        cls,
        business_object_code: str,
        role_codes: List[str]
    ) -> Optional[Dict[str, Dict[str, bool]]]:
        """
        Get cached field permissions.

        Args:
            business_object_code: Business object code
            role_codes: List of role codes

        Returns:
            Field permissions dict or None if not cached
        """
        role_key = ':'.join(sorted(role_codes))
        key = cls._make_key('field_perms', business_object_code, role_key)
        return cache.get(key)

    @classmethod
    def set_field_permissions(
        cls,
        business_object_code: str,
        role_codes: List[str],
        permissions: Dict[str, Dict[str, bool]]
    ) -> None:
        """
        Cache field permissions.

        Args:
            business_object_code: Business object code
            role_codes: List of role codes
            permissions: Field permissions dict
        """
        role_key = ':'.join(sorted(role_codes))
        key = cls._make_key('field_perms', business_object_code, role_key)
        cache.set(key, permissions, cls.CACHE_TIMEOUT)

    @classmethod
    def invalidate_field_permissions(
        cls,
        business_object_code: Optional[str] = None
    ) -> None:
        """
        Clear field permissions cache.

        Args:
            business_object_code: Optional business object code.
                                  If None, clears all field permissions.
        """
        try:
            from django_redis import get_redis_connection
            conn = get_redis_connection('default')
            pattern = cls._make_key('field_perms', business_object_code or '*', '*')
            keys = conn.keys(pattern)
            if keys:
                conn.delete(*keys)
        except (ImportError, Exception):
            # For non-Redis backends, we can only clear specific keys
            pass

    @classmethod
    def invalidate_all(cls, user_id: Optional[str] = None) -> None:
        """
        Clear all permission caches.

        Args:
            user_id: Optional user ID. If provided, only clears that user's cache.
        """
        if user_id:
            cls.invalidate_user(user_id)
            cls.invalidate_user_roles(user_id)
        else:
            # Try to clear all permission caches
            try:
                from django_redis import get_redis_connection
                conn = get_redis_connection('default')
                pattern = f'{cls.CACHE_PREFIX}:*'
                keys = conn.keys(pattern)
                if keys:
                    conn.delete(*keys)
            except (ImportError, Exception):
                pass
