# 元数据驱动布局系统 - 统一PRD

## Document Information

| Project | Description |
|---------|-------------|
| PRD Version | v2.0 (Merged) |
| Creation Date | 2025-02-03 |
| Status | Design Review |
| Author | Claude (Architecture Analysis) |
| Merged From | - Unified Field Display Architecture (2025-02-03)<br>- Layout Designer Enhancement (2026-02-03) |

---

## Executive Summary

This PRD merges two related initiatives into a unified **Metadata-Driven Layout System**:

1. **Unified Field Display Architecture** - Solves field inconsistency between detail/edit pages
2. **Layout Designer Enhancement** - Provides WYSIWYG visual layout editing

**Key Decision**: These features must be implemented together because:
- Layout Designer depends on enhanced metadata API
- Both share PageLayout model extensions
- Consistent user experience requires unified approach
- Avoids duplicate work and integration issues

---

## 1. Problem Statement

### 1.1 Core Issues

| Issue | Current State | Impact |
|-------|--------------|--------|
| **Field Inconsistency** | Edit pages show more fields than detail pages | User confusion, data inconsistency |
| **Hardcoded Detail Pages** | Field lists manually defined in components | Maintenance burden, error-prone |
| **No Visual Layout Editor** | Layout configuration requires JSON editing | Poor UX, high learning curve |
| **Reverse Relations** | Not properly handled in any view | Missing related data display |

### 1.2 Example Case: `maintenance_records` Field

```
Maintenance Model ──[related_name='maintenance_records']──> Asset Model
```

| View | Current Behavior | Expected Behavior |
|------|-----------------|-------------------|
| Detail Page | NOT shown (hardcoded fields) | Show as read-only table in tab |
| Edit Page | Shown as editable sub-table | Show as editable inline table |
| List Page | Not applicable | Hidden |

---

## 2. Design Solution

### 2.1 Core Principles

1. **Single Source of Truth**: All field definitions from FieldDefinition metadata
2. **Context-Aware Rendering**: Different displays for form/detail/list contexts
3. **Visual Layout Editing**: WYSIWYG designer for non-technical users
4. **Differential Configuration**: Store only changes from default layout
5. **Zero Hardcoding**: All pages metadata-driven

### 2.2 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Interface Layer                        │
├──────────────────────────────┬──────────────────────────────────────┤
│   LayoutDesigner (Visual)    │      Runtime Rendering               │
│   - Drag & drop fields       │      - BaseDetailPage                │
│   - Configure containers     │      - DynamicForm                   │
│   - Preview changes          │      - BaseListPage                 │
└──────────────────────────────┴──────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Layout Rendering Layer                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Layout Engine (useFieldMetadata)               │   │
│  │  - Merge default + differential configuration             │   │
│  │  - Context-aware field filtering (form/detail/list)        │   │
│  │  - Separate editable fields from reverse relations          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              Container Components                          │   │
│  │  - TabPanel, ColumnLayout, CollapsePanel, Divider         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              RelatedObjectTable (New)                      │   │
│  │  - Display reverse relations as read-only tables          │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Backend API Layer                           │
│  GET /api/system/business-objects/{code}/fields/?context={context} │
│  GET /api/system/page-layouts/?object_code={code}&view_type={type} │
│  POST /api/system/page-layouts/{id}/configure/                    │
└─────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Metadata Storage Layer                         │
│  ┌────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │
│  │BusinessObject  │  │ FieldDefinition  │  │   PageLayout     │    │
│  │ - is_hardcoded │  │ - show_in_form   │  │ - layout_config  │    │
│  │ - model_path   │  │ - show_in_detail │  │ - view_type      │    │
│  │                │  │ - is_reverse_rel │  │ - priority       │    │
│  │                │  │ - relation_mode  │  │ - diff_config    │    │
│  └────────────────┘  └──────────────────┘  └──────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.3 Layout Merge Logic

