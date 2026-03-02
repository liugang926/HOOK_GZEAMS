# Metadata Organization Filtering - Analysis Report

## Document Information
| Project | Description |
|---------|-------------|
| Report Version | v1.0 |
| Creation Date | 2026-01-28 |
| Report Type | Root Cause Analysis & Design Proposal |

---

## Executive Summary

**Problem**: BusinessObject, FieldDefinition, and PageLayout models inherit `TenantManager` from `BaseModel`, which automatically filters queries by the current organization. However, these are **global system metadata** models that should be accessible across all organizations.

**Impact**:
- Users from non-default organizations get 404 errors accessing metadata
- 70+ code locations use `BusinessObject.objects` incorrectly
- Page loading performance degraded

**Root Cause**: Architecture mismatch - metadata models use the same manager as business data models

**Proposed Solution**: Create a `GlobalMetadataManager` that bypasses organization filtering for metadata models while maintaining soft-delete filtering

---

## 1. Current Architecture Analysis

### 1.1 TenantManager Behavior

```python
class TenantManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        org_id = get_current_organization()  # From thread-local context

        if org_id:
            queryset = queryset.filter(organization_id=org_id)  # ⚠️ PROBLEM

        queryset = queryset.filter(is_deleted=False)
        return queryset
```

**Issue**: All models inheriting `BaseModel` get organization filtering, even when inappropriate.

### 1.2 Model Classification

| Category | Models | Organization Filter? | Current State |
|----------|--------|---------------------|---------------|
| Business Data | Asset, AssetPickup, AssetTransfer, etc. | YES | ✅ Correct |
| System Metadata | BusinessObject, FieldDefinition, PageLayout | NO | ❌ Wrong |
| System Config | DictionaryType, SequenceRule, SystemConfig | NO | ❌ Wrong |

---

## 2. Impact Analysis

### 2.1 Affected Code Locations

**BusinessObject.objects** (70+ locations):
- `apps/system/services/object_registry.py:186` ✅ FIXED
- `apps/system/services/business_object_service.py:137, 176, 215, 241, 293, 387, 424`
- `apps/system/services/metadata_service.py:55, 197`
- `apps/system/services/config_package_service.py:116, 473, 496, 520, 563, 605`
- `apps/system/viewsets/__init__.py:74, 170, 304, 390, 757`
- `apps/common/viewsets/metadata_driven.py:61`
- `apps/common/validators/dynamic_field.py:371`
- `apps/common/filters/metadata_driven.py:66`
- `apps/common/serializers/metadata_driven.py:142`
- Multiple test files...

**FieldDefinition.objects** (15+ locations):
- `apps/system/viewsets/__init__.py:373`
- `apps/system/viewsets/object_router.py:447`
- `apps/system/serializers.py:101`
- `apps/system/services/config_package_service.py:128, 526`
- `apps/system/services/metadata_service.py:101`
- `apps/system/services/metadata_cache_service.py:182`

**PageLayout.objects** (15+ locations):
- `apps/system/viewsets/__init__.py:416, 534, 546, 597, 697, 766`
- `apps/common/viewsets/metadata_driven.py:168`
- `apps/system/services/config_package_service.py:137, 569`
- `apps/system/services/column_config_service.py:79`
- `apps/system/services/metadata_service.py:155`

### 2.2 Performance Impact

When a user loads `/objects/Asset`:

```
1. GET /api/system/objects/Asset/metadata/
   → BusinessObject.objects.get(code='Asset')  ❌ Filtered by org
   → FieldDefinition.objects.filter(business_object=...)  ❌ Filtered by org
   → PageLayout.objects.filter(...)  ❌ Filtered by org

2. Each query includes: WHERE organization_id = 'current_org_id'
3. Returns 0 results if metadata created by different org
4. Frontend receives 404 or incomplete data
```

---

## 3. Solutions Comparison

### Option A: GlobalMetadataManager (RECOMMENDED)

Create a new manager for metadata models:

```python
class GlobalMetadataManager(models.Manager):
    """Manager for global metadata - NO organization filtering."""
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class BusinessObject(BaseModel):
    objects = GlobalMetadataManager()  # Override BaseModel
    all_objects = models.Manager()
```

**Advantages**:
- Clean architectural separation
- No code changes in services/viewsets
- Best performance
- Explicit intent

**Effort**: Low (3 model changes + 1 new file)

---

### Option B: Context-Aware TenantManager

Modify TenantManager to check for metadata flag:

```python
class TenantManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        org_id = get_current_organization()

        # Skip org filtering for global metadata
        if getattr(self.model._meta, 'is_global_metadata', False):
            org_id = None

        if org_id:
            queryset = queryset.filter(organization_id=org_id)
        # ...
```

**Advantages**:
- Keeps BaseModel inheritance
- Backward compatible

**Effort**: Medium (modify TenantManager + add Meta to 3 models)

---

### Option C: Service Layer Wrapper

Centralize metadata access through service methods:

```python
class MetadataQuery:
    @staticmethod
    def get_business_object(code: str):
        return BusinessObject.all_objects.get(code=code, is_deleted=False)
```

**Advantages**:
- Single source of truth
- Easy to add caching

**Effort**: High (update 70+ call sites)

---

### Option D: Hybrid (Short-term Fix)

Use `all_objects` in critical metadata services only:

**Phase 1** (Immediate):
- `ObjectRegistry.get_or_create_from_db()` ✅ DONE
- `BusinessObjectService` core methods
- `MetadataCacheService`

**Phase 2** (Later):
- Implement Option A or B

**Effort**: Low (spread over time)

---

## 4. Recommendation

**Primary**: Option A (GlobalMetadataManager)
- Best long-term solution
- Clean architecture
- Minimal code changes

**Fallback**: Option D (Hybrid)
- If Option A is too invasive
- Fixes immediate issues
- Spreads work over time

---

## 5. Implementation Plan (Option A)

### Phase 1: Create Manager (1 file)
```
apps/common/managers.py  [NEW]
    - GlobalMetadataManager
    - Documentation
    - Unit tests
```

### Phase 2: Update Models (1 file)
```
apps/system/models.py  [MODIFY]
    - BusinessObject.objects = GlobalMetadataManager()
    - FieldDefinition.objects = GlobalMetadataManager()
    - PageLayout.objects = GlobalMetadataManager()
```

### Phase 3: Documentation
```
CLAUDE.md  [UPDATE]
    - Document metadata model exception
    - Add examples

docs/plans/...  [CREATE]
    - Design document
```

---

## 6. Testing Checklist

- [ ] User from Org A can access BusinessObject created by Org B
- [ ] FieldDefinition query returns all fields for any org
- [ ] PageLayout query returns layouts across orgs
- [ ] Business data (Asset) still filtered by org
- [ ] Soft delete still works for metadata models
- [ ] Cache invalidation works correctly
- [ ] Performance test: metadata load time < 100ms

---

## 7. Related Files

| File | Purpose |
|------|---------|
| `apps/common/models.py` | BaseModel, TenantManager |
| `apps/system/models.py` | BusinessObject, FieldDefinition, PageLayout |
| `apps/system/services/object_registry.py` | Metadata registry (line 186 fixed) |
| `docs/plans/2026-01-28-metadata-org-filtering-design.md` | Full design document |

---

*Report End*
