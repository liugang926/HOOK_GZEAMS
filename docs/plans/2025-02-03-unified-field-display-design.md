# Unified Field Display Architecture - Design PRD

## Document Information

| Project | Description |
|---------|-------------|
| PRD Version | v1.0 |
| Creation Date | 2025-02-03 |
| Status | Design Review |
| Author | Claude (Architecture Analysis) |

---

## 1. Problem Statement

### 1.1 Current Issue

**Field Display Inconsistency**: Edit pages show MORE fields than detail pages, causing user confusion and data inconsistency.

**Example Case - `maintenance_records` field:**
- **Detail Page (AssetDetail.vue)**: Uses hardcoded `detailSections` - `maintenance_records` is NOT included
- **Edit Page (DynamicForm)**: Loads ALL fields from metadata including `maintenance_records` as a reverse relation (subTable type)

### 1.2 Root Cause Analysis

| Aspect | Detail Page | Edit Page |
|--------|-------------|-----------|
| **Field Source** | Hardcoded in component | From FieldDefinition metadata |
| **Rendering Method** | Static field list | Metadata-driven DynamicForm |
| **Reverse Relations** | NOT included | Included as sub_table |
| **Field Types** | ~6 basic types | 20+ types |
| **Consistency** | Manual sync required | Automatic from metadata |

### 1.3 The Real Problem

`maintenance_records` is a **reverse relation** from the `Maintenance` model back to `Asset` (via `related_name='maintenance_records'`). It should NOT be treated as a regular editable field, but rather as a related object display.

---

## 2. Design Solution: Full Metadata-Driven Architecture

### 2.1 Core Principles

1. **Single Source of Truth**: All field definitions come from metadata
2. **Context-Aware Rendering**: Same field, different display based on context (form/detail/list)
3. **Reverse Relation Handling**: Proper categorization and display of reverse relations
4. **Zero Hardcoding**: All pages use metadata-driven rendering

### 2.2 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend View Layer                      │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Detail Page   │    Edit Page    │      List Page          │
│  (BaseDetailPage)│  (DynamicForm)  │   (BaseListPage)        │
├─────────────────┴─────────────────┴─────────────────────────┤
│              Unified Field Renderer (FieldRenderer)          │
│        - Context-aware rendering based on field_type         │
│        - Edit mode vs read mode handling                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Metadata Orchestration Layer               │
│         (useFieldMetadata composable)                       │
│    - Fetches field definitions by context                   │
│    - Filters fields by view type (form/detail/list)         │
│    - Separates editable fields from reverse relations        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend API Layer                       │
│  /api/system/business-objects/{code}/fields/?context=form   │
│  /api/system/page-layouts/?object_code=Asset&view_type=detail│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Metadata Storage Layer                    │
│  BusinessObject │ FieldDefinition │ PageLayout              │
│  - field_type   │ - show_in_form  │ - view_type             │
│  - is_hardcoded │ - show_in_detail│ - field_groups          │
│                │ - is_reverse_relation                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Backend Changes

### 3.1 FieldDefinition Model Extensions

**New Fields to Add:**

```python
class FieldDefinition(BaseModel):
    # ... existing fields ...

    # === NEW: Reverse Relation Handling ===
    is_reverse_relation = models.BooleanField(
        default=False,
        db_comment='True if this field represents a reverse relation (related_name)'
    )
    reverse_relation_model = models.CharField(
        max_length=200,
        blank=True,
        db_comment='Path to model that owns this relation (e.g., apps.lifecycle.models.Maintenance)'
    )
    reverse_relation_field = models.CharField(
        max_length=100,
        blank=True,
        db_comment='FK field name on related model (e.g., asset)'
    )

    # === NEW: Context Display Flags ===
    show_in_form = models.BooleanField(
        default=True,
        db_comment='Show in create/edit forms'
    )
    relation_display_mode = models.CharField(
        max_length=20,
        choices=[
            ('inline_editable', 'Inline Editable Table'),
            ('inline_readonly', 'Inline Read-Only Table'),
            ('tab_readonly', 'Tab Read-Only Table'),
        ],
        default='inline_editable',
        db_comment='How to display reverse relations'
    )
```

### 3.2 ModelFieldDefinition Updates

**Add Reverse Relation Detection:**

