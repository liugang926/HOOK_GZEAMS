# GZEAMS Backend API Documentation

## Base Information

### Base URL
```
Production: https://api.gzeams.com/api/
Development: http://localhost:8000/api/
```

### Authentication
All API requests (except login) require authentication via JWT token:

```http
Authorization: Bearer <access_token>
```

#### Obtain Token
```http
POST /api/auth/login/
Content-Type: application/json

{
    "username": "user@example.com",
    "password": "your_password"
}
```

Response:
```json
{
    "success": true,
    "data": {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "user": {...}
    }
}
```

### Response Format

#### Success Response
```json
{
    "success": true,
    "message": "Operation successful",
    "data": {
        "id": "uuid",
        "field": "value"
    }
}
```

#### Paginated List Response
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": "http://api.example.com/api/resource/?page=2",
        "previous": null,
        "results": [...]
    }
}
```

#### Error Response
```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable error message",
        "details": {
            "field": ["Detailed error information"]
        }
    }
}
```

### Standard Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Request data validation failed |
| `UNAUTHORIZED` | 401 | Authentication required |
| `PERMISSION_DENIED` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `METHOD_NOT_ALLOWED` | 405 | Method not allowed |
| `CONFLICT` | 409 | Resource conflict |
| `ORGANIZATION_MISMATCH` | 403 | Organization mismatch |
| `SOFT_DELETED` | 410 | Resource has been deleted |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded |
| `SERVER_ERROR` | 500 | Internal server error |

### Standard CRUD Operations

All ModelViewSets provide:

#### List Resources
```http
GET /api/{resource}/
```

Query Parameters:
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20)
- `search`: Search query
- `ordering`: Ordering field (e.g., `-created_at`)
- Filters: Field-specific filters (e.g., `status=active`)

#### Retrieve Single Resource
```http
GET /api/{resource}/{id}/
```

#### Create Resource
```http
POST /api/{resource}/
Content-Type: application/json

{
    "field": "value",
    ...
}
```

#### Update Resource
```http
PUT /api/{resource}/{id}/
Content-Type: application/json

{
    "field": "new_value",
    ...
}
```

#### Partial Update
```http
PATCH /api/{resource}/{id}/
Content-Type: application/json

{
    "field": "new_value"
}
```

#### Delete Resource (Soft Delete)
```http
DELETE /api/{resource}/{id}/
```

### Extended Operations

#### List Deleted Records
```http
GET /api/{resource}/deleted/
```

#### Restore Deleted Record
```http
POST /api/{resource}/{id}/restore/
```

#### Batch Operations
```http
# Batch Soft Delete
POST /api/{resource}/batch-delete/
{
    "ids": ["uuid1", "uuid2", "uuid3"]
}

# Batch Restore
POST /api/{resource}/batch-restore/
{
    "ids": ["uuid1", "uuid2", "uuid3"]
}

# Batch Update
POST /api/{resource}/batch-update/
{
    "ids": ["uuid1", "uuid2"],
    "data": {"status": "active"}
}
```

## API Endpoints

### Assets Module

#### Asset Management

##### List Assets
```http
GET /api/assets/
```

Query Parameters:
- `asset_code`: Filter by asset code
- `asset_name`: Filter by asset name
- `asset_status`: Filter by status (idle, in_use, maintenance, etc.)
- `asset_category_id`: Filter by category
- `department_id`: Filter by department
- `location_id`: Filter by location
- `supplier_id`: Filter by supplier

##### Create Asset
```http
POST /api/assets/
Content-Type: application/json

{
    "asset_code": "AST001",
    "asset_name": "Laptop Computer",
    "specification": "Dell XPS 15",
    "brand": "Dell",
    "model": "XPS 15",
    "serial_number": "SN123456",
    "asset_category_id": "uuid",
    "original_value": 1500.00,
    "useful_life": 60
}
```

##### Asset Statistics
```http
GET /api/assets/statistics/
```

Response:
```json
{
    "success": true,
    "data": {
        "total": 100,
        "by_status": {
            "idle": 30,
            "in_use": 50,
            "maintenance": 10,
            "lost": 5,
            "scrapped": 5
        },
        "total_value": 150000.00,
        "total_net_value": 120000.00,
        "by_category": {...}
    }
}
```

##### Change Asset Status
```http
POST /api/assets/{id}/change-status/
Content-Type: application/json

{
    "new_status": "in_use",
    "reason": "Asset assigned to user"
}
```

##### Export Assets
```http
POST /api/assets/export/
Content-Type: application/json

{
    "filters": {
        "asset_status": "idle",
        "department_id": "uuid"
    },
    "columns": [
        "asset_code",
        "asset_name",
        "brand",
        "model",
        "asset_status",
        "original_value"
    ]
}
```

Returns: Excel file (.xlsx) download

#### Asset Categories

##### Category Tree
```http
GET /api/assets/categories/tree/
```

### Inventory Module

#### Inventory Tasks

##### List Tasks
```http
GET /api/inventory/tasks/
```

##### Create Task
```http
POST /api/inventory/tasks/
Content-Type: application/json

