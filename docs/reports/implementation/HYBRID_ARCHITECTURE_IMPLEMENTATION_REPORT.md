# Hybrid Architecture Implementation Report

## Document Information

| Project | Description |
|---------|-------------|
| Report Version | v1.0 |
| Created Date | 2025-01-20 |
| Author | Claude |
| Type | Implementation Report |

---

## 1. Summary

This document summarizes the implementation of the **Hybrid Architecture** for GZEAMS (固定资产管理系统), which combines hardcoded Django models for core business objects with a low-code metadata engine for extensions.

### 1.1 Architecture Decision

**Decision**: Option A - Keep hardcoded core modules while integrating them with the low-code engine.

**Key Features**:
- Core models (Assets, Consumables, Lifecycle, etc.) remain as hardcoded Django models
- Low-code engine used for custom business objects and extensions
- Hardcoded models are visible and selectable in low-code configuration UIs
- Unified API for both types of objects

---

## 2. Implementation Overview

### 2.1 Files Created

| File | Description |
|------|-------------|
| `docs/plans/common_base_features/00_core/hybrid_architecture.md` | PRD document for hybrid architecture |
| `backend/apps/system/services/business_object_service.py` | Service for unified business object access |
| `backend/apps/system/serializers/business_object.py` | Serializers for business objects |
| `backend/apps/system/views/business_object.py` | ViewSets for business object API (standalone) |
| `backend/apps/system/management/commands/register_core_models.py` | Management command to register core models |
| `backend/apps/system/migrations/0002_hybrid_architecture.py` | Database migration |

### 2.2 Files Modified

| File | Changes |
|------|---------|
| `backend/apps/system/models.py` | Added `is_hardcoded`, `django_model_path` to BusinessObject; Added `ModelFieldDefinition` model |
| `backend/apps/system/viewsets/__init__.py` | Enhanced BusinessObjectViewSet with hybrid architecture endpoints |

---

## 3. Technical Changes

### 3.1 Model Changes

#### BusinessObject Extensions

```python
class BusinessObject(BaseModel):
    # ... existing fields ...

    # NEW: Hybrid architecture flags
    is_hardcoded = models.BooleanField(default=False)
    django_model_path = models.CharField(max_length=200, blank=True)
```

#### New ModelFieldDefinition Model

```python
class ModelFieldDefinition(BaseModel):
    """Exposes fields from hardcoded Django models to the low-code engine."""

    business_object = models.ForeignKey(BusinessObject, ...)
    field_name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=50)
    django_field_type = models.CharField(max_length=50)
    # ... validation and display flags
```

### 3.2 Service Layer

`BusinessObjectService` provides:
- `get_all_objects()` - Returns both hardcoded and custom objects
- `get_reference_options()` - For UI object selection
- `get_object_fields()` - Get field definitions for an object
- `register_hardcoded_object()` - Register a hardcoded model
- `sync_model_fields()` - Sync Django model fields to metadata

### 3.3 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/system/business-objects/` | GET | List all objects (grouped by type) |
| `/api/system/business-objects/reference-options/` | GET | Get objects for reference field |
| `/api/system/business-objects/fields/?object_code=X` | GET | Get fields for an object |
| `/api/system/business-objects/hardcoded/` | GET | List hardcoded objects only |
| `/api/system/business-objects/custom/` | GET | List custom objects only |
| `/api/system/business-objects/{id}/sync-fields/` | GET | Sync model fields |

### 3.4 Management Command

```bash
# Register all hardcoded models as BusinessObjects
python manage.py register_core_models

# Register and sync fields
python manage.py register_core_models --sync-fields

# Register specific model
python manage.py register_core_models --code Asset

# Update existing registrations
python manage.py register_core_models --force
```

---

## 4. Core Model Registry

The following hardcoded models are registered:

| Module | Models |
|--------|--------|
| **Assets** | Asset, AssetCategory, Supplier, Location, AssetStatusLog, AssetPickup, AssetTransfer, AssetReturn, AssetLoan |
| **Consumables** | Consumable, ConsumableCategory, ConsumableStock, ConsumablePurchase, ConsumableIssue |
| **Lifecycle** | PurchaseRequest, AssetReceipt, Maintenance, MaintenancePlan, DisposalRequest |
| **Inventory** | InventoryTask, InventorySnapshot, InventoryItem |
| **Organizations** | Organization, Department |
| **Accounts** | User, Role |
| **Workflows** | WorkflowDefinition, WorkflowInstance |

---

## 5. Usage Examples

### 5.1 Get All Business Objects (Grouped)

```bash
GET /api/system/business-objects/

Response:
{
    "success": true,
    "data": {
        "hardcoded": [
            {"code": "Asset", "name": "资产", "app_label": "assets", ...}
        ],
        "custom": [
            {"code": "CustomRequest", "name": "自定义申请", ...}
        ]
    }
}
```

### 5.2 Get Reference Options

```bash
GET /api/system/business-objects/reference-options/

Response:
{
    "success": true,
    "data": [
        {"value": "Asset", "label": "资产", "type": "hardcoded", "icon": "box"},
        {"value": "CustomRequest", "label": "自定义申请", "type": "custom", "icon": "document"}
    ]
}
```

### 5.3 Get Object Fields

```bash
GET /api/system/business-objects/fields/?object_code=Asset

Response:
{
    "success": true,
    "data": {
        "object_code": "Asset",
        "object_name": "资产",
        "is_hardcoded": true,
        "fields": [
            {"field_name": "asset_code", "display_name": "资产编码", "field_type": "text", ...}
        ]
    }
}
```

---

## 6. Frontend Integration

### 6.1 Reference Field Component

```vue
<el-select v-model="selectedObject" placeholder="Select关联对象">
  <el-option-group label="核心模块">
    <el-option
      v-for="obj in hardcodedObjects"
      :key="obj.code"
      :label="obj.name"
      :value="obj.code"
    >
      <span>{{ obj.name }}</span>
      <span class="type-badge">核心</span>
    </el-option>
  </el-option-group>

  <el-option-group label="自定义对象">
    <el-option
      v-for="obj in customObjects"
      :key="obj.code"
      :label="obj.name"
      :value="obj.code"
    >
      <span>{{ obj.name }}</span>
      <span class="type-badge">自定义</span>
    </el-option>
  </el-option-group>
</el-select>
```

---

## 7. Benefits of This Architecture

| Aspect | Benefit |
|--------|---------|
| **Performance** | Core queries use optimized Django ORM with proper indexes |
| **Type Safety** | Compile-time checks for core models |
| **Flexibility** | Custom fields can be added without deployment |
| **Integration** | ERP/Finance integrations work with stable schema |
| **Upgrade Safety** | Core schema changes are versioned with migrations |
| **User Experience** | Consistent UI for both core and custom objects |

---

## 8. Next Steps

1. **Run Migrations**: Apply database migrations
   ```bash
   docker-compose exec backend python manage.py migrate
   ```

2. **Register Core Models**: Create BusinessObject entries for hardcoded models
   ```bash
   docker-compose exec backend python manage.py register_core_models --sync-fields
   ```

3. **Update Frontend**: Implement reference field component with hardcoded/custom grouping

4. **Test API**: Verify all endpoints return expected data

---

## 9. Validation Rules

### Hardcoded Objects
- Cannot be created/deleted through API
- Must have `django_model_path`
- Cannot have `table_name`

### Custom Objects
- Must have `table_name`
- Cannot have `django_model_path`
- Fully editable through API

---

## 10. Completion Status

| Task | Status |
|------|--------|
| PRD Documentation | ✅ Completed |
| Model Extensions | ✅ Completed |
| Service Layer | ✅ Completed |
| API Endpoints | ✅ Completed |
| Serializers | ✅ Completed |
| Management Command | ✅ Completed |
| Database Migration | ✅ Completed |
| Frontend Integration | ⏳ Pending |
| Testing | ⏳ Pending |