```python
@classmethod
def from_django_field(cls, business_object, field):
    # ... existing code ...

    # Detect reverse relations
    is_reverse = False
    reverse_model = ''
    reverse_field = ''

    # Check if field name matches a related_name pattern
    # This requires inspecting related models
    if hasattr(field, 'remote_field') and field.remote_field:
        # This is a forward relation (ForeignKey)
        pass
    else:
        # Check for reverse relation by name
        # Reverse relations typically end in 's' or use specific related_name
        is_reverse = cls._detect_reverse_relation(business_object, field.name)

    return cls(
        # ... existing fields ...
        is_reverse_relation=is_reverse,
        reverse_relation_model=reverse_model,
        reverse_relation_field=reverse_field,
    )
```

### 3.3 PageLayout Model Extensions

**Enhanced Layout Configuration:**

```python
class PageLayout(BaseModel):
    # ... existing fields ...

    # === NEW: Tab Configuration for Detail Views ===
    layout_config = models.JSONField(
        default=dict,
        db_comment='''
        Enhanced JSON configuration:
        {
            "sections": [...],           // Form sections
            "tabs": [                    // Detail tabs
                {
                    "name": "maintenance_records",
                    "label": "维保记录",
                    "type": "relation_table",
                    "relation_field": "maintenance_records",
                    "readonly": true,
                    "columns": [...]
                }
            ]
        }
        '''
    )
```

### 3.4 API Endpoints

**Enhanced Field Metadata Endpoint:**

```http
GET /api/system/business-objects/{code}/fields/?context={context}
```

**Query Parameters:**
- `context`: `form` | `detail` | `list`
- `include_relations`: `true` | `false`

**Response Format:**

```json
{
    "success": true,
    "data": {
        "editable_fields": [
            {
                "code": "name",
                "name": "资产名称",
                "field_type": "text",
                "is_required": true,
                "show_in_form": true,
                "show_in_detail": true
            }
        ],
        "reverse_relations": [
            {
                "code": "maintenance_records",
                "name": "维保记录",
                "field_type": "sub_table",
                "is_reverse_relation": true,
                "reverse_relation_model": "apps.lifecycle.models.Maintenance",
                "relation_display_mode": "tab_readonly",
                "related_fields": [...]
            }
        ]
    }
}
```

---

## 4. Frontend Changes

### 4.1 New Composable: `useFieldMetadata`

**Location:** `frontend/src/composables/useFieldMetadata.ts`

```typescript
import { ref, computed } from 'vue'
import { businessObjectApi } from '@/api/system'

export interface FieldMetadata {
  code: string
  name: string
  field_type: string
  is_reverse_relation: boolean
  relation_display_mode?: string
  show_in_form: boolean
  show_in_detail: boolean
  show_in_list: boolean
  // ... other field properties
}

export function useFieldMetadata(objectCode: string) {
  const fields = ref<FieldMetadata[]>([])
  const loading = ref(false)
  const error = ref<Error | null>(null)

  // Separate editable fields from reverse relations
  const editableFields = computed(() =>
    fields.value.filter(f => !f.is_reverse_relation)
  )

  const reverseRelations = computed(() =>
    fields.value.filter(f => f.is_reverse_relation)
  )

  // Context-aware field filtering
  async function fetchFields(context: 'form' | 'detail' | 'list') {
    loading.value = true
    try {
      const response = await businessObjectApi.getFields(objectCode, { context })
      fields.value = response.data
    } catch (e) {
      error.value = e as Error
    } finally {
      loading.value = false
    }
  }

  return {
    fields,
    editableFields,
    reverseRelations,
    loading,
    error,
    fetchFields
  }
}
```

### 4.2 Enhanced BaseDetailPage

**Key Changes:**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useFieldMetadata } from '@/composables/useFieldMetadata'
import { useRoute } from 'vue-router'
import DynamicTabs from '@/components/common/DynamicTabs.vue'
import RelatedObjectTable from '@/components/common/RelatedObjectTable.vue'

const props = defineProps<{
  objectCode: string
  id: string
}>()

const { editableFields, reverseRelations, fetchFields } = useFieldMetadata(props.objectCode)

const activeTab = ref('main')
const record = ref(null)

onMounted(async () => {
  await fetchFields('detail')
  // Load record data...
})

// Generate tab configuration
const tabConfig = computed(() => {
  const mainTab = {
    name: 'main',
    label: '基本信息',
    content: 'main-fields'
  }

  const relationTabs = reverseRelations.value.map(rel => ({
    name: rel.code,
    label: rel.name,
    type: 'table',
    readonly: true,
    relation: rel
  }))

  return [mainTab, ...relationTabs]
})
</script>

