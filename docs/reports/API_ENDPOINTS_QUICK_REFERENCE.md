# API Endpoints Quick Reference

## Test Summary (2026-01-28)

✅ **All 9 core business object endpoints are working correctly (100% success rate)**

---

## Correct API URL Paths

### Assets Module
| Business Object | API Endpoint | Status |
|----------------|--------------|--------|
| Asset Cards | `/api/assets/` | ✅ Working (200) |
| Asset Categories | `/api/assets/categories/` | ✅ Working (200) |
| Suppliers | `/api/assets/suppliers/` | ✅ Working (200) |
| Locations | `/api/assets/locations/` | ✅ Working (200) |

### Organizations Module
| Business Object | API Endpoint | Status |
|----------------|--------------|--------|
| Departments | `/api/organizations/departments/` | ✅ Working (200) |

### Consumables Module
| Business Object | API Endpoint | Status |
|----------------|--------------|--------|
| Consumables | `/api/consumables/` | ✅ Working (200) |

### Inventory Module
| Business Object | API Endpoint | Status |
|----------------|--------------|--------|
| Inventory Tasks | `/api/inventory/tasks/` | ✅ Working (200) |

### Lifecycle Module
| Business Object | API Endpoint | Status |
|----------------|--------------|--------|
| Maintenance Records | `/api/lifecycle/maintenance/` | ✅ Working (200) |

---

## URL Configuration Files

| Module | Config File Location |
|--------|---------------------|
| Main Config | `backend/config/urls.py` |
| Assets | `backend/apps/assets/urls.py` |
| Organizations | `backend/apps/organizations/urls.py` |
| Consumables | `backend/apps/consumables/urls.py` |
| Inventory | `backend/apps/inventory/urls.py` |
| Lifecycle | `backend/apps/lifecycle/urls.py` |

---

## Frontend API Call Updates

**If your frontend is using the old URLs, update them:**

```typescript
// ❌ Old/Wrong URLs
'/api/asset-categories/'
'/api/suppliers/'
'/api/locations/'
'/api/departments/'
'/api/inventory-tasks/'
'/api/maintenance/'

// ✅ Correct URLs
'/api/assets/categories/'
'/api/assets/suppliers/'
'/api/assets/locations/'
'/api/organizations/departments/'
'/api/inventory/tasks/'
'/api/lifecycle/maintenance/'
```

---

## Authentication

All endpoints require JWT Bearer Token authentication:

```bash
# 1. Login to get token
POST /api/auth/login/
{
  "username": "admin",
  "password": "admin123"
}

# 2. Use token in subsequent requests
GET /api/assets/
Authorization: Bearer <your-token-here>
```

---

## API Documentation

Interactive API documentation available at:
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

---

## Test Scripts

| Script | Purpose |
|--------|---------|
| `check_correct_endpoints.ps1` | PowerShell script to test all endpoints with correct URLs |
| `test_api_endpoints.ps1` | PowerShell script (initial test with expected URLs) |

---

## Summary

- **Total Endpoints Tested**: 9
- **Working**: 9 (100%)
- **Missing**: 0
- **Errors**: 0

All endpoints are operational. The URL structure follows domain-driven design with related resources nested under parent modules.
