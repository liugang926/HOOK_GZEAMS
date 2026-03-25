# GZEAMS Hybrid Architecture: Hardcoded Core + Low-Code Extensions

## Document Information

| Project | Description |
|---------|-------------|
| Document Version | v1.0 |
| Created Date | 2025-01-20 |
| Author | Claude |
| Status | Active |

---

## 1. Executive Summary

GZEAMS is a **metadata-driven low-code platform** that employs a **hybrid architecture** combining:

1. **Hardcoded Core Modules**: Enterprise-critical business objects implemented as Django models with full type safety and optimized performance
2. **Low-Code Extensions**: Custom business objects configured through metadata without code changes

### 1.1 Architecture Decision: Option A

**Decision**: Keep core business modules as hardcoded Django models while using the low-code engine for extensions and custom objects.

**Rationale**:
| Factor | Hardcoded Core | Low-Code Extensions |
|--------|---------------|---------------------|
| **Performance** | Optimized queries, indexes | JSONB with GIN indexes |
| **Type Safety** | Compile-time checks | Runtime validation |
| **Business Logic** | Complex workflows, rules | Formula fields only |
| **Change Frequency** | Stable core schema | Dynamic custom fields |
| **Integration** | ERP, Finance, SSO | Internal extensions |

---

## 2. Core Module Definition

### 2.1 Hardcoded Business Objects

The following modules are implemented as hardcoded Django models:

| Module | Models | Purpose |
|--------|--------|---------|
| **Assets** | Asset, AssetCategory, Supplier, Location, AssetStatusLog | Core asset management |
| **Asset Operations** | AssetPickup, AssetTransfer, AssetReturn, AssetLoan | Asset lifecycle operations |
| **Consumables** | Consumable, ConsumableCategory, ConsumableStock, ConsumablePurchase, ConsumableIssue | Consumable tracking |
| **Lifecycle** | PurchaseRequest, AssetReceipt, Maintenance, MaintenancePlan, DisposalRequest | Asset lifecycle events |
| **Inventory** | InventoryTask, InventorySnapshot, InventoryItem | Asset inventory management |
| **Organizations** | Organization, Department | Multi-tenant structure |
| **Accounts** | User, Role, Permission | RBAC security |
| **Workflows** | WorkflowDefinition, WorkflowInstance, WorkflowNode | BPM engine |

### 2.2 Low-Code Business Objects

Custom objects defined through the metadata engine:

- Department-specific request forms
- Custom approval workflows
- Extended asset attributes
- Integration-specific data structures

---

## 3. Integration Architecture

### 3.1 Metadata Model for Hardcoded Objects

Hardcoded models register themselves as `BusinessObject` entries with a flag indicating they are hardcoded:

```python
# BusinessObject model extension
class BusinessObject(BaseModel):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)

    # NEW: Flag to identify hardcoded models
    is_hardcoded = models.BooleanField(
        default=False,
        db_comment='True for core Django models, False for metadata-driven objects'
    )

    # Reference to actual Django model for hardcoded objects
    django_model_path = models.CharField(
        max_length=200,
        blank=True,
        db_comment='Python path to Django model (e.g., apps.assets.models.Asset)'
    )

    # For low-code objects: table_name for DynamicData
    table_name = models.CharField(
        max_length=100,
        blank=True,
        db_comment='Custom table name for low-code objects'
    )
```

### 3.2 Field Registration for Hardcoded Models

Hardcoded models expose their field definitions to the metadata engine:

```python
# ModelFieldDefinition - auto-generated from hardcoded models
class ModelFieldDefinition(BaseModel):
    """Field definitions exposed by hardcoded Django models."""

    business_object = models.ForeignKey(BusinessObject, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=50)  # Actual Django field name
    display_name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20)  # Mapped to FieldDefinition types
    is_required = models.BooleanField(default=False)
    is_readonly = models.BooleanField(default=False)
    is_editable = models.BooleanField(default=True)
```

### 3.3 Field Type Mapping

