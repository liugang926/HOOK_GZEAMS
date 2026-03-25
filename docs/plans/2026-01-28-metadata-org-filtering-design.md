# Metadata Model Organization Filtering - Centralized Design

## Document Information
| Project | Description |
|---------|-------------|
| Design Version | v1.0 |
| Creation Date | 2026-01-28 |
| Status | DRAFT - Pending Review |

---

## 1. Problem Analysis

### 1.1 Root Cause

The system has three types of models with different organization filtering requirements:

| Model Type | Organization Required? | Current Behavior | Expected Behavior |
|------------|------------------------|------------------|-------------------|
| **Business Data** (Asset, Pickup, etc.) | YES | Filtered by org ✅ | Filtered by org ✅ |
| **Metadata** (BusinessObject, FieldDefinition, PageLayout) | NO | Filtered by org ❌ | NOT filtered ❌ |
| **System Config** (DictionaryType, SequenceRule) | NO | Filtered by org ❌ | NOT filtered ❌ |

**Core Issue**: `BusinessObject`, `FieldDefinition`, and `PageLayout` inherit `TenantManager` from `BaseModel`, which automatically filters by organization. But these are **global system metadata**, not organization-specific data.

### 1.2 Impact Analysis

From grep results, the following locations are affected:

| Model | Affected Locations | Type |
|-------|-------------------|------|
| `BusinessObject.objects` | 70+ locations | Services, ViewSets, Serializers, Tests |
| `FieldDefinition.objects` | 15+ locations | Services, ViewSets |
| `PageLayout.objects` | 15+ locations | Services, ViewSets |

**Performance Impact**:
- Each page load triggers multiple metadata queries
- N+1 query problems when loading field definitions
- Cache misses due to organization-specific cache keys

---

## 2. Proposed Solutions

### Option A: Separate Manager Pattern (RECOMMENDED)

**Approach**: Create a `GlobalMetadataManager` that bypasses organization filtering for metadata models.

```python
# apps/common/managers.py
class GlobalMetadataManager(models.Manager):
    """
    Manager for global metadata models that should NOT be organization-filtered.

    Used by: BusinessObject, FieldDefinition, PageLayout, DictionaryType, etc.
    """
    def get_queryset(self):
        # Only filter soft-delete, NOT organization
        return super().get_queryset().filter(is_deleted=False)

class BusinessObject(BaseModel):
    # Use GlobalMetadataManager instead of TenantManager
    objects = GlobalMetadataManager()
    # Keep all_objects for admin access
    all_objects = models.Manager()
```

**Pros**:
- Clean architectural separation
- Explicit intent - metadata models declare their global nature
- No code changes needed in services/viewsets
- Performance benefit - simpler queries

**Cons**:
- Breaks BaseModel inheritance (metadata models don't use TenantManager)
- Need to update 3 model definitions
- Must document this exception clearly

---

### Option B: Context-Aware TenantManager

**Approach**: Modify `TenantManager` to check a model attribute for global metadata flag.

```python
class TenantManager(models.Manager):
    def get_queryset(self):
        queryset = super().get_queryset()
        from apps.common.middleware import get_current_organization
        org_id = get_current_organization()

        # Skip org filtering for global metadata models
        if getattr(self.model._meta, 'is_global_metadata', False):
            org_id = None

        if org_id:
            queryset = queryset.filter(organization_id=org_id)

        queryset = queryset.filter(is_deleted=False)
        return queryset

class BusinessObject(BaseModel):
    class Meta:
        is_global_metadata = True
```

**Pros**:
- Keeps BaseModel inheritance intact
- Backward compatible
- Centralized control

**Cons**:
- More complex logic in TenantManager
- Magic attribute behavior
- Still need to add Meta class to metadata models

---

### Option C: Service Layer Wrapper

**Approach**: Create centralized service methods for metadata access.

```python
# apps/system/services/metadata_query.py
class MetadataQuery:
    """
    Centralized service for metadata model queries.

    All metadata access should go through this service
    to ensure consistent organization filtering behavior.
    """
    @staticmethod
    def get_business_object(code: str) -> BusinessObject:
        return BusinessObject.all_objects.get(code=code, is_deleted=False)

    @staticmethod
    def list_business_objects():
        return BusinessObject.all_objects.filter(is_deleted=False)

    @staticmethod
    def get_field_definitions(business_object: BusinessObject):
        return FieldDefinition.all_objects.filter(
            business_object=business_object,
            is_deleted=False
        )
```

**Pros**:
- Single source of truth
- Easy to add caching
- Explicit API

**Cons**:
- Requires updating 70+ call sites
- Adoption risk - developers may forget to use it
- More verbose code

---

## 3. Recommendation: Option A (Separate Manager)

### 3.1 Implementation Plan

**Phase 1: Create GlobalMetadataManager**
- Create `apps/common/managers.py`
- Define `GlobalMetadataManager` class
- Add unit tests

**Phase 2: Update Metadata Models**
- Update `BusinessObject` to use `GlobalMetadataManager`
- Update `FieldDefinition` to use `GlobalMetadataManager`
- Update `PageLayout` to use `GlobalMetadataManager`
- Keep `organization` field for future multi-org layout customization

**Phase 3: Documentation**
- Add docstring explaining global metadata pattern
- Update CLAUDE.md with metadata model exception
- Add code comments

### 3.2 File Changes

| File | Change |
|------|--------|
| `apps/common/managers.py` | CREATE - Add GlobalMetadataManager |
| `apps/common/models.py` | UPDATE - Import managers |
| `apps/system/models.py` | UPDATE - BusinessObject, FieldDefinition, PageLayout use new manager |

### 3.3 Expected Benefits

1. **Performance**: Fewer database queries, no organization joins needed
2. **Correctness**: Metadata accessible across organizations
3. **Maintainability**: Clear architectural intent
4. **Caching**: Simpler cache keys (no org_id)

---

## 4. Alternative: Hybrid Approach

If Option A is too invasive, consider:

**Short-term**: Use `all_objects` consistently in metadata services
- Update `ObjectRegistry.get_or_create_from_db()` ✅ DONE
- Update `BusinessObjectService` methods
- Update `MetadataCacheService`

**Long-term**: Implement Option A during next refactor cycle

This approach:
- Fixes immediate issues with minimal code change
- Spreads the work over time
- Reduces risk

---

## 5. Performance Optimization (Independent of Solution)

Regardless of which option chosen, also implement:

### 5.1 Metadata Caching

```python
# Cache metadata for 1 hour
@cache_page(3600)
def metadata(request, code):
    ...
```

### 5.2 Query Optimization

```python
# Use select_related/prefetch_related
BusinessObject.objects.prefetch_related(
    'field_definitions',
    'page_layouts'
)
```

### 5.3 Batch Loading

```python
# Load all metadata at startup
def load_system_metadata():
    cache.set('all_business_objects', BusinessObject.objects.all(), 3600)
```

---

## 6. Decision Matrix

| Criterion | Option A | Option B | Option C |
|-----------|----------|----------|----------|
| Implementation effort | Low | Medium | High |
| Code clarity | High | Medium | High |
| Performance | Best | Good | Best |
| Maintainability | Best | Good | Medium |
| Risk | Low | Medium | Low |

---

## 7. Next Steps

Pending user review and approval:

1. [ ] Choose solution option (A, B, C, or Hybrid)
2. [ ] Review and approve implementation plan
3. [ ] Create implementation PR
4. [ ] Test with multiple organizations
5. [ ] Update documentation

---

*Design End*
