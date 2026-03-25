# SLA Dashboard API Documentation

## Overview

The SLA Dashboard API provides comprehensive metrics for Service Level Agreement (SLA) compliance, workflow performance, error summaries, and system health.

## Base URL

```
/api/sla
```

## Authentication

All endpoints require authentication via Bearer token:

```http
Authorization: Bearer <token>
```

---

## Endpoints

### 1. SLA Dashboard Data

Get a complete overview of SLA compliance, performance, and alerts.

**Endpoint**: `GET /api/sla/dashboard`

**Query Parameters**:
- `time_range` (string, optional): Time range (e.g., `24h`, `7d`, `30d`; default: `24h`)
- `include_trends` (boolean, optional): Include historical trends (default: `true`)

**Response**:
```json
{
  "success": true,
  "data": {
    "timestamp": "2026-03-24T14:00:00Z",
    "time_range": "24h",
    "sla_metrics": {
      "workflow_sla": {
        "total_instances": 150,
        "completed_instances": 120,
        "sla_compliant": 110,
        "sla_violations": 10,
        "compliance_rate": 91.67,
        "avg_completion_time_hours": 5.2
      },
      "task_sla": {
        "total_tasks": 300,
        "completed_tasks": 280,
        "overdue_tasks": 20,
        "on_time_rate": 93.33
      }
    },
    "performance_metrics": {
      "api_performance": {
        "total_requests": 1250,
        "avg_response_time_ms": 145.2,
        "max_response_time_ms": 450.0,
        "error_rate": 0.96
      },
      "error_metrics": {
        "total_errors": 45,
        "error_rate_per_hour": 1.875,
        "by_severity": {
          "high": 8,
          "medium": 25,
          "low": 12
        }
      },
      "cache_performance": {
        "enabled": true,
        "hit_rate": 90.91
      }
    },
    "alert_summary": {
      "total_alerts": 5,
      "by_severity": {
        "critical": 1,
        "warning": 4
      },
      "active_critical": 1,
      "active_warnings": 4,
      "last_alert": {"message": "High response time..."}
    },
    "trends": {
      "interval": "hourly",
      "data": [
        {
          "timestamp": "2026-03-24T12:00:00Z",
          "workflow_count": 5,
          "task_count": 10,
          "overdue_count": 1
        }
      ]
    },
    "top_issues": [
      {
        "type": "sla_violation",
        "count": 10,
        "severity": "high",
        "examples": [
          {"instance_id": "uuid1", "duration_hours": 28, "definition": "Purchase Approval"}
        ]
      }
    ],
    "health_score": {
      "score": 85,
      "status": "healthy",
      "factors": []
    }
  }
}
```

### 2. SLA Alert Configuration

Get or update alert thresholds and notification settings for SLA metrics.

**Endpoint**: `GET /api/sla/alerts/config`
**Endpoint**: `POST /api/sla/alerts/config`

**GET Response**:
```json
{
  "success": true,
  "data": {
    "alert_rules": {
      "sla_compliance": {
        "name": "SLA Compliance Monitoring",
        "metrics": {
          "sla_compliance_rate": {
            "warning_threshold": 90,
            "critical_threshold": 80
          }
        }
      }
    }
  }
}
```

**POST Request Body**:
```json
{
  "alert_rules": {
    "sla_compliance": {
      "metrics": {
        "sla_compliance_rate": {
          "warning_threshold": 85,
          "critical_threshold": 75
        }
      }
    }
  }
}
```

### 3. SLA Historical Trends

Get historical trends for SLA compliance over longer periods.

**Endpoint**: `GET /api/sla/trends`

**Query Parameters**:
- `days` (integer, optional): Number of days to look back (default: 7)
- `interval` (string, optional): Time interval (`hourly` or `daily`; default: `daily`)

**Response**:
```json
{
  "success": true,
  "data": {
    "interval": "daily",
    "period_days": 7,
    "trends": [
      {
        "timestamp": "2026-03-18T00:00:00Z",
        "total_workflows": 50,
        "compliant_workflows": 45,
        "compliance_rate": 90.0
      }
    ]
  }
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| `VALIDATION_ERROR` | Invalid query parameters or request body |
| `UNAUTHORIZED` | Missing or invalid authentication |
| `PERMISSION_DENIED` | Insufficient permissions |
| `SERVICE_UNAVAILABLE` | SLA Dashboard service unavailable |

---

## Best Practices

### 1. Dashboard Usage
- Monitor the `health_score` for an immediate system overview.
- Drill down into `top_issues` to identify and address bottlenecks.
- Use `trends` to identify long-term degradation or improvement.

### 2. Alert Configuration
- Set `critical_threshold` for immediate action alerts.
- Set `warning_threshold` for proactive monitoring.
- Customize notification channels based on team preferences.

### 3. Compliance Reporting
- Generate monthly or quarterly `SLA Historical Trends` reports for stakeholders.
- Track `avg_completion_time_hours` for process efficiency improvements.

---

## Examples

### Python

```python
import requests

headers = {'Authorization': f'Bearer {token}'}

# Get SLA dashboard data for last 7 days
response = requests.get(
    'https://api.example.com/api/sla/dashboard?time_range=7d',
    headers=headers
)
data = response.json()

if data['success']:
    print(f"Overall health score: {data['data']['health_score']['score']}")
    print(f"SLA compliance rate: {data['data']['sla_metrics']['workflow_sla']['compliance_rate']}%")
```

### JavaScript

```javascript
const headers = {'Authorization': `Bearer ${token}`};

// Get SLA trends for last 30 days, daily interval
fetch('/api/sla/trends?days=30&interval=daily', {headers})
  .then(response => response.json())
  .then(data => {
    if (data.success) {
      console.log('SLA trends:', data.data.trends);
    }
  });
```

---

## See Also

- [Monitoring API Documentation](/docs/api/monitoring-api.md)
- [Alert Rules Configuration](/docs/configuration/alert-rules.md)
- [Performance Baselines](/docs/reports/performance-baseline.md)