```
FieldDefinition (实时)
       │
       ▼ 动态生成
┌─────────────────────┐
│   Default Layout    │
│ (所有字段按sort_order)│
└─────────────────────┘
       │
       ▼ 合并
┌─────────────────────────────┐
│  Differential Config        │
│  (用户调整的位置/可见性等)    │
└─────────────────────────────┘
       │
       ▼
┌─────────────────────────────┐
│    Final Rendered Layout   │
└─────────────────────────────┘
```

---

## 3. Backend Changes

### 3.1 FieldDefinition Model Extensions

```python
class FieldDefinition(BaseModel):
    # ... existing fields ...

    # === NEW: Context Display Flags ===
    show_in_form = models.BooleanField(
        default=True,
        db_comment='Show in create/edit forms'
    )

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

    # === NEW: Relation Display Mode ===
    RELATION_DISPLAY_CHOICES = [
        ('inline_editable', 'Inline Editable Table'),   # For edit forms
        ('inline_readonly', 'Inline Read-Only Table'),  # For detail views
        ('tab_readonly', 'Tab Read-Only Table'),       # For detail views
        ('hidden', 'Hidden'),                          # Don't show
    ]
    relation_display_mode = models.CharField(
        max_length=20,
        choices=RELATION_DISPLAY_CHOICES,
        default='tab_readonly',
        db_comment='How to display reverse relations'
    )
```

### 3.2 PageLayout Model Extensions

```python
class PageLayout(BaseModel):
    # ... existing fields ...

    # === NEW: Layout Priority (for override hierarchy) ===
    PRIORITY_CHOICES = [
        ('default', 'Default Layout'),      # Auto-generated from FieldDefinition
        ('global', 'Global Custom'),        # System-wide customization
        ('org', 'Organization Custom'),     # Per-organization
        ('role', 'Role Custom'),            # Per-role
        ('user', 'User Custom'),            # Per-user preference
    ]
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='global',
        db_comment='Layout priority level for override hierarchy'
    )

    # === NEW: Differential Configuration ===
    # Only stores changes from default layout
    diff_config = models.JSONField(
        default=dict,
        blank=True,
        db_comment='''
        Differential configuration (only changes from default):
        {
            "fieldOrder": ["code", "name", "category"],  # Custom order
            "fieldOverrides": {
                "status": { "visible": false },           # Hide field
                "code": { "readonly": true, "span": 12 }  # Override props
            },
            "sections": [
                {
                    "id": "section_basic",
                    "title": "基本信息",
                    "fields": ["code", "name"],
                    "columns": 2
                }
            ],
            "tabs": [
                {
                    "id": "tab_relations",
                    "title": "关联数据",
                    "relations": ["maintenance_records", "pickup_items"]
                }
            ]
        }
        '''
    )

    # === NEW: Context Type ===
    context_type = models.CharField(
        max_length=20,
        choices=[
            ('form', 'Form Layout'),
            ('detail', 'Detail Layout'),
            ('list', 'List Layout'),
        ],
        default='form',
        db_comment='Context this layout applies to'
    )
```

### 3.3 API Endpoints

#### Enhanced Field Metadata Endpoint

