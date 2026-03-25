# Monitoring API Documentation

## Overview

The monitoring API provides real-time performance metrics, error tracking, and system health information.

## Base URL

```
/api/monitoring
```

## Authentication

All endpoints require authentication via Bearer token:

```http
Authorization: Bearer <token>
```

---

## Endpoints

### 1. Performance Metrics

Get API performance statistics including response times, error rates, and throughput.

**Endpoint**: `GET /api/monitoring/performance`

**Query Parameters**:
- `hours` (integer, optional): Time range in hours (default: 1)

**Response**:
```json
{
  "success": true,
  "data": {
    "time_period_hours": 1,
    "total_requests": 1250,
    "error_count": 12,
    "error_rate": 0.96,
    "avg_response_time_ms": 145.2,
    "max_response_time_ms": 450.0,
    "min_response_time_ms": 45.0,
    "endpoint_stats": {
      "/api/workflows/definitions/": {
        "requests": 500,
        "avg_time": 120.5,
        "error_rate": 0.4
      }
    }
  }
}
```

### 2. System Metrics

Get system resource usage including CPU, memory, and disk.

**Endpoint**: `GET /api/monitoring/system`

**Response**:
```json
{
  "success": true,
  "data": {
    "cpu_usage": 45.2,
    "memory_usage": {
      "total": 17179869184,
      "available": 8589934592,
      "percent": 50.0
    },
    "disk_usage": {
      "total": 107374182400,
      "used": 53687091200,
      "percent": 50.0
    },
    "timestamp": "2026-03-24T13:00:00Z"
  }
}
```

### 3. Error Statistics

Get error statistics grouped by category, severity, and component.

**Endpoint**: `GET /api/monitoring/errors`

**Query Parameters**:
- `hours` (integer, optional): Time range in hours (default: 24)

**Response**:
```json
{
  "success": true,
  "data": {
    "time_period_hours": 24,
    "total_errors": 45,
    "by_category": {
      "validation_error": 15,
      "database_error": 5,
      "network_error": 10
    },
    "by_severity": {
      "high": 8,
      "medium": 25,
      "low": 12
    },
    "by_component": {
      "workflow_engine": 20,
      "api_layer": 15,
      "statistics_service": 10
    },
    "error_rate_per_hour": 1.875,
    "top_errors": [
      {
        "message": "Validation failed",
        "count": 15
      }
    ]
  }
}
```

### 4. Error Trends

Get error trends over time with configurable intervals.

**Endpoint**: `GET /api/monitoring/errors/trends`

**Query Parameters**:
- `hours` (integer, optional): Time range in hours (default: 24)
- `interval_minutes` (integer, optional): Bucket size in minutes (default: 60)

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "timestamp": "2026-03-24T12:00:00Z",
      "total_errors": 3,
      "by_category": {
        "validation_error": 2,
        "database_error": 1
      },
      "max_severity": "high"
    }
  ]
}
```

### 5. Cache Statistics

Get cache performance metrics including hit rate and memory usage.

**Endpoint**: `GET /api/monitoring/cache`

**Response**:
```json
{
  "success": true,
  "data": {
    "enabled": true,
    "backend": "redis",
    "connected": true,
    "key_count": 1250,
    "hits": 50000,
    "misses": 5000,
    "hit_rate": 90.91,
    "used_memory": "256M",
    "evicted_keys": 10,
    "expired_keys": 50
  }
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Invalid query parameters |
| `UNAUTHORIZED` | Missing or invalid authentication |
| `PERMISSION_DENIED` | Insufficient permissions |
| `SERVICE_UNAVAILABLE` | Monitoring service unavailable |

---

## Rate Limiting

- **Default**: 100 requests/minute per IP
- **Authenticated**: 200 requests/minute per user
- **Headers included**:
  - `X-RateLimit-Limit`: Request limit
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset timestamp

---

## Best Practices

### 1. Time Range Selection
- Use `hours=1` for real-time monitoring
- Use `hours=24` for daily reports
- Use `hours=168` (7 days) for weekly analysis

### 2. Error Monitoring
- Monitor `error_rate` threshold (target: < 2%)
- Track `by_severity` distribution
- Investigate repeated `top_errors`

### 3. Performance Optimization
- Aim for `avg_response_time_ms` < 250ms
- Keep `max_response_time_ms` < 500ms
- Monitor `endpoint_stats` for optimization opportunities

### 4. Cache Management
- Target `hit_rate` > 90%
- Monitor `evicted_keys` for capacity planning
- Track `used_memory` for scaling decisions

---

## Examples

### Python

```python
import requests

headers = {'Authorization': f'Bearer {token}'}

# Get performance metrics
response = requests.get(
    'https://api.example.com/api/monitoring/performance?hours=1',
    headers=headers
)
data = response.json()

if data['success']:
    print(f"Average response time: {data['data']['avg_response_time_ms']}ms")
    print(f"Error rate: {data['data']['error_rate']}%")
```

### JavaScript

```javascript
const headers = {'Authorization': `Bearer ${token}`};

// Get error statistics
fetch('https://api.example.com/api/monitoring/errors?hours=24', {headers})
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      console.log(`Total errors: ${data.data.total_errors}`);
      console.log('By category:', data.data.by_category);
    }
  });
```

---

## See Also

- [SLA Dashboard API](/docs/api/sla-dashboard-api.md)
- [Alert Configuration](/docs/configuration/alert-rules.md)
- [Performance Baselines](/docs/reports/performance-baseline.md)