{
    "task_name": "Q1 2024 Inventory",
    "task_type": "full",
    "planned_start_date": "2024-01-15",
    "planned_end_date": "2024-01-20",
    "department_ids": ["uuid1", "uuid2"]
}
```

##### Start Task
```http
POST /api/inventory/tasks/{id}/start/
```

##### Complete Task
```http
POST /api/inventory/tasks/{id}/complete/
```

#### Inventory Scans

##### Record Scan
```http
POST /api/inventory/scans/
Content-Type: application/json

{
    "task": "task_uuid",
    "qr_code": "ASSET_QR_CODE",
    "scan_method": "qr",
    "scan_status": "normal",
    "actual_location_name": "Office A",
    "actual_custodian_name": "John Doe",
    "remark": "Asset in good condition"
}
```

##### Batch Scan
```http
POST /api/inventory/scans/batch-scan/
Content-Type: application/json

{
    "task": "task_uuid",
    "scans": [
        {
            "qr_code": "ASSET_QR_1",
            "scan_method": "qr",
            "actual_location_name": "Office A"
        },
        {
            "qr_code": "ASSET_QR_2",
            "scan_method": "qr",
            "actual_location_name": "Office B"
        }
    ]
}
```

##### Get Scans by Task
```http
GET /api/inventory/scans/by-task/{task_id}/
```

##### Validate QR Code
```http
POST /api/inventory/scans/validate-qr/
Content-Type: application/json

{
    "qr_code": "ASSET_QR_CODE",
    "task_id": "optional_task_uuid"
}
```

Response:
```json
{
    "success": true,
    "data": {
        "valid": true,
        "asset": {
            "id": "uuid",
            "asset_code": "AST001",
            "asset_name": "Laptop Computer"
        }
    }
}
```

### Notifications Module

#### Notifications

##### List Notifications
```http
GET /api/notifications/
```

##### Unread Count
```http
GET /api/notifications/unread-count/
```

Response:
```json
{
    "success": true,
    "data": {
        "count": 5
    }
}
```

##### Mark as Read
```http
POST /api/notifications/{id}/mark-read/
```

##### Mark All as Read
```http
POST /api/notifications/mark-all-read/
```

##### Send Notification
```http
POST /api/notifications/send/
Content-Type: application/json

{
    "recipient_id": "user_uuid",
    "notification_type": "workflow_approval",
    "variables": {
        "asset_name": "Laptop",
        "requester": "John Doe"
    },
    "channels": ["inbox", "email"],
    "priority": "normal"
}
```

### Workflows Module

#### Workflow Definitions

##### List Definitions
```http
GET /api/workflows/definitions/
```

##### Start Workflow
```http
POST /api/workflows/definitions/{id}/start/
Content-Type: application/json

{
    "business_object_code": "asset_pickup",
    "business_id": "pickup_uuid",
    "title": "Asset Pickup Approval",
    "priority": "normal"
}
```

#### Workflow Instances

##### List Instances
```http
GET /api/workflows/instances/
```

##### Get Instance Details
```http
GET /api/workflows/instances/{id}/
```

##### Approve Task
```http
POST /api/workflows/tasks/{id}/approve/
Content-Type: application/json

{
    "comment": "Approved",
    "action": "approve"
}
```

### Accounts Module

#### Users

##### List Users
```http
GET /api/accounts/users/
```

##### Get Current User
```http
GET /api/accounts/users/me/
```

#### Roles

##### List Roles
```http
GET /api/accounts/roles/
```

##### Assign Role to User
```http
POST /api/accounts/roles/{id}/assign-user/
Content-Type: application/json

{
    "user_id": "user_uuid"
}
```

### Organizations Module

#### Departments

##### Department Tree
```http
GET /api/organizations/departments/tree/
```

##### List Departments
```http
GET /api/organizations/departments/
```

#### Locations

##### Location Tree
```http
GET /api/organizations/locations/tree/
```

## Rate Limiting

API requests are rate limited:

- **Standard**: 100 requests per minute
- **Bulk operations**: 10 requests per minute

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

## Common Patterns

### Filtering
Most list endpoints support filtering:
```http
GET /api/assets/?asset_status=active&department_id=uuid
```

### Searching
Full-text search on indexed fields:
```http
GET /api/assets/?search=laptop
```

### Ordering
Sort results:
```http
GET /api/assets/?ordering=-created_at
```

Use `-` prefix for descending order.

### Pagination
All list endpoints support pagination:
```http
GET /api/assets/?page=2&page_size=50
```

### Field Selection
Some endpoints support field selection:
```http
GET /api/assets/?fields=id,asset_code,asset_name
```

## Versioning

API version is included in the URL:
```
/api/v1/resource/
```

Current version: **v1**

## Changelog

### Version 1.0.0 (2024-01-23)
- Initial API release
- Asset management endpoints
- Inventory management endpoints
- Notification system
- Workflow management
- User and organization management

## Support

For API support and questions:
- Documentation: https://docs.gzeams.com/
- Issue Tracker: https://github.com/liugang926/HOOK_GZEAMS/issues
- Email: support@gzeams.com