| Django Field Type | Metadata Field Type | Component |
|-------------------|-------------------|-----------|
| CharField | text | el-input |
| TextField | textarea | el-input type="textarea" |
| IntegerField | number | el-input-number |
| DecimalField | currency | CurrencyInput |
| DateField | date | el-date-picker |
| DateTimeField | datetime | el-date-picker |
| BooleanField | boolean | el-switch |
| ForeignKey (User) | user | UserPicker |
| ForeignKey (Organization) | department | DeptTreePicker |
| ForeignKey (Asset) | asset | AssetSelector |
| ForeignKey (*) | reference | ReferenceSelector |

---

## 4. Low-Code Engine Visibility

### 4.1 Object Association Fields

When creating a reference field in the low-code engine, users can select from:

1. **Core Hardcoded Objects** (marked with `is_hardcoded=True`)
2. **Custom Low-Code Objects** (created by users)

```json
// API Response for GET /api/system/objects/?type=reference
{
  "success": true,
  "data": {
    "hardcoded": [
      {"code": "Asset", "name": "资产", "model": "apps.assets.models.Asset"},
      {"code": "AssetPickup", "name": "资产领用", "model": "apps.assets.models.AssetPickup"},
      {"code": "Consumable", "name": "耗材", "model": "apps.consumables.models.Consumable"}
    ],
    "custom": [
      {"code": "CustomRequest", "name": "自定义申请", "table": "dynamic_data_customrequest"}
    ]
  }
}
```

### 4.2 Custom Field Layout Configuration

When configuring custom fields for hardcoded models, the available models are:

```python
# Service to get all business objects (hardcoded + low-code)
class BusinessObjectService:
    def get_all_objects(self, include_hardcoded=True, include_custom=True):
        """Get all business objects available for reference."""
        queryset = BusinessObject.objects.filter(is_deleted=False)

        if include_hardcoded:
            hardcoded = queryset.filter(is_hardcoded=True)
        if include_custom:
            custom = queryset.filter(is_hardcoded=False)

        return {
            'hardcoded': self._format_hardcoded_objects(hardcoded),
            'custom': self._format_custom_objects(custom)
        }

    def _format_hardcoded_objects(self, queryset):
        """Format hardcoded objects with their Django model info."""
        return [{
            'code': obj.code,
            'name': obj.name,
            'name_en': obj.name_en,
            'model_path': obj.django_model_path,
            'app_label': obj.django_model_path.split('.')[0],  # e.g., 'assets'
            'field_count': obj.model_fields.count(),
        } for obj in queryset]

    def _format_custom_objects(self, queryset):
        """Format low-code objects with their table info."""
        return [{
            'code': obj.code,
            'name': obj.name,
            'name_en': obj.name_en,
            'table_name': obj.table_name,
            'field_count': obj.field_definitions.count(),
        } for obj in queryset]
```

---

## 5. Implementation Plan

### 5.1 Phase 1: BusinessObject Registration

Create management command to register hardcoded models:

```bash
# Register all hardcoded models as BusinessObjects
python manage.py register_core_models

# Creates BusinessObject entries with:
# - is_hardcoded=True
# - django_model_path='apps.assets.models.Asset'
# - code='Asset', name='资产'
```

### 5.2 Phase 2: Field Definition Exposure

Auto-generate `ModelFieldDefinition` entries from Django model metadata:

```python
# apps/system/management/commands/sync_model_fields.py
class Command(BaseCommand):
    def handle(self, *args, **options):
        for obj in BusinessObject.objects.filter(is_hardcoded=True):
            model = get_model(obj.django_model_path)
            for field in model._meta.get_fields():
                ModelFieldDefinition.objects.get_or_create(
                    business_object=obj,
                    field_name=field.name,
                    defaults={
                        'display_name': field.verbose_name,
                        'field_type': map_django_type(field),
                        'is_required': not field.null,
                        'is_readonly': not field.editable,
                    }
                )
```

### 5.3 Phase 3: API Endpoints

Create unified API for querying business objects:

