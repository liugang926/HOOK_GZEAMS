"""
Redis Caching Service for Workflow Statistics.

Provides caching for expensive statistics queries to improve performance.
Includes automatic cache invalidation on workflow state changes.
"""

import json
import logging
from typing import Any, Optional, Dict, List

from django.conf import settings
from django.core.cache import cache, caches

logger = logging.getLogger(__name__)


class RedisService:
    """
    Redis client for workflow caching.
    
    Provides:
    - Statistics caching
    - Workflow state caching
    - Cache invalidation on workflow events
    
    Falls back to Django's cache backend if Redis is not available.
    """
    
    # Cache key prefixes
    PREFIX_WORKFLOW = 'workflow'
    PREFIX_STATS = 'stats'
    PREFIX_TRENDS = 'trends'
    PREFIX_BOTTLENECKS = 'bottlenecks'
    PREFIX_PERFORMANCE = 'performance'
    
    # Default TTL values (in seconds)
    DEFAULT_TTL = 300  # 5 minutes
    STATS_TTL = 300    # 5 minutes
    TRENDS_TTL = 600   # 10 minutes
    BOTTLENECKS_TTL = 600  # 10 minutes
    
    def __init__(self):
        """Initialize Redis service."""
        self.enabled = getattr(settings, 'REDIS_CACHE_ENABLED', True)
        self._redis_client = None
    
    @property
    def redis_client(self):
        """Lazy-load Redis client."""
        if self._redis_client is None:
            try:
                import redis
                self._redis_client = redis.Redis(
                    host=getattr(settings, 'REDIS_HOST', 'localhost'),
                    port=getattr(settings, 'REDIS_PORT', 6379),
                    db=getattr(settings, 'REDIS_DB', 0),
                    password=getattr(settings, 'REDIS_PASSWORD', None),
                    decode_responses=True
                )
                # Test connection
                self._redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis not available, falling back to Django cache: {e}")
                self._redis_client = False  # Mark as unavailable
        
        return self._redis_client if self._redis_client else None
    
    def get_cache_key(
        self,
        prefix: str,
        suffix: str = None,
        organization_id: Optional[str] = None
    ) -> str:
        """
        Generate cache key with namespace.
        
        Args:
            prefix: Cache key prefix (e.g., 'stats')
            suffix: Optional suffix (e.g., 'overview')
            organization_id: Optional organization ID for tenant-aware keys
            
        Returns:
            Fully qualified cache key
        """
        parts = [self.PREFIX_WORKFLOW, prefix]
        if organization_id:
            parts.append(str(organization_id))
        if suffix:
            parts.append(str(suffix))
        return ':'.join(parts)
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        if not self.enabled:
            return None
        
        try:
            if self.redis_client:
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            else:
                # Fallback to Django cache
                return cache.get(key)
        except Exception as e:
            logger.error(f"Cache get failed for key {key}: {e}")
        
        return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (default: 300)
            
        Returns:
            True if successful
        """
        if not self.enabled:
            return False
        
        ttl = ttl or self.DEFAULT_TTL
        
        try:
            if self.redis_client:
                self.redis_client.setex(
                    key,
                    ttl,
                    json.dumps(value)
                )
            else:
                # Fallback to Django cache
                cache.set(key, value, ttl)
            return True
        except Exception as e:
            logger.error(f"Cache set failed for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful
        """
        if not self.enabled:
            return False
        
        try:
            if self.redis_client:
                self.redis_client.delete(key)
            else:
                cache.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete failed for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Key pattern (e.g., 'workflow:stats:*')
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0
        
        count = 0
        
        try:
            if self.redis_client:
                cursor = 0
                while True:
                    cursor, keys = self.redis_client.scan(
                        cursor=cursor,
                        match=pattern,
                        count=100
                    )
                    if keys:
                        count += self.redis_client.delete(*keys)
                    if cursor == 0:
                        break
            else:
                # Django cache doesn't support pattern deletion
                # This is a limitation
                logger.warning("Pattern deletion not supported for Django cache")
        except Exception as e:
            logger.error(f"Cache pattern delete failed for {pattern}: {e}")
        
        return count

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache backend statistics for monitoring and benchmarking.

        Returns:
            Dictionary with cache backend type, availability, key counts, and hit rate
        """
        stats: Dict[str, Any] = {
            'enabled': self.enabled,
            'backend': 'disabled',
            'connected': False,
            'key_count': 0,
            'hits': 0,
            'misses': 0,
            'hit_rate': 0.0,
        }

        if not self.enabled:
            return stats

        try:
            if self.redis_client:
                redis_stats = self.redis_client.info('stats')
                redis_memory = self.redis_client.info('memory')
                redis_keyspace = self.redis_client.info('keyspace')

                hits = int(redis_stats.get('keyspace_hits', 0) or 0)
                misses = int(redis_stats.get('keyspace_misses', 0) or 0)
                total_requests = hits + misses
                key_count = sum(
                    int(database_stats.get('keys', 0) or 0)
                    for database_stats in redis_keyspace.values()
                    if isinstance(database_stats, dict)
                )

                stats.update({
                    'backend': 'redis',
                    'connected': True,
                    'key_count': key_count,
                    'hits': hits,
                    'misses': misses,
                    'hit_rate': round((hits / total_requests * 100), 2) if total_requests else 0.0,
                    'used_memory': redis_memory.get('used_memory_human'),
                    'evicted_keys': int(redis_stats.get('evicted_keys', 0) or 0),
                    'expired_keys': int(redis_stats.get('expired_keys', 0) or 0),
                })
                return stats

            default_cache = caches['default']
            local_cache = getattr(default_cache, '_cache', None)
            local_hits = getattr(default_cache, '_hits', None)
            local_misses = getattr(default_cache, '_misses', None)
            total_requests = (
                (local_hits or 0) + (local_misses or 0)
                if local_hits is not None and local_misses is not None
                else 0
            )

            stats.update({
                'backend': default_cache.__class__.__name__,
                'connected': True,
                'key_count': len(local_cache) if local_cache is not None else 0,
                'hits': int(local_hits or 0),
                'misses': int(local_misses or 0),
                'hit_rate': round((local_hits / total_requests * 100), 2)
                if total_requests and local_hits is not None
                else 0.0,
            })
        except Exception as e:
            logger.error(f"Failed to collect cache stats: {e}")
            stats['error'] = str(e)

        return stats
    
    # ============================================
    # Statistics Caching Methods
    # ============================================
    
    def get_workflow_stats(
        self,
        stats_type: str,
        organization_id: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get cached workflow statistics.
        
        Args:
            stats_type: Type of statistics (overview, trends, bottlenecks, performance)
            organization_id: Optional organization ID for tenant-specific stats
            
        Returns:
            Cached statistics or None
        """
        key = self.get_cache_key(
            self.PREFIX_STATS,
            stats_type,
            organization_id=organization_id
        )
        return self.get(key)
    
    def set_workflow_stats(
        self,
        stats_type: str,
        data: Dict,
        ttl: int = None,
        organization_id: Optional[str] = None
    ) -> bool:
        """
        Cache workflow statistics.
        
        Args:
            stats_type: Type of statistics
            data: Statistics data to cache
            ttl: Time-to-live (default based on type)
            organization_id: Optional organization ID for tenant-specific stats
            
        Returns:
            True if successful
        """
        key = self.get_cache_key(
            self.PREFIX_STATS,
            stats_type,
            organization_id=organization_id
        )
        
        # Use type-specific TTL
        if ttl is None:
            ttl = {
                'overview': self.STATS_TTL,
                'trends': self.TRENDS_TTL,
                'bottlenecks': self.BOTTLENECKS_TTL,
                'performance': self.STATS_TTL
            }.get(stats_type, self.DEFAULT_TTL)
        
        return self.set(key, data, ttl)
    
    def invalidate_workflow_stats(self, organization_id: Optional[str] = None) -> int:
        """
        Invalidate all workflow statistics cache.
        
        Should be called when workflow state changes.

        Args:
            organization_id: Optional organization ID to limit invalidation scope
        
        Returns:
            Number of cache keys deleted
        """
        pattern = self.get_cache_key(
            self.PREFIX_STATS,
            '*',
            organization_id=organization_id
        )
        return self.delete_pattern(pattern)
    
    # ============================================
    # Workflow Instance Caching
    # ============================================
    
    def get_workflow_instance_cache(
        self,
        instance_id: str
    ) -> Optional[Dict]:
        """
        Get cached workflow instance data.
        
        Args:
            instance_id: Workflow instance ID
            
        Returns:
            Cached instance data or None
        """
        key = self.get_cache_key('instance', instance_id)
        return self.get(key)
    
    def set_workflow_instance_cache(
        self,
        instance_id: str,
        data: Dict,
        ttl: int = 60
    ) -> bool:
        """
        Cache workflow instance data.
        
        Args:
            instance_id: Workflow instance ID
            data: Instance data to cache
            ttl: Time-to-live (default: 60 seconds for short-term caching)
            
        Returns:
            True if successful
        """
        key = self.get_cache_key('instance', instance_id)
        return self.set(key, data, ttl)
    
    def invalidate_workflow_instance_cache(self, instance_id: str) -> bool:
        """
        Invalidate workflow instance cache.
        
        Args:
            instance_id: Workflow instance ID
            
        Returns:
            True if successful
        """
        key = self.get_cache_key('instance', instance_id)
        return self.delete(key)
    
    # ============================================
    # User Task Cache
    # ============================================
    
    def get_user_tasks_cache(
        self,
        user_id: str
    ) -> Optional[List]:
        """
        Get cached user tasks.
        
        Args:
            user_id: User ID
            
        Returns:
            Cached task list or None
        """
        key = self.get_cache_key('user_tasks', user_id)
        return self.get(key)
    
    def set_user_tasks_cache(
        self,
        user_id: str,
        tasks: List,
        ttl: int = 120
    ) -> bool:
        """
        Cache user tasks.
        
        Args:
            user_id: User ID
            tasks: List of tasks to cache
            ttl: Time-to-live (default: 2 minutes)
            
        Returns:
            True if successful
        """
        key = self.get_cache_key('user_tasks', user_id)
        return self.set(key, tasks, ttl)
    
    def invalidate_user_tasks_cache(self, user_id: str) -> bool:
        """
        Invalidate user tasks cache.
        
        Args:
            user_id: User ID
            
        Returns:
            True if successful
        """
        key = self.get_cache_key('user_tasks', user_id)
        return self.delete(key)
    
    # ============================================
    # Cache Invalidation on Workflow Events
    # ============================================

    def _normalize_organization_id(self, organization_id: Optional[Any]) -> Optional[str]:
        """Normalize organization IDs before using them in cache keys."""
        if organization_id in (None, ''):
            return None
        return str(organization_id)
    
    def on_workflow_started(self, workflow_instance) -> None:
        """Handle workflow started event - invalidate relevant caches."""
        self.invalidate_workflow_stats(
            self._normalize_organization_id(getattr(workflow_instance, 'organization_id', None))
        )
        if workflow_instance.initiator:
            self.invalidate_user_tasks_cache(str(workflow_instance.initiator.id))
    
    def on_workflow_completed(self, workflow_instance) -> None:
        """Handle workflow completed event - invalidate relevant caches."""
        self.invalidate_workflow_stats(
            self._normalize_organization_id(getattr(workflow_instance, 'organization_id', None))
        )
        self.invalidate_workflow_instance_cache(str(workflow_instance.id))
        if workflow_instance.initiator:
            self.invalidate_user_tasks_cache(str(workflow_instance.initiator.id))
    
    def on_workflow_rejected(self, workflow_instance) -> None:
        """Handle workflow rejected event - invalidate relevant caches."""
        self.invalidate_workflow_stats(
            self._normalize_organization_id(getattr(workflow_instance, 'organization_id', None))
        )
        self.invalidate_workflow_instance_cache(str(workflow_instance.id))
        if workflow_instance.initiator:
            self.invalidate_user_tasks_cache(str(workflow_instance.initiator.id))
    
    def on_workflow_cancelled(self, workflow_instance) -> None:
        """Handle workflow cancelled event - invalidate relevant caches."""
        self.invalidate_workflow_stats(
            self._normalize_organization_id(getattr(workflow_instance, 'organization_id', None))
        )
        self.invalidate_workflow_instance_cache(str(workflow_instance.id))
        if workflow_instance.initiator:
            self.invalidate_user_tasks_cache(str(workflow_instance.initiator.id))
    
    def on_task_assigned(self, task) -> None:
        """Handle task assigned event - invalidate relevant caches."""
        if task.assignee:
            self.invalidate_user_tasks_cache(str(task.assignee.id))
    
    def on_task_completed(self, task) -> None:
        """Handle task completed event - invalidate relevant caches."""
        self.invalidate_workflow_stats(
            self._normalize_organization_id(getattr(task, 'organization_id', None))
        )
        if task.assignee:
            self.invalidate_user_tasks_cache(str(task.assignee.id))


# Singleton instance
redis_service = RedisService()