<template>
  <div class="detail-page">
    <DynamicTabs v-model="activeTab" :tabs="tabConfig">
      <template #main-fields>
        <div class="field-grid">
          <div
            v-for="field in editableFields"
            :key="field.code"
            class="field-item"
          >
            <label>{{ field.name }}</label>
            <span>{{ record?.[field.code] }}</span>
          </div>
        </div>
      </template>

      <template v-for="rel in reverseRelations" :key="rel.code" #[rel.code]>
        <RelatedObjectTable
          :relation="rel"
          :parent-id="id"
          readonly
        />
      </template>
    </DynamicTabs>
  </div>
</template>
```

### 4.3 New Component: RelatedObjectTable

**Location:** `frontend/src/components/common/RelatedObjectTable.vue`

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import { createObjectClient } from '@/api/dynamic'
import BaseTable from '@/components/common/BaseTable.vue'
import ElTable from 'element-plus'

const props = defineProps<{
  relation: FieldMetadata
  parentId: string
  readonly?: boolean
}>()

// Get the related object code from reverse_relation_model
const relatedObjectCode = computed(() => {
  // Extract model name from path like "apps.lifecycle.models.Maintenance"
  const parts = props.relation.reverse_relation_model.split('.')
  return parts[parts.length - 1] // "Maintenance"
})

const api = createObjectClient(relatedObjectCode.value)
const loading = ref(false)
const data = ref([])

async function loadRelatedData() {
  loading.value = true
  try {
    // Filter by parent relation
    const response = await api.list({
      [props.relation.reverse_relation_field]: props.parentId
    })
    data.value = response.results
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadRelatedData()
})
</script>

<template>
  <BaseTable
    :data="data"
    :loading="loading"
    :columns="relation.related_fields"
    :readonly="readonly"
  >
    <template #actions="{ row }">
      <el-button
        type="primary"
        size="small"
        link
        @click="$router.push(`/${relatedObjectCode}/${row.id}`)"
      >
        View Details
      </el-button>
    </template>
  </BaseTable>
</template>
```

### 4.4 DynamicForm Updates

**Context-Aware Field Loading:**

```typescript
// In DynamicForm.vue
const { editableFields, reverseRelations, fetchFields } = useFieldMetadata(props.objectCode)

onMounted(async () => {
  await fetchFields('form') // Get form-specific fields

  // Editable fields render in form
  // Reverse relations render as inline editable tables
})
```

---

## 5. Data Flow Diagrams

### 5.1 Detail Page Flow

```
User navigates to /assets/123
         │
         ▼
BaseDetailPage mounted
         │
         ├──► useFieldMetadata.fetchFields('detail')
         │        │
         │        ▼
         │   Backend: /api/system/business-objects/Asset/fields/?context=detail
         │        │
         │        ▼
         │   Returns: {
         │     editable_fields: [...],
         │     reverse_relations: [
         │       {
         │         code: "maintenance_records",
         │         relation_display_mode: "tab_readonly"
         │       }
         │     ]
         │   }
         │
         ├──► Generate tab config from reverse_relations
         │
         └──► Render:
                  - Main tab with editable_fields
                  - One tab per reverse_relation
```

### 5.2 Edit Page Flow

```
User navigates to /assets/123/edit
         │
         ▼
DynamicForm mounted
         │
         ├──► useFieldMetadata.fetchFields('form')
         │        │
         │        ▼
         │   Backend: /api/system/business-objects/Asset/fields/?context=form
         │        │
         │        ▼
         │   Returns: {
         │     editable_fields: [...],
         │     reverse_relations: [
         │       {
         │         code: "maintenance_records",
         │         relation_display_mode: "inline_editable"
         │       }
         │     ]
         │   }
         │
         └──► Render:
                  - Form fields from editable_fields
                  - Inline editable sub-table for reverse_relations
```

---

## 6. Implementation Phases

### Phase 1: Backend Metadata Extensions (Priority: HIGH)

| Task | File | Effort |
|------|------|--------|
| Add `is_reverse_relation` fields to FieldDefinition | `backend/apps/system/models.py` | 2h |
| Add `show_in_form` field to FieldDefinition | `backend/apps/system/models.py` | 1h |
| Add `relation_display_mode` field to FieldDefinition | `backend/apps/system/models.py` | 1h |
| Create migration | `backend/apps/system/migrations/` | 1h |
| Update field metadata serializer | `backend/apps/system/serializers.py` | 2h |
| Add context filtering to field endpoint | `backend/apps/system/viewsets/` | 3h |