```python
# apps/system/views/business_object.py
class BusinessObjectViewSet(BaseModelViewSetWithBatch):
    """Unified API for both hardcoded and low-code business objects."""

    def list(self, request):
        """Return all business objects, grouped by type."""
        service = BusinessObjectService()
        data = service.get_all_objects()
        return Response({'success': True, 'data': data})

    @action(detail=False, methods=['get'])
    def reference_options(self, request):
        """Get objects available for reference field selection."""
        service = BusinessObjectService()
        data = service.get_reference_options()
        return Response({'success': True, 'data': data})

    @action(detail=False, methods=['get'])
    def fields(self, request):
        """Get field definitions for a specific object."""
        obj_code = request.query_params.get('object_code')
        service = BusinessObjectService()
        data = service.get_object_fields(obj_code)
        return Response({'success': True, 'data': data})
```

---

## 6. Public Model Reference

### 6.1 Base Class Inheritance

| Component | Base Class | Path | Auto-Features |
|-----------|-----------|------|---------------|
| Model | BaseModel | apps.common.models.BaseModel | Org isolation, soft delete, audit fields, custom_fields |
| Serializer | BaseModelSerializer | apps.common.serializers.base.BaseModelSerializer | Common fields, custom_fields serialization |
| ViewSet | BaseModelViewSetWithBatch | apps.common.viewsets.base.BaseModelViewSetWithBatch | Org filtering, soft delete, batch operations |
| Filter | BaseModelFilter | apps.common.filters.base.BaseModelFilter | Time range, user filtering |
| Service | BaseCRUDService | apps.common.services.base_crud.BaseCRUDService | Unified CRUD methods |

### 6.2 New Metadata Models

| Model | Purpose | Key Fields |
|-------|---------|------------|
| BusinessObject (extended) | Unified business object registry | is_hardcoded, django_model_path, table_name |
| ModelFieldDefinition (new) | Exposed fields from hardcoded models | business_object, field_name, field_type |
| FieldDefinition (existing) | Low-code field definitions | business_object, field_type, options |

---

## 7. API Specification

### 7.1 Get All Business Objects

```
GET /api/system/business-objects/
```

Response:
```json
{
  "success": true,
  "data": {
    "hardcoded": [
      {
        "code": "Asset",
        "name": "资产",
        "name_en": "Asset",
        "app_label": "assets",
        "model_path": "apps.assets.models.Asset",
        "field_count": 25
      }
    ],
    "custom": [
      {
        "code": "CustomRequest",
        "name": "自定义申请",
        "table_name": "dynamic_data_customrequest",
        "field_count": 10
      }
    ]
  }
}
```

### 7.2 Get Reference Field Options

```
GET /api/system/business-objects/reference-options/
```

Response:
```json
{
  "success": true,
  "data": [
    {"value": "Asset", "label": "资产", "type": "hardcoded"},
    {"value": "Consumable", "label": "耗材", "type": "hardcoded"},
    {"value": "CustomRequest", "label": "自定义申请", "type": "custom"}
  ]
}
```

### 7.3 Get Object Fields

```
GET /api/system/business-objects/fields/?object_code=Asset
```

Response:
```json
{
  "success": true,
  "data": {
    "object_code": "Asset",
    "object_name": "资产",
    "is_hardcoded": true,
    "fields": [
      {
        "field_name": "asset_code",
        "display_name": "资产编码",
        "field_type": "text",
        "is_required": true,
        "is_readonly": true,
        "is_editable": false
      },
      {
        "field_name": "asset_category",
        "display_name": "资产分类",
        "field_type": "category",
        "is_required": true,
        "is_readonly": false,
        "is_editable": true
      }
    ]
  }
}
```

---

## 8. Frontend Integration

### 8.1 Reference Field Component

