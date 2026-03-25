# Business Metadata Engine - Quick Start Guide

## Overview
The Business Metadata Engine is now fully implemented! This guide helps you get started quickly.

## Files Created Summary

### Core Implementation (13 files)
```
backend/apps/system/
├── models.py                    # 5 models: BusinessObject, FieldDefinition, PageLayout, DynamicData, DynamicSubTableData
├── serializers/
│   ├── __init__.py             # Exports all serializers
│   └── base.py                 # 6 serializers with BaseModel inheritance
├── filters/
│   ├── __init__.py             # Exports all filters
│   └── base.py                 # 4 filters with BaseModelFilter inheritance
├── views.py                     # 4 ViewSets with BaseModelViewSetWithBatch inheritance
├── dynamic_views.py             # 3 dynamic views: list/form/detail
├── services/
│   ├── __init__.py             # Exports all services
│   ├── metadata_service.py     # Metadata management service
│   └── dynamic_data_service.py # Dynamic data CRUD service
├── urls.py                      # Complete URL routing
├── admin.py                     # Django admin configuration
├── apps.py                      # Django app configuration
└── __init__.py                  # App initialization
```

## Next Steps

### 1. Generate and Apply Migrations
```bash
# Generate migrations
docker-compose exec backend python manage.py makemigrations system

# Review migrations (optional)
docker-compose exec backend python manage.py showmigrations system

# Apply migrations
docker-compose exec backend python manage.py migrate system
```

### 2. Create Superuser (if needed)
```bash
docker-compose exec backend python manage.py createsuperuser
```

### 3. Test with Django Admin
1. Visit: http://localhost:8000/admin/
2. Login with superuser credentials
3. Navigate to "业务元数据引擎" section
4. Create a BusinessObject (e.g., "Asset")
5. Add FieldDefinitions to the BusinessObject
6. Create PageLayouts for form/list/detail

### 4. Test API Endpoints

#### Create Business Object
```bash
curl -X POST http://localhost:8000/api/system/business-objects/ \
  -H "Content-Type: application/json" \
  -d '{
    "code": "Asset",
    "name": "资产卡片",
    "description": "固定资产主数据",
    "enable_workflow": false,
    "enable_version": true
  }'
```

#### Create Field Definition
```bash
curl -X POST http://localhost:8000/api/system/field-definitions/ \
  -H "Content-Type: application/json" \
  -d '{
    "business_object": "BUSINESS_OBJECT_UUID",
    "code": "asset_name",
    "name": "资产名称",
    "field_type": "text",
    "is_required": true,
    "show_in_list": true,
    "sort_order": 1
  }'
```

#### Create Dynamic Data
```bash
curl -X POST http://localhost:8000/api/system/dynamic-data/ \
  -H "Content-Type: application/json" \
  -d '{
    "business_object": "BUSINESS_OBJECT_UUID",
    "dynamic_fields": {
      "asset_name": "测试资产"
    }
  }'
```

#### Query Dynamic List
```bash
curl -X GET "http://localhost:8000/api/dynamic/Asset/list/?page=1&page_size=20"
```

## Key Features

### 23 Supported Field Types
- **Basic**: text, textarea, number, currency, date, datetime
- **Choice**: select, multi_select, radio, checkbox, boolean
- **Reference**: user, department, reference
- **Advanced**: formula, sub_table, file, image, rich_text
- **Read-Only**: qr_code, barcode

### Formula Fields
Formula fields support calculations:
```python
# Example formula
{quantity} * {unit_price}

# Supported operators
+, -, *, /, %, **
```

### Batch Operations
All ViewSets support batch operations:
```bash
# Batch delete
POST /api/system/business-objects/batch-delete/
{"ids": ["uuid1", "uuid2", "uuid3"]}

# Batch restore
POST /api/system/business-objects/batch-restore/
{"ids": ["uuid1", "uuid2"]}

# Batch update
POST /api/system/business-objects/batch-update/
{
  "ids": ["uuid1"],
  "data": {"enable_workflow": true}
}
```

### Deleted Records Management
```bash
# List deleted records
GET /api/system/business-objects/deleted/

# Restore single record
POST /api/system/business-objects/{id}/restore/
```

## Testing Checklist

- [ ] Migrations generated and applied successfully
- [ ] Django admin accessible and working
- [ ] Create BusinessObject via admin
- [ ] Add FieldDefinitions via admin
- [ ] Create PageLayouts via admin
- [ ] Test API endpoints with Postman/curl
- [ ] Verify organization isolation
- [ ] Test soft delete functionality
- [ ] Test batch operations
- [ ] Test dynamic views (list/form/detail)
- [ ] Verify formula field calculations

## API Response Format

### Success Response
```json
{
    "success": true,
    "message": "操作成功",
    "data": {
        "id": "uuid",
        ...
    }
}
```

### Error Response
```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "验证失败",
        "details": {...}
    }
}
```

### List Response (Paginated)
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": null,
        "previous": null,
        "results": [...]
    }
}
```

## Common Issues

### Issue: "relation already exists"
**Solution**: Drop and recreate database
```bash
docker-compose exec backend python manage.py migrate system --fake-initial
```

### Issue: "business object does not exist"
**Solution**: Ensure BusinessObject is created before FieldDefinitions

### Issue: Formula fields returning 0
**Solution**: Install simpleeval package
```bash
docker-compose exec backend pip install simpleeval
```

## Need Help?

- Full Implementation Report: `PHASE1_3_IMPLEMENTATION_REPORT.md`
- PRD Document: `docs/plans/phase1_3_business_metadata/backend.md`
- Common Base Features: `docs/plans/common_base_features/backend.md`

---

**Status**: ✅ Implementation Complete
**Ready for**: Migrations, Testing, Frontend Integration
