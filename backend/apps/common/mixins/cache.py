"""
Cache mixin for ViewSets and Services.

Provides:
- Unified caching abstraction
- Redis/Memory cache support
- Automatic cache key generation
- Cache invalidation patterns
- View caching decorator
"""
from typing import Any, Optional, List
from functools import wraps
from django.core.cache import cache
from django.conf import settings
import hashlib
import json


class BaseCacheMixin:
    """
    Base mixin providing caching capabilities.

    Attributes:
        cache_timeout: Cache timeout in seconds (default: 300)
        cache_key_prefix: Prefix for cache keys (default: '')
        cache_enabled: Whether caching is enabled (default: True)

    Usage:
        class MyViewSet(BaseCacheMixin, viewsets.ModelViewSet):
            cache_timeout = 600
            cache_key_prefix = 'assets'

            def list(self, request):
                cache_key = self.get_cache_key('list', request.query_params)
                result = self.cache_get(cache_key)
                if result is None:
                    result = super().list(request).data
                    self.cache_set(cache_key, result)
                return Response(result)
    """

    cache_timeout: int = 300  # 5 minutes
    cache_key_prefix: str = ''
    cache_enabled: bool = True

    def get_cache_key(self, *args, **kwargs) -> str:
        """
        Generate a cache key from arguments.

        Args:
            *args: Positional arguments to include in key
            **kwargs: Keyword arguments to include in key

        Returns:
            str: Cache key in format 'cache:{prefix}:{hash}'
        """
        # Build key components
        components = [str(arg) for arg in args]
        if kwargs:
            components.append(json.dumps(kwargs, sort_keys=True, default=str))

        # Create hash of components
        key_data = ':'.join(components)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:12]

        # Build final key
        prefix = self.cache_key_prefix or self.__class__.__name__.lower()
        return f'cache:{prefix}:{key_hash}'

    def cache_get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.cache_enabled:
            return None
        return cache.get(key)

    def cache_set(self, key: str, value: Any, timeout: Optional[int] = None) -> None:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            timeout: Optional timeout override
        """
        if not self.cache_enabled:
            return
        cache.set(key, value, timeout or self.cache_timeout)

    def cache_delete(self, key: str) -> None:
        """
        Delete a specific cache key.

        Args:
            key: Cache key to delete
        """
        cache.delete(key)

    def cache_delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.

        Args:
            pattern: Pattern to match (e.g., 'cache:assets:*')

        Returns:
            Number of keys deleted

        Note:
            Only works with Redis cache backend.
        """
        try:
            # Try to use Redis pattern delete
            from django_redis import get_redis_connection
            conn = get_redis_connection('default')
            keys = conn.keys(pattern)
            if keys:
                conn.delete(*keys)
            return len(keys)
        except (ImportError, Exception):
            # Fallback for non-Redis backends
            return 0

    def cache_clear(self) -> None:
        """Clear all cache entries for this prefix."""
        pattern = f'cache:{self.cache_key_prefix or self.__class__.__name__.lower()}:*'
        self.cache_delete_pattern(pattern)


class CachedQuerySetMixin(BaseCacheMixin):
    """
    Mixin for caching QuerySet results in list views.

    Usage:
        class AssetViewSet(CachedQuerySetMixin, BaseModelViewSet):
            cache_timeout = 600

            def get_cache_key(self):
                return super().get_cache_key('list', self.request.query_params)
    """

    def list(self, request, *args, **kwargs):
        """Cache list results."""
        cache_key = self.get_cache_key('list', request.query_params)
        result = self.cache_get(cache_key)

        if result is None:
            response = super().list(request, *args, **kwargs)
            self.cache_set(cache_key, response.data)
            return response

        from rest_framework.response import Response
        return Response(result)


class CachedObjectMixin(BaseCacheMixin):
    """
    Mixin for caching single object results in detail views.
    """

    def retrieve(self, request, *args, **kwargs):
        """Cache retrieve results."""
        pk = kwargs.get('pk') or kwargs.get('id')
        cache_key = self.get_cache_key('retrieve', pk)
        result = self.cache_get(cache_key)

        if result is None:
            response = super().retrieve(request, *args, **kwargs)
            self.cache_set(cache_key, response.data)
            return response

        from rest_framework.response import Response
        return Response(result)

    def perform_update(self, serializer):
        """Invalidate cache on update."""
        super().perform_update(serializer)
        pk = serializer.instance.pk
        self.cache_delete(self.get_cache_key('retrieve', pk))

    def perform_destroy(self, instance):
        """Invalidate cache on delete."""
        pk = instance.pk
        super().perform_destroy(instance)
        self.cache_delete(self.get_cache_key('retrieve', pk))


def cache_view(timeout: int = 300, key_prefix: str = ''):
    """
    Decorator to cache view results.

    Args:
        timeout: Cache timeout in seconds
        key_prefix: Prefix for cache key

    Usage:
        @cache_view(timeout=600, key_prefix='asset_list')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Build cache key
            key_parts = [
                key_prefix or view_func.__name__,
                request.path,
                str(request.query_params) if hasattr(request, 'query_params') else '',
            ]
            key_data = ':'.join(key_parts)
            key_hash = hashlib.md5(key_data.encode()).hexdigest()[:12]
            cache_key = f'view:{key_prefix or view_func.__name__}:{key_hash}'

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                from rest_framework.response import Response
                return Response(result)

            # Execute view and cache result
            response = view_func(request, *args, **kwargs)
            if hasattr(response, 'data'):
                cache.set(cache_key, response.data, timeout)

            return response
        return wrapper
    return decorator


def cached_property_with_ttl(ttl: int = 300):
    """
    Decorator for cached properties with TTL.

    Args:
        ttl: Time to live in seconds

    Usage:
        class MyService:
            @cached_property_with_ttl(ttl=600)
            def expensive_computation(self):
                return compute_something()
    """
    def decorator(method):
        cache_key_attr = f'_cache_{method.__name__}'
        cache_time_attr = f'_cache_time_{method.__name__}'

        @property
        @wraps(method)
        def wrapper(self):
            import time

            # Check if cached and not expired
            cached_value = getattr(self, cache_key_attr, None)
            cached_time = getattr(self, cache_time_attr, 0)

            if cached_value is not None and (time.time() - cached_time) < ttl:
                return cached_value

            # Compute and cache
            value = method(self)
            setattr(self, cache_key_attr, value)
            setattr(self, cache_time_attr, time.time())
            return value

        return wrapper
    return decorator