**Total Phase 1: ~10 hours**

### Phase 2: Frontend Metadata Composable (Priority: HIGH)

| Task | File | Effort |
|------|------|--------|
| Create `useFieldMetadata` composable | `frontend/src/composables/useFieldMetadata.ts` | 3h |
| Update businessObjectApi for context parameter | `frontend/src/api/system.ts` | 1h |
| Add TypeScript types for metadata | `frontend/src/types/metadata.ts` | 2h |

**Total Phase 2: ~6 hours**

### Phase 3: BaseDetailPage Enhancement (Priority: HIGH)

| Task | File | Effort |
|------|------|--------|
| Enhance BaseDetailPage with metadata support | `frontend/src/components/common/BaseDetailPage.vue` | 4h |
| Create RelatedObjectTable component | `frontend/src/components/common/RelatedObjectTable.vue` | 3h |
| Update AssetDetail.vue to use enhanced BaseDetailPage | `frontend/src/views/assets/AssetDetail.vue` | 2h |

**Total Phase 3: ~9 hours**

### Phase 4: DynamicForm Updates (Priority: MEDIUM)

| Task | File | Effort |
|------|------|--------|
| Update DynamicForm to use metadata composable | `frontend/src/components/engine/DynamicForm.vue` | 3h |
| Update SubTableField for reverse relation handling | `frontend/src/components/engine/fields/SubTableField.vue` | 2h |

**Total Phase 4: ~5 hours**

### Phase 5: Testing & Documentation (Priority: MEDIUM)

| Task | File | Effort |
|------|------|--------|
| Unit tests for metadata filtering | `backend/apps/system/tests/` | 4h |
| Integration tests for detail page | `frontend/e2e/` | 3h |
| Update PRD documentation | `docs/plans/` | 2h |

**Total Phase 5: ~9 hours**

**Total Estimated Effort: ~39 hours (5 working days)**

---

## 7. Migration Path

### 7.1 Backward Compatibility

**Existing detail pages continue to work:**
- Hardcoded field lists remain functional
- New metadata-driven rendering is opt-in
- Gradual migration path available

### 7.2 Rollout Strategy

1. **Week 1**: Deploy backend changes (non-breaking)
2. **Week 2**: Deploy frontend composables (non-breaking)
3. **Week 3**: Migrate AssetDetail to new architecture
4. **Week 4**: Migrate remaining detail pages
5. **Week 5**: Remove deprecated code

---

## 8. Success Criteria

| Criterion | Measurement |
|-----------|-------------|
| Field Consistency | Edit and detail pages show same field set |
| Reverse Relation Display | Related records visible in detail tabs |
| Zero Hardcoding | All pages use metadata-driven rendering |
| Performance | Metadata API response < 200ms |
| Maintainability | Adding new field requires 0 frontend code changes |

---

## 9. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing detail pages | HIGH | Maintain backward compatibility |
| Performance degradation | MEDIUM | Implement metadata caching |
| Complex migration | MEDIUM | Phased rollout with testing |
| Missing edge cases | LOW | Comprehensive testing plan |

---

## 10. Related Files

### Backend
- `backend/apps/system/models.py` - FieldDefinition, ModelFieldDefinition, PageLayout
- `backend/apps/system/serializers.py` - Metadata serializers
- `backend/apps/system/viewsets/business_object.py` - Field metadata endpoints
- `backend/apps/common/viewsets/base.py` - BaseModelViewSet

### Frontend
- `frontend/src/components/common/BaseDetailPage.vue` - Detail page base component
- `frontend/src/components/engine/DynamicForm.vue` - Form renderer
- `frontend/src/components/common/DynamicTabs.vue` - Tab component
- `frontend/src/composables/useMetadata.ts` - Existing metadata composable
- `frontend/src/api/system.ts` - System API clients

---

## 11. Open Questions

1. **Q:** Should reverse relations be cached?
   **A:** Yes, implement Redis caching for metadata

2. **Q:** How to handle nested reverse relations?
   **A:** Limit to one level for Phase 1, evaluate for Phase 2

3. **Q:** Should we support custom relation display modes?
   **A:** Start with 3 predefined modes, evaluate extensibility later

---

## 12. References

- GZEAMS Architecture Standards (`CLAUDE.md`)
- Field Type Definitions (`backend/apps/system/models.py:183-212`)
- Existing Metadata System (`docs/reports/summaries/`)
- NIIMBOT Hook Fixed Assets (Reference Benchmark)
