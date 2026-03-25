"""
Rate Limiting Middleware.

Protects API endpoints from abuse and DDoS attacks.
Implements sliding window rate limiting with configurable limits.
"""

import time
import logging
from typing import Dict, Any, Optional
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings
from rest_framework import status

logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """
    Rate limiting middleware using sliding window algorithm.
    
    Features:
    - Per-IP rate limiting
    - Per-user rate limiting
    - Per-endpoint rate limiting
    - Configurable time windows
    - Automatic cleanup
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Rate limit configuration
        self.default_limits = {
            'global': {
                'requests': 1000,
                'window': 60  # 1000 requests per minute
            },
            'per_ip': {
                'requests': 100,
                'window': 60  # 100 requests per minute per IP
            },
            'per_user': {
                'requests': 200,
                'window': 60  # 200 requests per minute per user
            },
            'strict_endpoints': {
                'requests': 10,
                'window': 60  # 10 requests per minute for strict endpoints
            }
        }
        
        # Endpoints with strict rate limiting
        self.strict_endpoints = [
            '/api/workflows/submit/',
            '/api/workflows/approve/',
            '/api/workflows/reject/',
            '/api/auth/login/',
            '/api/auth/logout/'
        ]
        
        # Skip rate limiting for these endpoints
        self.excluded_paths = [
            '/api/health/',
            '/api/metrics/',
            '/static/',
            '/media/'
        ]
    
    def __call__(self, request):
        """Process request and apply rate limiting."""
        
        # Skip excluded paths
        if self._should_skip(request.path):
            return self.get_response(request)
        
        # Get client identifier
        client_id = self._get_client_id(request)
        
        # Check rate limits
        limit_result = self._check_rate_limit(
            client_id,
            request.path,
            request.method
        )
        
        if not limit_result['allowed']:
            # Log rate limit violation
            logger.warning(
                f"Rate limit exceeded: {client_id} - "
                f"{request.method} {request.path}"
            )
            
            # Return 429 Too Many Requests
            response = JsonResponse({
                'success': False,
                'error': 'Rate limit exceeded',
                'retry_after': limit_result['retry_after']
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Add rate limit headers
            response['Retry-After'] = str(limit_result['retry_after'])
            response['X-RateLimit-Limit'] = str(limit_result['limit'])
            response['X-RateLimit-Remaining'] = '0'
            response['X-RateLimit-Reset'] = str(limit_result['reset_time'])
            
            return response
        
        # Add rate limit headers to successful response
        response = self.get_response(request)
        
        if hasattr(response, '__setitem__'):
            response['X-RateLimit-Limit'] = str(limit_result['limit'])
            response['X-RateLimit-Remaining'] = str(limit_result['remaining'])
            response['X-RateLimit-Reset'] = str(limit_result['reset_time'])
        
        return response
    
    def _should_skip(self, path: str) -> bool:
        """Check if path should be excluded from rate limiting."""
        return any(path.startswith(excluded) for excluded in self.excluded_paths)
    
    def _get_client_id(self, request) -> str:
        """
        Get client identifier for rate limiting.
        
        Priority:
        1. Authenticated user ID
        2. API key
        3. IP address
        """
        # Try authenticated user
        if hasattr(request, 'user') and request.user.is_authenticated:
            return f"user:{request.user.id}"
        
        # Try API key
        api_key = request.headers.get('X-API-Key') or request.GET.get('api_key')
        if api_key:
            return f"apikey:{api_key}"
        
        # Fall back to IP address
        ip = self._get_client_ip(request)
        return f"ip:{ip}"
    
    def _get_client_ip(self, request) -> str:
        """Get client IP address from request."""
        # Check for forwarded IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        
        # Check for real IP
        x_real_ip = request.META.get('HTTP_X_REAL_IP')
        if x_real_ip:
            return x_real_ip
        
        # Fall back to remote address
        return request.META.get('REMOTE_ADDR', 'unknown')
    
    def _check_rate_limit(self, client_id: str, path: str, method: str) -> Dict[str, Any]:
        """
        Check if request is within rate limits.
        
        Uses sliding window algorithm for accurate rate limiting.
        
        Returns:
            Dictionary with rate limit status
        """
        # Determine which limit to apply
        if any(path.startswith(endpoint) for endpoint in self.strict_endpoints):
            limit_config = self.default_limits['strict_endpoints']
        elif client_id.startswith('user:'):
            limit_config = self.default_limits['per_user']
        elif client_id.startswith('ip:'):
            limit_config = self.default_limits['per_ip']
        else:
            limit_config = self.default_limits['global']
        
        max_requests = limit_config['requests']
        window_size = limit_config['window']
        
        # Cache key for this client
        cache_key = f"rate_limit:{client_id}:{path}:{method}"
        
        # Get current window data
        now = time.time()
        window_start = now - window_size
        
        window_data = cache.get(cache_key, {'requests': [], 'count': 0})
        
        # Clean up old requests outside the window
        window_data['requests'] = [
            req_time for req_time in window_data['requests']
            if req_time > window_start
        ]
        
        # Check if limit exceeded
        current_count = len(window_data['requests'])
        
        if current_count >= max_requests:
            # Find oldest request to calculate retry_after
            oldest_request = min(window_data['requests']) if window_data['requests'] else now
            retry_after = int(oldest_request + window_size - now) + 1
            reset_time = int(oldest_request + window_size)
            
            return {
                'allowed': False,
                'limit': max_requests,
                'remaining': 0,
                'retry_after': retry_after,
                'reset_time': reset_time
            }
        
        # Add current request to window
        window_data['requests'].append(now)
        window_data['count'] = len(window_data['requests'])
        
        # Store updated window data
        cache.set(cache_key, window_data, window_size)
        
        # Calculate reset time
        oldest_request = min(window_data['requests']) if window_data['requests'] else now
        reset_time = int(oldest_request + window_size)
        
        return {
            'allowed': True,
            'limit': max_requests,
            'remaining': max_requests - current_count - 1,
            'retry_after': 0,
            'reset_time': reset_time
        }


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    pass


def check_rate_limit(client_id: str, endpoint: str, 
                    requests: int = 100, window: int = 60) -> Dict[str, Any]:
    """
    Check rate limit for a specific client and endpoint.
    
    Args:
        client_id: Unique client identifier
        endpoint: Endpoint path
        requests: Maximum requests allowed
        window: Time window in seconds
        
    Returns:
        Dictionary with rate limit status
    """
    cache_key = f"rate_limit:{client_id}:{endpoint}"
    now = time.time()
    window_start = now - window
    
    window_data = cache.get(cache_key, {'requests': [], 'count': 0})
    
    # Clean up old requests
    window_data['requests'] = [
        req_time for req_time in window_data['requests']
        if req_time > window_start
    ]
    
    current_count = len(window_data['requests'])
    
    if current_count >= requests:
        oldest_request = min(window_data['requests']) if window_data['requests'] else now
        retry_after = int(oldest_request + window - now) + 1
        
        return {
            'allowed': False,
            'limit': requests,
            'remaining': 0,
            'retry_after': retry_after
        }
    
    # Add current request
    window_data['requests'].append(now)
    cache.set(cache_key, window_data, window)
    
    return {
        'allowed': True,
        'limit': requests,
        'remaining': requests - current_count - 1,
        'retry_after': 0
    }


def reset_rate_limit(client_id: str, endpoint: str) -> None:
    """Reset rate limit for a specific client and endpoint."""
    cache_key = f"rate_limit:{client_id}:{endpoint}"
    cache.delete(cache_key)


def get_rate_limit_stats(client_id: str = None) -> Dict[str, Any]:
    """
    Get rate limit statistics.
    
    Args:
        client_id: Specific client to get stats for (optional)
        
    Returns:
        Rate limit statistics
    """
    # Get all rate limit keys
    all_keys = cache.keys('rate_limit:*')
    
    if client_id:
        all_keys = [key for key in all_keys if f':{client_id}:' in key]
    
    stats = {
        'total_clients': len(set(key.split(':')[1] for key in all_keys)),
        'total_endpoints': len(all_keys),
        'active_clients': 0,
        'top_clients': []
    }
    
    # Get top clients by request count
    client_counts = {}
    for key in all_keys:
        try:
            data = cache.get(key, {})
            client = key.split(':')[1]
            if data.get('count', 0) > 0:
                client_counts[client] = client_counts.get(client, 0) + data['count']
        except Exception:
            continue
    
    stats['active_clients'] = len(client_counts)
    stats['top_clients'] = sorted(
        client_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
    
    return stats