```vue
<!-- ReferenceField.vue -->
<template>
  <el-select
    v-model="selectedObject"
    placeholder="Select关联对象"
    @change="onObjectChange"
  >
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
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getBusinessObjects } from '@/api/system'

const hardcodedObjects = ref([])
const customObjects = ref([])

onMounted(async () => {
  const { data } = await getBusinessObjects()
  hardcodedObjects.value = data.hardcoded
  customObjects.value = data.custom
})
</script>
```

### 8.2 Field Designer Component

```vue
<!-- FieldDesigner.vue -->
<template>
  <div class="field-designer">
    <!-- Field type selection includes reference to core modules -->
    <el-form-item label="字段类型">
      <el-select v-model="field.field_type">
        <el-option-group label="基础类型">
          <el-option label="单行文本" value="text" />
          <el-option label="数字" value="number" />
        </el-option-group>

        <el-option-group label="关联核心模块">
          <el-option label="关联资产" value="asset" />
          <el-option label="关联用户" value="user" />
          <el-option label="关联部门" value="department" />
        </el-option-group>

        <el-option-group label="关联自定义对象">
          <el-option
            v-for="obj in customObjects"
            :key="obj.code"
            :label="`关联${obj.name}`"
            :value="`ref:${obj.code}`"
          />
        </el-option-group>
      </el-select>
    </el-form-item>
  </div>
</template>
```

---

## 9. Migration Strategy

### 9.1 Step 1: Extend BusinessObject Model

```python
# Migration file: 0001_add_harcoded_flags.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('system', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='businessobject',
            name='is_hardcoded',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='businessobject',
            name='django_model_path',
            field=models.CharField(max_length=200, blank=True),
        ),
    ]
```

### 9.2 Step 2: Create ModelFieldDefinition Model

```python
# Migration file: 0002_add_modelfielddefinition.py
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [
        ('system', '0001_add_harcoded_flags'),
    ]

    operations = [
        migrations.CreateModel(
            name='ModelFieldDefinition',
            fields=[
                ('id', models.UUIDField(primary_key=True)),
                ('field_name', models.CharField(max_length=50)),
                ('display_name', models.CharField(max_length=100)),
                ('field_type', models.CharField(max_length=20)),
                ('is_required', models.BooleanField(default=False)),
                ('is_readonly', models.BooleanField(default=False)),
                ('is_editable', models.BooleanField(default=True)),
                ('business_object', models.ForeignKey(
                    'system.BusinessObject',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='model_fields'
                )),
                # ... inherited BaseModel fields
            ],
        ),
    ]
```

### 9.3 Step 3: Register Core Models

```bash
# Run after migrations
python manage.py register_core_models
python manage.py sync_model_fields
```

---

## 10. Validation Rules

### 10.1 Hardcoded Object Constraints

- `is_hardcoded=True` objects MUST have `django_model_path`
- `is_hardcoded=True` objects CANNOT have `table_name` (uses Django model)
- Fields of hardcoded objects are read-only in metadata UI
- Hardcoded objects cannot be deleted through metadata UI

### 10.2 Custom Object Constraints

- `is_hardcoded=False` objects MUST have `table_name`
- `is_hardcoded=False` objects CANNOT have `django_model_path`
- Fields of custom objects are fully editable

---

## 11. Benefits of Hybrid Architecture

| Aspect | Benefit |
|--------|---------|
| **Performance** | Core queries use optimized indexes, no JSONB overhead |
| **Type Safety** | Compile-time checks for core models prevent runtime errors |
| **Flexibility** | Custom fields can be added without deployment |
| **Integration** | ERP/Finance integrations work with stable schema |
| **Upgrade Safety** | Core schema changes are versioned with migrations |
| **User Experience** | Consistent UI for both core and custom objects |

---

## 12. Summary

This hybrid architecture provides:

1. **Stable Core**: Hardcoded Django models for enterprise-critical operations
2. **Extensible Edges**: Low-code engine for custom business requirements
3. **Unified Interface**: Single metadata API for both types of objects
4. **Visibility**: Core modules appear as options in low-code configuration UIs

The architecture ensures that GZEAMS remains both a high-performance enterprise system and a flexible low-code platform.