```http
GET /api/system/business-objects/{code}/fields/?context={context}&include_relations={bool}
```

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
                "show_in_detail": true,
                "show_in_list": true,
                "sort_order": 1
            }
        ],
        "reverse_relations": [
            {
                "code": "maintenance_records",
                "name": "维保记录",
                "field_type": "sub_table",
                "is_reverse_relation": true,
                "reverse_relation_model": "apps.lifecycle.models.Maintenance",
                "reverse_relation_field": "asset",
                "relation_display_mode": "tab_readonly",
                "related_fields": [...]
            }
        ]
    }
}
```

#### Layout Configuration Endpoint

```http
POST /api/system/page-layouts/save-differential/
```

**Request Body:**

```json
{
    "business_object": "Asset",
    "context_type": "detail",
    "priority": "org",
    "diff_config": {
        "fieldOrder": ["code", "name", "category"],
        "fieldOverrides": {
            "status": { "visible": false }
        },
        "tabs": [...]
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
  sort_order: number
  reverse_relation_model?: string
  reverse_relation_field?: string
  related_fields?: FieldMetadata[]
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
      const response = await businessObjectApi.getFields(objectCode, {
        context,
        include_relations: true
      })
      fields.value = response.data.editable_fields + response.data.reverse_relations
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

### 4.2 Layout Container Components

**Directory Structure:**

```
frontend/src/components/designer/containers/
├── TabPanel.vue          # Tab container
├── ColumnLayout.vue      # Column/row layout
├── CollapsePanel.vue     # Collapsible sections
└── DividerElement.vue    # Visual divider
```

**TabPanel.vue Example:**

```vue
<script setup lang="ts">
import { defineProps, computed } from 'vue'
import { ElTabs, ElTabPane } from 'element-plus'

interface TabConfig {
  id: string
  title: string
  fields?: string[]
  relations?: string[]
  disabled?: boolean
}

const props = defineProps<{
  config: {
    position?: 'top' | 'left' | 'right' | 'bottom'
    type?: 'card' | 'border-card'
    tabs: TabConfig[]
  }
}>()

const tabPosition = computed(() => props.config.position || 'top')
</script>

<template>
  <el-tabs :tab-position="tabPosition" :type="config.type">
    <el-tab-pane
      v-for="tab in config.tabs"
      :key="tab.id"
      :label="tab.title"
      :disabled="tab.disabled"
    >
      <slot :name="tab.id" :tab="tab">
        <!-- Render fields or relations based on tab config -->
      </slot>
    </el-tab-pane>
  </el-tabs>
</template>
```

### 4.3 New Component: RelatedObjectTable

**Location:** `frontend/src/components/common/RelatedObjectTable.vue`

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { createObjectClient } from '@/api/dynamic'
import BaseTable from './BaseTable.vue'

const props = defineProps<{
  relation: {
    code: string
    name: string
    reverse_relation_model: string
    reverse_relation_field: string
    related_fields: any[]
  }
  parentId: string
  readonly?: boolean
}>()

const router = useRouter()
const loading = ref(false)
const data = ref([])

// Extract object code from model path
const relatedObjectCode = computed(() => {
  const parts = props.relation.reverse_relation_model.split('.')
  return parts[parts.length - 1]
})

const api = createObjectClient(relatedObjectCode.value)

async function loadRelatedData() {
  loading.value = true
  try {
    const response = await api.list({
      [props.relation.reverse_relation_field]: props.parentId,
      page_size: 50
    })
    data.value = response.results || []
  } catch (e) {
    console.error('Failed to load related data:', e)
  } finally {
    loading.value = false
  }
}

function viewDetail(record: any) {
  router.push(`/${relatedObjectCode.value}/${record.id}`)
}

onMounted(() => {
  loadRelatedData()
})

// Expose refresh method
defineExpose({ refresh: loadRelatedData })
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
        @click="viewDetail(row)"
      >
        View Details
      </el-button>
    </template>
  </BaseTable>
</template>
```

### 4.4 Enhanced BaseDetailPage

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useFieldMetadata } from '@/composables/useFieldMetadata'
import DynamicTabs from '@/components/common/DynamicTabs.vue'
import RelatedObjectTable from '@/components/common/RelatedObjectTable.vue'
import SectionBlock from '@/components/common/SectionBlock.vue'

const props = defineProps<{
  objectCode: string
  recordId: string
}>()

const { editableFields, reverseRelations, fetchFields } = useFieldMetadata(props.objectCode)

const activeTab = ref('main')
const record = ref(null)
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  await fetchFields('detail')
  // Load record data...
  loading.value = false
})

// Generate tab configuration
const tabConfig = computed(() => {
  const tabs = [{
    name: 'main',
    label: '基本信息',
    type: 'section'
  }]

  // Add relation tabs
  reverseRelations.value.forEach(rel => {
    tabs.push({
      name: rel.code,
      label: rel.name,
      type: 'table',
      readonly: true
    })
  })

  return tabs
})

// Group editable fields by section
const groupedFields = computed(() => {
  // Simple grouping - can be enhanced with layout config
  const basic = editableFields.value.filter(f =>
    ['code', 'name', 'category', 'status'].includes(f.code)
  )
  const detail = editableFields.value.filter(f =>
    !['code', 'name', 'category', 'status'].includes(f.code)
  )
  return { basic, detail }
})
</script>

<template>
  <div class="detail-page" v-loading="loading">
    <DynamicTabs v-model="activeTab" :tabs="tabConfig" type="border-card">
      <!-- Main tab with field sections -->
      <template #main>
        <SectionBlock title="Basic Information" collapsible>
          <div class="field-grid">
            <div v-for="field in groupedFields.basic" :key="field.code" class="field-item">
              <label>{{ field.name }}</label>
              <span>{{ record?.[field.code] || '-' }}</span>
            </div>
          </div>
        </SectionBlock>

        <SectionBlock title="Details" collapsible :collapsed="true">
          <div class="field-grid">
            <div v-for="field in groupedFields.detail" :key="field.code" class="field-item">
              <label>{{ field.name }}</label>
              <span>{{ record?.[field.code] || '-' }}</span>
            </div>
          </div>
        </SectionBlock>
      </template>

      <!-- Relation tabs -->
      <template v-for="rel in reverseRelations" :key="rel.code" #[rel.code]>
        <RelatedObjectTable
          :relation="rel"
          :parent-id="recordId"
          readonly
        />
      </template>
    </DynamicTabs>
  </div>
</template>
```

### 4.5 LayoutDesigner Enhancements

**Key Components:**

```
frontend/src/components/designer/
├── LayoutDesigner.vue          # Main container
├── ComponentPanel.vue          # Field/component palette
├── CanvasArea.vue              # Editing canvas
├── PropertyPanel.vue           # Property editor
├── LayoutPreview.vue           # Live preview
├── containers/                 # Layout containers
│   ├── TabPanel.vue
│   ├── ColumnLayout.vue
│   └── CollapsePanel.vue
└── services/
    └── layoutMerge.ts          # Merge logic for default + diff
```

**CanvasArea Drag & Drop:**

```typescript
// services/layoutMerge.ts
export function mergeLayoutWithDiff(
  defaultFields: FieldMetadata[],
  diffConfig: DifferentialConfig
): MergedLayout {
  const { fieldOrder, fieldOverrides, sections, tabs } = diffConfig

  // Apply custom order, or use default sort_order
  const orderedFields = fieldOrder
    ? sortByOrder(defaultFields, fieldOrder)
    : sortByDefault(defaultFields)

  // Apply field overrides
  const mergedFields = orderedFields.map(field => ({
    ...field,
    ...(fieldOverrides?.[field.code] || {})
  }))

  return {
    fields: mergedFields,
    sections: sections || generateDefaultSections(mergedFields),
    tabs: tabs || generateDefaultTabs(mergedFields)
  }
}
```

---

## 5. Data Flow Diagrams

### 5.1 Detail Page Rendering Flow

```
User navigates to /assets/123
         │
         ▼
BaseDetailPage mounted
         │
         ├──► useFieldMetadata.fetchFields('detail')
         │        │
         │        ▼
         │   Backend: GET /api/system/business-objects/Asset/fields/?context=detail
         │        │
         │        ▼
         │   Returns: {
         │     editable_fields: [...],
         │     reverse_relations: [
         │       { code: "maintenance_records", relation_display_mode: "tab_readonly" }
         │     ]
         │   }
         │
         ├──► Get PageLayout diff_config
         │        │
         │        ▼
         │   Merge: Default Fields + Differential Config
         │
         └──► Render:
                  - Main tab with editable fields (grouped by sections)
                  - One tab per reverse_relation with RelatedObjectTable
```

### 5.2 Layout Designer Flow

```
User opens Layout Designer for Asset
         │
         ▼
LayoutDesigner mounted
         │
         ├──► Fetch FieldDefinition (all fields)
         │        │
         │        ▼
         │   Available fields list (left panel)
         │
         ├──► Fetch existing PageLayout diff_config
         │        │
         │        ▼
         │   Merge with default → Canvas rendering
         │
         └──► User Actions:
                  - Drag field to new position → Update fieldOrder
                  - Toggle field visibility → Update fieldOverrides
                  - Add container → Update sections
                  - Configure tab → Update tabs
                  │
                  ▼
                  POST /api/system/page-layouts/save-differential/
```

---

## 6. Implementation Phases

### Phase 1: Backend Metadata Foundation (2 days)

| Task | File | Effort |
|------|------|--------|
| Add `show_in_form` to FieldDefinition | `backend/apps/system/models.py` | 1h |
| Add reverse relation fields to FieldDefinition | `backend/apps/system/models.py` | 2h |
| Add `relation_display_mode` to FieldDefinition | `backend/apps/system/models.py` | 1h |
| Add PageLayout extensions (priority, diff_config, context_type) | `backend/apps/system/models.py` | 2h |
| Create migration | `backend/apps/system/migrations/` | 1h |
| Update field metadata serializer | `backend/apps/system/serializers.py` | 2h |
| Add context filtering to field endpoint | `backend/apps/system/viewsets/` | 3h |
| Add differential config save endpoint | `backend/apps/system/viewsets/` | 2h |

**Total Phase 1: ~14 hours (2 days)**

### Phase 2: Frontend Metadata & Rendering (3 days)

| Task | File | Effort |
|------|------|--------|
| Create `useFieldMetadata` composable | `frontend/src/composables/useFieldMetadata.ts` | 3h |
| Update businessObjectApi for context parameter | `frontend/src/api/system.ts` | 1h |
| Add TypeScript types for metadata | `frontend/src/types/metadata.ts` | 2h |
| Create RelatedObjectTable component | `frontend/src/components/common/RelatedObjectTable.vue` | 3h |
| Enhance BaseDetailPage with metadata support | `frontend/src/components/common/BaseDetailPage.vue` | 4h |
| Update AssetDetail.vue to use enhanced BaseDetailPage | `frontend/src/views/assets/AssetDetail.vue` | 2h |
| Update DynamicForm for context-aware fields | `frontend/src/components/engine/DynamicForm.vue` | 3h |
| Update SubTableField for reverse relation handling | `frontend/src/components/engine/fields/SubTableField.vue` | 2h |

**Total Phase 2: ~20 hours (3 days)**

### Phase 3: Layout Container Components (2 days)

| Task | File | Effort |
|------|------|--------|
| Create TabPanel container component | `frontend/src/components/designer/containers/TabPanel.vue` | 3h |
| Create ColumnLayout container component | `frontend/src/components/designer/containers/ColumnLayout.vue` | 3h |
| Create CollapsePanel container component | `frontend/src/components/designer/containers/CollapsePanel.vue` | 2h |
| Create DividerElement component | `frontend/src/components/designer/containers/DividerElement.vue` | 1h |
| Create layout merge service | `frontend/src/components/designer/services/layoutMerge.ts` | 3h |
| Create layout schema validation | `frontend/src/components/designer/services/layoutSchema.ts` | 2h |

**Total Phase 3: ~14 hours (2 days)**

### Phase 4: Layout Designer Enhancement (3 days)

| Task | File | Effort |
|------|------|--------|
| Enhance CanvasArea with drag-drop | `frontend/src/components/designer/CanvasArea.vue` | 4h |
| Enhance ComponentPanel for field list | `frontend/src/components/designer/ComponentPanel.vue` | 2h |
| Enhance PropertyPanel for field props | `frontend/src/components/designer/PropertyPanel.vue` | 3h |
| Add LayoutPreview component | `frontend/src/components/designer/LayoutPreview.vue` | 3h |
| Responsive preview support | `frontend/src/components/designer/` | 3h |
| Undo/redo functionality | `frontend/src/components/designer/` | 2h |
| Save/load differential config | `frontend/src/components/designer/` | 2h |

**Total Phase 4: ~19 hours (3 days)**

### Phase 5: Integration & Testing (1.5 days)

| Task | File | Effort |
|------|------|--------|
| Backend unit tests for metadata filtering | `backend/apps/system/tests/` | 3h |
| Frontend integration tests for detail page | `frontend/e2e/` | 2h |
| Layout designer E2E tests | `frontend/e2e/` | 2h |
| Performance testing & optimization | | 2h |
| Documentation updates | `docs/plans/` | 2h |

**Total Phase 5: ~11 hours (1.5 days)**

### Total Estimated Effort

| Phase | Days | Hours |
|-------|------|-------|
| Phase 1: Backend Foundation | 2 | 14 |
| Phase 2: Frontend Rendering | 3 | 20 |
| Phase 3: Container Components | 2 | 14 |
| Phase 4: Layout Designer | 3 | 19 |
| Phase 5: Testing & Docs | 1.5 | 11 |
| **TOTAL** | **11.5** | **78** |

---

## 7. Migration Path

### 7.1 Backward Compatibility Strategy

**Phase 1 - Non-Breaking:**
- Backend model changes are additive (new fields with defaults)
- New API endpoints don't affect existing ones
- Existing hardcoded pages continue to work

**Phase 2 - Opt-In:**
- New composable and components are additions
- Pages can migrate incrementally

**Phase 3 - Gradual Migration:**
- Migrate AssetDetail first as proof of concept
- Then migrate other detail pages
- Finally migrate all forms

**Phase 4 - Cleanup:**
- Remove deprecated hardcoded field lists
- Remove old layout configuration format
- Consolidate to unified system

### 7.2 Rollout Timeline

| Week | Activities |
|------|------------|
| Week 1 | Deploy backend changes (non-breaking) |
| Week 2 | Deploy frontend composables and containers |
| Week 3 | Deploy enhanced BaseDetailPage, migrate AssetDetail |
| Week 4 | Migrate remaining detail pages |
| Week 5 | Deploy enhanced LayoutDesigner |
| Week 6 | Integration testing and cleanup |

---

## 8. Success Criteria

| Criterion | Measurement | Target |
|-----------|-------------|--------|
| Field Consistency | Same fields in detail and edit views | 100% |
| Reverse Relations | Related records visible in detail tabs | All relations shown |
| Zero Hardcoding | Pages use metadata-driven rendering | 0 hardcoded field lists |
| Visual Editing | Layout designer works without JSON editing | Full drag-drop support |
| Performance | Metadata API response time | < 200ms |
| Maintainability | Adding new field requires 0 code changes | 100% |
| Layout Merge | Differential config correctly merged with default | All cases |

---

## 8.1 Detailed Acceptance Checklist

### Phase 1: Backend Metadata Foundation

| ID | Checkpoint | Verification Method | Status |
|----|-----------|-------------------|--------|
| B1.1 | `show_in_form` field added to FieldDefinition model | Migration file exists | ☐ |
| B1.2 | `is_reverse_relation` field added to FieldDefinition model | Migration file exists | ☐ |
| B1.3 | `reverse_relation_model` field added to FieldDefinition model | Migration file exists | ☐ |
| B1.4 | `reverse_relation_field` field added to FieldDefinition model | Migration file exists | ☐ |
| B1.5 | `relation_display_mode` field added to FieldDefinition model | Migration file exists | ☐ |
| B1.6 | PageLayout `priority` field added | Migration file exists | ☐ |
| B1.7 | PageLayout `diff_config` field added | Migration file exists | ☐ |
| B1.8 | PageLayout `context_type` field added | Migration file exists | ☐ |
| B1.9 | Migration runs successfully | `python manage.py migrate` | ☐ |
| B1.10 | Field serializer includes new fields in API response | API test | ☐ |
| B1.11 | Context filtering works (`?context=form/detail/list`) | API test | ☐ |
| B1.12 | Reverse relations separated from editable fields in response | API test | ☐ |
| B1.13 | Differential config save endpoint works | POST test | ☐ |
| B1.14 | Backend unit tests pass | `pytest` | ☐ |

### Phase 2: Frontend Metadata & Rendering

| ID | Checkpoint | Verification Method | Status |
|----|-----------|-------------------|--------|
| F2.1 | `useFieldMetadata` composable created | File exists | ☐ |
| F2.2 | `useFieldMetadata` fetches fields by context | Component test | ☐ |
| F2.3 | `editableFields` computed property filters correctly | Component test | ☐ |
| F2.4 | `reverseRelations` computed property filters correctly | Component test | ☐ |
| F2.5 | TypeScript types defined in `types/metadata.ts` | File exists | ☐ |
| F2.6 | `businessObjectApi.getFields()` accepts context param | API call works | ☐ |
| F2.7 | `RelatedObjectTable` component created | File exists | ☐ |
| F2.8 | `RelatedObjectTable` loads related data correctly | E2E test | ☐ |
| F2.9 | `RelatedObjectTable` displays read-only table | Visual test | ☐ |
| F2.10 | `RelatedObjectTable` "View Details" button navigates correctly | E2E test | ☐ |
| F2.11 | `BaseDetailPage` enhanced with metadata support | Component works | ☐ |
| F2.12 | Detail page shows editable fields in main tab | Visual test | ☐ |
| F2.13 | Detail page shows relation tabs | Visual test | ☐ |
| F2.14 | AssetDetail.vue uses enhanced BaseDetailPage | Code review | ☐ |
| F2.15 | `DynamicForm` uses context-aware field loading | Form renders correctly | ☐ |
| F2.16 | `SubTableField` handles reverse relations | Inline table works | ☐ |
| F2.17 | Edit and detail pages show same field set | Comparison test | ☐ |

### Phase 3: Layout Container Components

| ID | Checkpoint | Verification Method | Status |
|----|-----------|-------------------|--------|
| F3.1 | `TabPanel.vue` container component created | File exists | ☐ |
| F3.2 | TabPanel renders tabs from config | Visual test | ☐ |
| F3.3 | TabPanel position prop works (top/left/right/bottom) | Visual test | ☐ |
| F3.4 | `ColumnLayout.vue` component created | File exists | ☐ |
| F3.5 | ColumnLayout renders correct column spans | Visual test | ☐ |
| F3.6 | `CollapsePanel.vue` component created | File exists | ☐ |
| F3.7 | CollapsePanel collapse/expand works | Interaction test | ☐ |
| F3.8 | `DividerElement.vue` component created | File exists | ☐ |
| F3.9 | Divider renders with correct position | Visual test | ☐ |
| F3.10 | `layoutMerge.ts` service created | File exists | ☐ |
| F3.11 | Merge logic applies custom field order | Unit test | ☐ |
| F3.12 | Merge logic applies field overrides | Unit test | ☐ |
| F3.13 | Merge logic generates default sections when missing | Unit test | ☐ |
| F3.14 | `layoutSchema.ts` validation created | File exists | ☐ |
| F3.15 | Schema validation catches invalid configs | Unit test | ☐ |

### Phase 4: Layout Designer Enhancement

| ID | Checkpoint | Verification Method | Status |
|----|-----------|-------------------|--------|
| F4.1 | CanvasArea drag-drop implemented | Interaction test | ☐ |
| F4.2 | Fields can be dragged to new position | E2E test | ☐ |
| F4.3 | Fields can be dragged into containers | E2E test | ☐ |
| F4.4 | ComponentPanel shows all available fields | Visual test | ☐ |
| F4.5 | ComponentPanel auto-syncs with FieldDefinition | Add field test | ☐ |
| F4.6 | PropertyPanel shows field properties | Visual test | ☐ |
| F4.7 | PropertyPanel allows editing visible/readonly/required | Interaction test | ☐ |
| F4.8 | PropertyPanel changes update canvas | Interaction test | ☐ |
| F4.9 | LayoutPreview component created | File exists | ☐ |
| F4.10 | Preview updates in real-time | Interaction test | ☐ |
| F4.11 | Responsive preview (desktop/tablet/mobile) | Visual test | ☐ |
| F4.12 | Undo functionality works | Interaction test | ☐ |
| F4.13 | Redo functionality works | Interaction test | ☐ |
| F4.14 | Save differential config works | API call succeeds | ☐ |
| F4.15 | Load differential config works | Canvas loads saved state | ☐ |
| F4.16 | New fields appear automatically after sync | Add field test | ☐ |

### Phase 5: Integration & Testing

| ID | Checkpoint | Verification Method | Status |
|----|-----------|-------------------|--------|
| I5.1 | Backend unit tests for metadata filtering | `pytest --cov` | ☐ |
| I5.2 | Backend tests cover all new model fields | Coverage >80% | ☐ |
| I5.3 | Frontend integration test for detail page | Playwright test | ☐ |
| I5.4 | Frontend integration test for edit page | Playwright test | ☐ |
| I5.5 | E2E test for layout designer save/load | Playwright test | ☐ |
| I5.6 | E2E test for field visibility toggle | Playwright test | ☐ |
| I5.7 | Performance test: metadata API <200ms | Load test | ☐ |
| I5.8 | Performance test: detail page load <1s | Load test | ☐ |
| I5.9 | Documentation updated | Docs reviewed | ☐ |
| I5.10 | Migration guide exists | Docs reviewed | ☐ |

### Cross-Cutting Concerns

| ID | Checkpoint | Verification Method | Status |
|----|-----------|-------------------|--------|
| X1 | No hardcoded field lists remain | Code scan | ☐ |
| X2 | All pages use metadata-driven rendering | Code review | ☐ |
| X3 | Backward compatibility maintained | Legacy pages work | ☐ |
| X4 | Error handling works for failed API calls | Error test | ☐ |
| X5 | Loading states display correctly | Visual test | ☐ |
| X6 | Empty states display correctly | Visual test | ☐ |
| X7 | English comments only (code standard) | Code review | ☐ |
| X8 | BaseModel inheritance followed | Code review | ☐ |
| X9 | No SQL injection vulnerabilities | Security scan | ☐ |
| X10 | No XSS vulnerabilities | Security scan | ☐ |

### Pre-Release Checklist

| ID | Checkpoint | Verification Method | Status |
|----|-----------|-------------------|--------|
| P1 | All Phase 1-5 tasks completed | Task list review | ☐ |
| P2 | All acceptance checkboxes checked | Checklist review | ☐ |
| P3 | No critical bugs outstanding | Bug triage | ☐ |
| P4 | Performance benchmarks met | Load test | ☐ |
| P5 | Security review passed | Security scan | ☐ |
| P6 | Documentation complete | Docs review | ☐ |
| P7 | Rollback plan tested | Rollback test | ☐ |
| P8 | Stakeholder approval obtained | Sign-off | ☐ |

---

## 9. Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Breaking existing pages | HIGH | LOW | Maintain backward compatibility, opt-in migration |
| Performance degradation | MEDIUM | LOW | Implement caching, lazy loading |
| Layout merge conflicts | MEDIUM | MEDIUM | Comprehensive testing, fallback to default |
| Designer complexity | MEDIUM | HIGH | Phased rollout, user training |
| Data loss during migration | HIGH | LOW | Backup before migration, rollback plan |

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
- `frontend/src/components/designer/LayoutDesigner.vue` - Visual designer
- `frontend/src/composables/useMetadata.ts` - Existing metadata composable
- `frontend/src/api/system.ts` - System API clients

---

## 11. Open Questions

1. **Q:** Should differential config support nested overrides (role > org > global)?
   **A:** Start with simple priority field, evaluate nested complexity for Phase 2

2. **Q:** How to handle conflicts when multiple users edit same layout?
   **A:** Implement optimistic locking with version field on PageLayout

3. **Q:** Should we support layout templates?
   **A:** Add in Phase 2 - allow copying layouts between objects

4. **Q:** How to handle mobile responsiveness?
   **A:** Use Element Plus grid system, add responsive breakpoints in Phase 4

---

## 12. References

- GZEAMS Architecture Standards (`CLAUDE.md`)
- Field Type Definitions (`backend/apps/system/models.py:183-212`)
- Existing Metadata System (`docs/reports/summaries/`)
- NIIMBOT Hook Fixed Assets (Reference Benchmark)
- Original PRDs:
  - `docs/plans/2025-02-03-unified-field-display-design.md`
  - `docs/plans/2026-02-03-layout-designer-enhancement.md`
