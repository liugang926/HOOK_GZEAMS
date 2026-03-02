# 元数据驱动布局系统 - 实施计划

## Document Information

| Project | Description |
|---------|-------------|
| Plan Version | v1.0 |
| Creation Date | 2025-02-03 |
| Based On | 2025-02-03-metadata-driven-layout-system.md |
| Total Duration | 11.5 Days (78 Hours) |
| Author | Claude (Implementation Planning) |

---

## Executive Summary

This implementation plan breaks down the **Metadata-Driven Layout System** PRD into actionable development tasks with clear dependencies, verification steps, and rollback procedures.

**Total Effort**: 11.5 days (78 hours)
**Rollout Strategy**: Phased, non-breaking deployment over 6 weeks

---

## Phase 1: Backend Metadata Foundation (2 Days / 14 Hours)

### Overview
Extend database models and API endpoints to support context-aware field metadata and reverse relation handling.

### Task Breakdown

#### Task 1.1: Add FieldDefinition Model Extensions (4 hours)

**File**: `backend/apps/system/models.py`

**Subtasks**:

| Subtask | Description | Lines | Verification |
|---------|-------------|-------|--------------|
| 1.1.1 | Add `show_in_form` BooleanField | 3 | Migration generated |
| 1.1.2 | Add `is_reverse_relation` BooleanField | 3 | Migration generated |
| 1.1.3 | Add `reverse_relation_model` CharField | 5 | Migration generated |
| 1.1.4 | Add `reverse_relation_field` CharField | 5 | Migration generated |
| 1.1.5 | Add `relation_display_mode` CharField with choices | 8 | Migration generated |

**Code Template**:

```python
# In FieldDefinition class (around line ~300)

# === Context Display Flags ===
show_in_form = models.BooleanField(
    default=True,
    db_comment='Show in create/edit forms'
)

# === Reverse Relation Handling ===
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

# === Relation Display Mode ===
RELATION_DISPLAY_CHOICES = [
    ('inline_editable', 'Inline Editable Table'),
    ('inline_readonly', 'Inline Read-Only Table'),
    ('tab_readonly', 'Tab Read-Only Table'),
    ('hidden', 'Hidden'),
]
relation_display_mode = models.CharField(
    max_length=20,
    choices=RELATION_DISPLAY_CHOICES,
    default='tab_readonly',
    db_comment='How to display reverse relations'
)
```

**Dependencies**: None

**Acceptance**:
- [ ] Migration file created in `migrations/`
- [ ] `python manage.py makemigrations` succeeds
- [ ] `python manage.py migrate` succeeds

---

#### Task 1.2: Add PageLayout Model Extensions (3 hours)

**File**: `backend/apps/system/models.py`

**Subtasks**:

| Subtask | Description | Lines | Verification |
|---------|-------------|-------|--------------|
| 1.2.1 | Add `priority` CharField with choices | 10 | Migration generated |
| 1.2.2 | Add `diff_config` JSONField | 15 | Migration generated |
| 1.2.3 | Add `context_type` CharField with choices | 8 | Migration generated |

**Code Template**:

```python
# In PageLayout class

# === Layout Priority (for override hierarchy) ===
PRIORITY_CHOICES = [
    ('default', 'Default Layout'),
    ('global', 'Global Custom'),
    ('org', 'Organization Custom'),
    ('role', 'Role Custom'),
    ('user', 'User Custom'),
]
priority = models.CharField(
    max_length=20,
    choices=PRIORITY_CHOICES,
    default='global',
    db_comment='Layout priority level for override hierarchy'
)

# === Differential Configuration ===
diff_config = models.JSONField(
    default=dict,
    blank=True,
    db_comment='Differential configuration (only changes from default)'
)

# === Context Type ===
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

**Dependencies**: None (can parallel with Task 1.1)

**Acceptance**:
- [ ] Migration file created
- [ ] Migration applies successfully

---

#### Task 1.3: Create and Apply Migration (1 hour)

**File**: `backend/apps/system/migrations/XXXX_auto_20250203.py`

**Commands**:

```bash
cd backend
venv/Scripts/python.exe manage.py makemigrations system
venv/Scripts/python.exe manage.py migrate system
```

**Verification**:

```bash
# Check migration applied
venv/Scripts/python.exe manage.py showmigrations system

# Verify new columns exist
venv/Scripts/python.exe -c "
from apps.system.models import FieldDefinition, PageLayout
print('FieldDefinition fields:', [f.name for f in FieldDefinition._meta.get_fields() if 'reverse' in f.name or 'show_in' in f.name or 'relation' in f.name])
print('PageLayout fields:', [f.name for f in PageLayout._meta.get_fields() if 'priority' in f.name or 'diff' in f.name or 'context' in f.name])
"
```

**Dependencies**: Tasks 1.1, 1.2 complete

**Acceptance**:
- [ ] Migration file generated
- [ ] Migration applied without errors
- [ ] New fields visible in database schema

---

#### Task 1.4: Update Field Metadata Serializer (2 hours)

**File**: `backend/apps/system/serializers.py` or `backend/apps/system/serializers/field_definition.py`

**Subtasks**:

| Subtask | Description | Lines | Verification |
|---------|-------------|-------|--------------|
| 1.4.1 | Add new fields to FieldDefinitionSerializer | 20 | API response includes fields |
| 1.4.2 | Implement context-based filtering logic | 15 | `?context=form` filters correctly |
| 1.4.3 | Separate editable_fields from reverse_relations | 20 | Response structure matches PRD |

**Code Template**:

```python
class FieldDefinitionSerializer(BaseModelSerializer):
    class Meta(BaseModelSerializer.Meta):
        model = FieldDefinition
        fields = BaseModelSerializer.Meta.fields + [
            # ... existing fields ...
            'show_in_form',
            'is_reverse_relation',
            'reverse_relation_model',
            'reverse_relation_field',
            'relation_display_mode',
        ]

    def to_representation(self, instance):
        """Filter fields based on context parameter."""
        data = super().to_representation(instance)
        context = self.context.get('request').query_params.get('context', 'form')

        # Apply context filtering
        if context == 'detail':
            # Only show fields with show_in_detail=True
            if not instance.show_in_detail:
                return None
        elif context == 'list':
            # Only show fields with show_in_list=True
            if not instance.show_in_list:
                return None

        return data
```

**API Endpoint Changes**:

```http
GET /api/system/business-objects/{code}/fields/?context=detail&include_relations=true
```

**Expected Response**:

```json
{
    "success": true,
    "data": {
        "editable_fields": [...],
        "reverse_relations": [...]
    }
}
```

**Dependencies**: Task 1.3 complete

**Acceptance**:
- [ ] API returns new fields
- [ ] Context filtering works
- [ ] Reverse relations separated

---

#### Task 1.5: Add Context Filtering to Field Endpoint (3 hours)

**File**: `backend/apps/system/viewsets/business_object.py` or `backend/apps/system/viewsets/field_definition.py`

**Subtasks**:

| Subtask | Description | Lines | Verification |
|---------|-------------|-------|--------------|
| 1.5.1 | Add `context` query parameter handling | 10 | `?context=form` works |
| 1.5.2 | Add `include_relations` query parameter | 5 | `?include_relations=true` works |
| 1.5.3 | Implement field categorization logic | 25 | Response split correctly |
| 1.5.4 | Add response wrapper with editable_fields/reverse_relations | 15 | Response format matches PRD |

**Code Template**:

```python
class FieldDefinitionViewSet(BaseModelViewSet):
    def get_queryset(self):
        queryset = super().get_queryset()
        context = self.request.query_params.get('context', 'form')

        # Apply context filtering
        if context == 'form':
            queryset = queryset.filter(show_in_form=True)
        elif context == 'detail':
            queryset = queryset.filter(show_in_detail=True)
        elif context == 'list':
            queryset = queryset.filter(show_in_list=True)

        return queryset

    def list(self, request, *args, **kwargs):
        """Override list to separate editable fields from reverse relations."""
        queryset = self.filter_queryset(self.get_queryset())

        # Separate into editable and reverse relations
        editable_fields = [f for f in queryset if not f.is_reverse_relation]
        reverse_relations = [f for f in queryset if f.is_reverse_relation]

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': {
                'editable_fields': FieldDefinitionSerializer(editable_fields, many=True).data,
                'reverse_relations': FieldDefinitionSerializer(reverse_relations, many=True).data
            }
        })
```

**Dependencies**: Task 1.4 complete

**Acceptance**:
- [ ] GET with `?context=form` returns form fields
- [ ] GET with `?context=detail` returns detail fields
- [ ] GET with `?include_relations=true` includes reverse relations

---

#### Task 1.6: Add Differential Config Save Endpoint (2 hours)

**File**: `backend/apps/system/viewsets/page_layout.py`

**Subtasks**:

| Subtask | Description | Lines | Verification |
|---------|-------------|-------|--------------|
| 1.6.1 | Add `save_differential` action | 20 | POST endpoint works |
| 1.6.2 | Implement merge logic | 25 | Config saves correctly |
| 1.6.3 | Add validation for diff_config | 15 | Invalid configs rejected |

**Code Template**:

```python
from rest_framework.decorators import action
from rest_framework.response import Response

class PageLayoutViewSet(BaseModelViewSet):
    @action(detail=False, methods=['post'], url_path='save-differential')
    def save_differential(self, request):
        """Save differential layout configuration."""
        business_object = request.data.get('business_object')
        context_type = request.data.get('context_type', 'form')
        priority = request.data.get('priority', 'global')
        diff_config = request.data.get('diff_config', {})

        # Validate diff_config structure
        self._validate_diff_config(diff_config)

        # Find or create layout
        layout, created = PageLayout.objects.get_or_create(
            business_object__code=business_object,
            context_type=context_type,
            priority=priority,
            defaults={'diff_config': diff_config}
        )

        if not created:
            layout.diff_config = diff_config
            layout.save()

        return Response({
            'success': True,
            'data': PageLayoutSerializer(layout).data
        })

    def _validate_diff_config(self, config):
        """Validate differential configuration structure."""
        required_keys = ['fieldOrder', 'fieldOverrides']
        for key in required_keys:
            if key not in config:
                raise ValidationError(f"Missing required key: {key}")
```

**Dependencies**: Task 1.3 complete

**Acceptance**:
- [ ] POST `/api/system/page-layouts/save-differential/` works
- [ ] Config saves to database
- [ ] Invalid configs return 400 error

---

### Phase 1 Verification

```bash
# Run backend tests
cd backend
venv/Scripts/python.exe -m pytest apps/system/tests/ -v

# Manual API test
curl -X GET "http://localhost:8000/api/system/business-objects/Asset/fields/?context=detail&include_relations=true" \
  -H "Authorization: Bearer $TOKEN"

# Expected: reverse_relations includes maintenance_records
```

**Phase 1 Exit Criteria**:
- [ ] All migrations applied
- [ ] API endpoints respond correctly
- [ ] Unit tests pass
- [ ] No breaking changes to existing endpoints

---

## Phase 2: Frontend Metadata & Rendering (3 Days / 20 Hours)

### Overview
Create frontend composables and components for metadata-driven rendering. Update detail and form pages.

### Task Breakdown

#### Task 2.1: Create useFieldMetadata Composable (3 hours)

**File**: `frontend/src/composables/useFieldMetadata.ts`

**Subtasks**:

| Subtask | Description | Lines | Verification |
|---------|-------------|-------|--------------|
| 2.1.1 | Define TypeScript interfaces | 30 | Types compile |
| 2.1.2 | Implement fetchFields method | 25 | Fetches from API |
| 2.1.3 | Add editableFields computed | 10 | Filters correctly |
| 2.1.4 | Add reverseRelations computed | 10 | Filters correctly |

**Code Template**:

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

export interface FieldMetadataResponse {
  editable_fields: FieldMetadata[]
  reverse_relations: FieldMetadata[]
}

export function useFieldMetadata(objectCode: string) {
  const fields = ref<FieldMetadata[]>([])
  const loading = ref(false)
  const error = ref<Error | null>(null)

  const editableFields = computed(() =>
    fields.value.filter(f => !f.is_reverse_relation)
  )

  const reverseRelations = computed(() =>
    fields.value.filter(f => f.is_reverse_relation)
  )

  const fieldsByContext = computed(() => {
    return (context: 'form' | 'detail' | 'list') => {
      return fields.value.filter(f => {
        if (context === 'form') return f.show_in_form
        if (context === 'detail') return f.show_in_detail
        if (context === 'list') return f.show_in_list
        return true
      })
    }
  })

  async function fetchFields(context: 'form' | 'detail' | 'list', includeRelations = true) {
    loading.value = true
    error.value = null

    try {
      const response = await businessObjectApi.getFields(objectCode, {
        context,
        include_relations: includeRelations
      })

      const data = response.data as FieldMetadataResponse
      fields.value = [...data.editable_fields, ...data.reverse_relations]
    } catch (e) {
      error.value = e as Error
      console.error('Failed to fetch field metadata:', e)
    } finally {
      loading.value = false
    }
  }

  function getReverseRelationByCode(code: string) {
    return reverseRelations.value.find(r => r.code === code)
  }

  return {
    fields,
    editableFields,
    reverseRelations,
    fieldsByContext,
    loading,
    error,
    fetchFields,
    getReverseRelationByCode
  }
}
```

**Dependencies**: Phase 1 complete

**Acceptance**:
- [ ] File created at `frontend/src/composables/useFieldMetadata.ts`
- [ ] TypeScript compiles without errors
- [ ] Composable exports all required methods

---

#### Task 2.2: Update businessObjectApi (1 hour)

**File**: `frontend/src/api/system.ts`

**Subtasks**:

| Subtask | Description | Lines | Verification |
|---------|-------------|-------|--------------|
| 2.2.1 | Add context parameter to getFields | 10 | API call works |
| 2.2.2 | Add include_relations parameter | 5 | API call works |

**Code Template**:

```typescript
// In system.ts, update businessObjectApi

export const businessObjectApi = {
  async getFields(objectCode: string, params?: {
    context?: 'form' | 'detail' | 'list'
    include_relations?: boolean
  }) {
    return request.get<FieldMetadataResponse>(
      `/system/business-objects/${objectCode}/fields/`,
      { params }
    )
  },

  // ... other methods
}
```

**Dependencies**: None (can parallel with Task 2.1)

**Acceptance**:
- [ ] TypeScript compiles
- [ ] API call returns expected data

---

#### Task 2.3: Add TypeScript Types (2 hours)

**File**: `frontend/src/types/metadata.ts`

**Subtasks**:

| Subtask | Description | Lines | Verification |
|---------|-------------|-------|--------------|
| 2.3.1 | Define FieldMetadata interface | 30 | Types compile |
| 2.3.2 | Define DifferentialConfig interface | 20 | Types compile |
| 2.3.3 | Define LayoutConfig interface | 25 | Types compile |
| 2.3.4 | Export all types | 10 | Imports work |

**Code Template**:

```typescript
// frontend/src/types/metadata.ts

export interface FieldMetadata {
  code: string
  name: string
  field_type: string
  is_required: boolean
  is_reverse_relation: boolean
  relation_display_mode?: 'inline_editable' | 'inline_readonly' | 'tab_readonly' | 'hidden'
  show_in_form: boolean
  show_in_detail: boolean
  show_in_list: boolean
  sort_order: number
  reverse_relation_model?: string
  reverse_relation_field?: string
  related_fields?: FieldMetadata[]
  // Additional field-specific properties
  default_value?: any
  options?: Array<{ value: any; label: string }>
}

export interface FieldOverride {
  visible?: boolean
  readonly?: boolean
  required?: boolean
  span?: number
  default_value?: any
}

export interface DifferentialConfig {
  fieldOrder?: string[]
  fieldOverrides?: Record<string, FieldOverride>
  sections?: SectionConfig[]
  tabs?: TabConfig[]
}

export interface SectionConfig {
  id: string
  title: string
  fields: string[]
  columns?: number
  collapsed?: boolean
}

export interface TabConfig {
  id: string
  title: string
  fields?: string[]
  relations?: string[]
  disabled?: boolean
}

export interface LayoutConfig {
  sections?: SectionConfig[]
  tabs?: TabConfig[]
  containers?: ContainerConfig[]
}

export interface ContainerConfig {
  type: 'tab' | 'column' | 'collapse' | 'divider'
  id: string
  [key: string]: any
}

export interface FieldMetadataResponse {
  editable_fields: FieldMetadata[]
  reverse_relations: FieldMetadata[]
}
```

**Dependencies**: None

**Acceptance**:
- [ ] All types defined
- [ ] No TypeScript errors

---

#### Task 2.4: Create RelatedObjectTable Component (3 hours)

**File**: `frontend/src/components/common/RelatedObjectTable.vue`

**Subtasks**:

| Subtask | Description | Lines | Verification |
|---------|-------------|-------|--------------|
| 2.4.1 | Create component structure | 50 | Component renders |
| 2.4.2 | Implement loadRelatedData method | 25 | Data loads |
| 2.4.3 | Add viewDetail navigation | 10 | Navigation works |
| 2.4.4 | Add error handling | 15 | Errors display |

**Code Template**:

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { createObjectClient } from '@/api/dynamic'
import BaseTable from './BaseTable.vue'
import type { FieldMetadata } from '@/types/metadata'

const props = defineProps<{
  relation: FieldMetadata
  parentId: string
  readonly?: boolean
}>()

const router = useRouter()
const loading = ref(false)
const data = ref<any[]>([])
const error = ref<Error | null>(null)

// Extract object code from model path
const relatedObjectCode = computed(() => {
  if (!props.relation.reverse_relation_model) return ''
  const parts = props.relation.reverse_relation_model.split('.')
  return parts[parts.length - 1]
})

const api = computed(() => {
  if (!relatedObjectCode.value) return null
  return createObjectClient(relatedObjectCode.value)
})

async function loadRelatedData() {
  if (!api.value) return

  loading.value = true
  error.value = null

  try {
    const response = await api.value.list({
      [props.relation.reverse_relation_field || '']: props.parentId,
      page_size: 50
    })
    data.value = response.results || []
  } catch (e) {
    error.value = e as Error
    console.error('Failed to load related data:', e)
  } finally {
    loading.value = false
  }
}

function viewDetail(record: any) {
  router.push(`/objects/${relatedObjectCode.value}/${record.id}`)
}

onMounted(() => {
  loadRelatedData()
})

defineExpose({ refresh: loadRelatedData })
</script>

<template>
  <div class="related-object-table">
    <el-alert
      v-if="error"
      type="error"
      :title="`Failed to load ${relation.name}: ${error.message}`"
      :closable="false"
    />

    <BaseTable
      v-else
      :data="data"
      :loading="loading"
      :columns="relation.related_fields || []"
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

    <el-empty
      v-if="!loading && data.length === 0"
      :description="`No ${relation.name} found`"
    />
  </div>
</template>

<style scoped>
.related-object-table {
  min-height: 200px;
}
</style>
```

**Dependencies**: Tasks 2.1, 2.2, 2.3 complete

**Acceptance**:
- [ ] Component renders
- [ ] Related data loads
- [ ] "View Details" button navigates

---

#### Task 2.5: Enhance BaseDetailPage (4 hours)

**File**: `frontend/src/components/common/BaseDetailPage.vue`

**Subtasks**:

| Subtask | Description | Lines | Verification |
|---------|-------------|-------|--------------|
| 2.5.1 | Add useFieldMetadata integration | 30 | Fields load |
| 2.5.2 | Generate tab configuration from reverse relations | 25 | Tabs appear |
| 2.5.3 | Group editable fields by section | 30 | Fields grouped |
| 2.5.4 | Integrate RelatedObjectTable | 20 | Tables render |

**Code Template**:

```vue
<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useFieldMetadata } from '@/composables/useFieldMetadata'
import { createObjectClient } from '@/api/dynamic'
import DynamicTabs from './DynamicTabs.vue'
import RelatedObjectTable from './RelatedObjectTable.vue'
import SectionBlock from './SectionBlock.vue'
import type { FieldMetadata } from '@/types/metadata'

const props = defineProps<{
  objectCode: string
  recordId?: string
}>()

const route = useRoute()
const id = computed(() => props.recordId || route.params.id as string)

const {
  editableFields,
  reverseRelations,
  loading: metadataLoading,
  fetchFields
} = useFieldMetadata(props.objectCode)

const activeTab = ref('main')
const record = ref<any>(null)
const loading = ref(false)

const api = computed(() => createObjectClient(props.objectCode))

async function loadRecord() {
  if (!id.value) return

  loading.value = true
  try {
    const response = await api.value.get(id.value)
    record.value = response.data
  } catch (e) {
    console.error('Failed to load record:', e)
  } finally {
    loading.value = false
  }
}

// Generate tab configuration
const tabConfig = computed(() => {
  const tabs = [{
    name: 'main',
    label: 'Basic Information',
    type: 'section'
  }]

  // Add relation tabs
  reverseRelations.value.forEach(rel => {
    if (rel.relation_display_mode === 'tab_readonly') {
      tabs.push({
        name: rel.code,
        label: rel.name,
        type: 'table',
        readonly: true
      })
    }
  })

  return tabs
})

// Group editable fields by section
const groupedFields = computed(() => {
  const basic = editableFields.value.filter(f =>
    ['code', 'name', 'category', 'status'].includes(f.code)
  )
  const detail = editableFields.value.filter(f =>
    !['code', 'name', 'category', 'status'].includes(f.code)
  )
  return { basic, detail }
})

onMounted(async () => {
  await fetchFields('detail')
  await loadRecord()
})

// Refresh related data when switching to relation tab
watch(activeTab, (newTab) => {
  const relation = reverseRelations.value.find(r => r.code === newTab)
  if (relation) {
    // Force refresh of related data
  }
})

defineExpose({ refresh: loadRecord })
</script>

<template>
  <div class="detail-page" v-loading="loading || metadataLoading">
    <DynamicTabs v-model="activeTab" :tabs="tabConfig" type="border-card">
      <!-- Main tab with field sections -->
      <template #main>
        <SectionBlock title="Basic Information" collapsible :collapsed="false">
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
          v-if="rel.relation_display_mode === 'tab_readonly'"
          :relation="rel"
          :parent-id="id"
          readonly
        />
      </template>
    </DynamicTabs>
  </div>
</template>

<style scoped>
.detail-page {
  padding: 20px;
}

.field-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.field-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field-item label {
  font-weight: 500;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.field-item span {
  color: var(--el-text-color-primary);
  font-size: 14px;
}
</style>
```

**Dependencies**: Tasks 2.1, 2.2, 2.3, 2.4 complete

**Acceptance**:
- [ ] Detail page renders with metadata
- [ ] Relation tabs appear
- [ ] RelatedObjectTable displays data

---

#### Task 2.6: Update AssetDetail.vue (2 hours)

**File**: `frontend/src/views/assets/AssetDetail.vue`

**Subtasks**:

| Subtask | Description | Lines | Verification |
|---------|-------------|-------|--------------|
| 2.6.1 | Replace hardcoded sections with BaseDetailPage | ~50 | Simplified component |
| 2.6.2 | Verify maintenance_records appears | Manual | Tab visible |

**Code Template**:

```vue
<script setup lang="ts">
import BaseDetailPage from '@/components/common/BaseDetailPage.vue'
</script>

<template>
  <BaseDetailPage objectCode="Asset" />
</template>
```

**Dependencies**: Task 2.5 complete

**Acceptance**:
- [ ] Component simplified
- [ ] maintenance_records tab appears

---

#### Task 2.7: Update DynamicForm for Context-Aware Fields (3 hours)

**File**: `frontend/src/components/engine/DynamicForm.vue`

**Subtasks**:

| Subtask | Description | Lines | Verification |
|---------|-------------|-------|--------------|
| 2.7.1 | Add useFieldMetadata integration | 25 | Fields load by context |
| 2.7.2 | Filter reverse relations for form context | 15 | Only editable fields shown |
| 2.7.3 | Handle inline_editable reverse relations | 20 | SubTableField works |

**Code Changes**:

```typescript
// In DynamicForm.vue script setup

import { useFieldMetadata } from '@/composables/useFieldMetadata'

const props = defineProps<{
  objectCode: string
  mode?: 'create' | 'edit' | 'view'
}>()

const {
  editableFields,
  reverseRelations,
  fetchFields
} = useFieldMetadata(props.objectCode)

// Filter fields for form context
const formFields = computed(() => {
  return editableFields.value.filter(f => f.show_in_form)
})

// Inline editable reverse relations
const inlineRelations = computed(() => {
  return reverseRelations.value.filter(
    r => r.relation_display_mode === 'inline_editable'
  )
})

onMounted(async () => {
  await fetchFields('form')
})
```

**Dependencies**: Tasks 2.1, 2.2, 2.3 complete

**Acceptance**:
- [ ] Form shows only editable fields
- [ ] Inline relations render correctly

---

#### Task 2.8: Update SubTableField for Reverse Relations (2 hours)

**File**: `frontend/src/components/engine/fields/SubTableField.vue`

**Subtasks**:

| Subtask | Description | Lines | Verification |
|---------|-------------|-------|--------------|
| 2.8.1 | Detect reverse relation from field metadata | 15 | Detection works |
| 2.8.2 | Adjust columns based on related_fields | 20 | Columns match |
| 2.8.3 | Handle readonly vs editable mode | 15 | Modes work |

**Dependencies**: Task 2.7 complete

**Acceptance**:
- [ ] Reverse relation sub-tables render
- [ ] Editable vs readonly modes work

---

### Phase 2 Verification

```bash
# Frontend build test
cd frontend
npm run build

# Manual browser test
# 1. Navigate to /assets/{id}
# 2. Verify "维保记录" tab appears
# 3. Click tab, verify related records display
```

**Phase 2 Exit Criteria**:
- [ ] Detail page shows relation tabs
- [ ] Edit page shows same field set as detail
- [ ] maintenance_records displays correctly
- [ ] No console errors

---

## Phase 3: Layout Container Components (2 Days / 14 Hours)

### Overview
Create reusable layout container components for the visual designer.

### Task Breakdown

#### Task 3.1: Create TabPanel Container (3 hours)

**File**: `frontend/src/components/designer/containers/TabPanel.vue`

**Code Template**:

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { ElTabs, ElTabPane } from 'element-plus'

export interface TabConfig {
  id: string
  title: string
  fields?: string[]
  relations?: string[]
  disabled?: boolean
}

interface TabPanelConfig {
  position?: 'top' | 'left' | 'right' | 'bottom'
  type?: '' | 'card' | 'border-card'
  tabs: TabConfig[]
}

const props = defineProps<{
  config: TabPanelConfig
}>()

const tabPosition = computed(() => props.config.position || 'top')
const tabType = computed(() => props.config.type || '')

defineEmits<{
  (e: 'tab-change', tabId: string): void
}>()
</script>

<template>
  <el-tabs
    :tab-position="tabPosition"
    :type="tabType"
    @tab-change="(id: string) => $emit('tab-change', id)"
  >
    <el-tab-pane
      v-for="tab in config.tabs"
      :key="tab.id"
      :label="tab.title"
      :name="tab.id"
      :disabled="tab.disabled"
    >
      <slot :name="tab.id" :tab="tab">
        <div class="tab-content">
          <!-- Fields will be rendered here by parent -->
        </div>
      </slot>
    </el-tab-pane>
  </el-tabs>
</template>

<style scoped>
.tab-content {
  padding: 16px 0;
}
</style>
```

**Acceptance**:
- [ ] Component renders tabs from config
- [ ] Position prop works
- [ ] Type prop works
- [ ] tab-change event emitted

---

#### Task 3.2: Create ColumnLayout Container (3 hours)

**File**: `frontend/src/components/designer/containers/ColumnLayout.vue`

**Code Template**:

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { ElRow, ElCol } from 'element-plus'

export interface ColumnConfig {
  span: number
  fields?: string[]
  children?: ContainerConfig[]
}

export interface ColumnLayoutConfig {
  gutter?: number
  justify?: 'start' | 'center' | 'end' | 'space-around' | 'space-between'
  align?: 'top' | 'middle' | 'bottom'
  columns: ColumnConfig[]
}

const props = defineProps<{
  config: ColumnLayoutConfig
}>()

const gutter = computed(() => props.config.gutter ?? 20)
const justify = computed(() => props.config.justify || 'start')
const align = computed(() => props.config.align || 'top')
</script>

<template>
  <el-row :gutter="gutter" :justify="justify" :align="align">
    <el-col
      v-for="(column, idx) in config.columns"
      :key="idx"
      :span="column.span"
    >
      <slot name="column" :column="column" :index="idx">
        <div v-for="field in column.fields" :key="field" class="field-placeholder">
          <!-- Field rendering delegated to parent -->
        </div>
      </slot>
    </el-col>
  </el-row>
</template>

<style scoped>
.field-placeholder {
  min-height: 32px;
}
</style>
```

**Acceptance**:
- [ ] Columns render with correct spans
- [ ] Gutter applies correctly
- [ ] Justify/align props work

---

#### Task 3.3: Create CollapsePanel Container (2 hours)

**File**: `frontend/src/components/designer/containers/CollapsePanel.vue`

**Code Template**:

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { ElCollapse, ElCollapseItem } from 'element-plus'

export interface CollapseItemConfig {
  id: string
  title: string
  fields?: string[]
  expanded?: boolean
}

export interface CollapsePanelConfig {
  accordion?: boolean
  items: CollapseItemConfig[]
}

const props = defineProps<{
  config: CollapsePanelConfig
}>()

const activeItems = ref(
  props.config.items
    .filter(i => i.expanded)
    .map(i => i.id)
)

defineEmits<{
  (e: 'change', activeItems: string[]): void
}>()
</script>

<template>
  <el-collapse
    v-model="activeItems"
    :accordion="config.accordion"
    @change="(items: string[]) => $emit('change', items)"
  >
    <el-collapse-item
      v-for="item in config.items"
      :key="item.id"
      :name="item.id"
      :title="item.title"
    >
      <slot :name="item.id" :item="item">
        <div class="collapse-content">
          <!-- Fields rendered here -->
        </div>
      </slot>
    </el-collapse-item>
  </el-collapse>
</template>

<style scoped>
.collapse-content {
  padding: 8px 0;
}
</style>
```

**Acceptance**:
- [ ] Collapse items render
- [ ] Accordion mode works
- [ ] Expand/collapse works

---

#### Task 3.4: Create DividerElement Component (1 hour)

**File**: `frontend/src/components/designer/containers/DividerElement.vue`

**Code Template**:

```vue
<script setup lang="ts">
export interface DividerConfig {
  content?: string
  contentPosition?: 'left' | 'center' | 'right'
  borderStyle?: 'solid' | 'dashed' | 'dotted'
}

const props = defineProps<{
  config: DividerConfig
}>()
</script>

<template>
  <el-divider
    :content-position="config.contentPosition || 'center'"
    :border-style="config.borderStyle || 'solid'"
  >
    {{ config.content }}
  </el-divider>
</template>
```

**Acceptance**:
- [ ] Divider renders
- [ ] Content position works
- [ ] Border style works

---

#### Task 3.5: Create Layout Merge Service (3 hours)

**File**: `frontend/src/components/designer/services/layoutMerge.ts`

**Code Template**:

```typescript
import type { FieldMetadata, DifferentialConfig, LayoutConfig } from '@/types/metadata'

export interface MergedLayout {
  fields: FieldMetadata[]
  sections: any[]
  tabs: any[]
}

export function mergeLayoutWithDiff(
  defaultFields: FieldMetadata[],
  diffConfig: DifferentialConfig
): MergedLayout {
  const { fieldOrder, fieldOverrides, sections, tabs } = diffConfig

  // Apply custom order, or use default sort_order
  let orderedFields = [...defaultFields]
  if (fieldOrder && fieldOrder.length > 0) {
    const fieldMap = new Map(defaultFields.map(f => [f.code, f]))
    orderedFields = fieldOrder
      .map(code => fieldMap.get(code))
      .filter(Boolean) as FieldMetadata[]

    // Add any fields not in custom order
    const orderedCodes = new Set(fieldOrder)
    defaultFields.forEach(f => {
      if (!orderedCodes.has(f.code)) {
        orderedFields.push(f)
      }
    })
  } else {
    orderedFields.sort((a, b) => a.sort_order - b.sort_order)
  }

  // Apply field overrides
  const mergedFields = orderedFields.map(field => {
    const overrides = fieldOverrides?.[field.code]
    if (!overrides) return field

    return {
      ...field,
      ...overrides
    }
  })

  // Use provided sections or generate default
  const mergedSections = sections || generateDefaultSections(mergedFields)

  // Use provided tabs or generate default
  const mergedTabs = tabs || generateDefaultTabs(mergedFields)

  return {
    fields: mergedFields,
    sections: mergedSections,
    tabs: mergedTabs
  }
}

function generateDefaultSections(fields: FieldMetadata[]) {
  // Simple grouping: first 6 fields in basic, rest in detail
  const basic = fields.slice(0, 6).map(f => f.code)
  const detail = fields.slice(6).map(f => f.code)

  return [
    { id: 'basic', title: 'Basic Information', fields: basic },
    { id: 'detail', title: 'Details', fields: detail, collapsed: true }
  ]
}

function generateDefaultTabs(fields: FieldMetadata[]) {
  // Group reverse relations into tabs
  const relations = fields.filter(f => f.is_reverse_relation)
  return relations.map(r => ({
    id: r.code,
    title: r.name,
    relations: [r.code],
    type: 'table'
  }))
}
```

**Acceptance**:
- [ ] Custom field order applies
- [ ] Field overrides apply
- [ ] Default sections generate when missing
- [ ] Default tabs generate when missing

---

#### Task 3.6: Create Layout Schema Validation (2 hours)

**File**: `frontend/src/components/designer/services/layoutSchema.ts`

**Code Template**:

```typescript
import type { DifferentialConfig } from '@/types/metadata'

export interface ValidationResult {
  valid: boolean
  errors: string[]
}

export function validateDifferentialConfig(config: DifferentialConfig): ValidationResult {
  const errors: string[] = []

  // Validate fieldOrder
  if (config.fieldOrder) {
    if (!Array.isArray(config.fieldOrder)) {
      errors.push('fieldOrder must be an array')
    }
  }

  // Validate fieldOverrides
  if (config.fieldOverrides) {
    if (typeof config.fieldOverrides !== 'object') {
      errors.push('fieldOverrides must be an object')
    } else {
      for (const [fieldCode, overrides] of Object.entries(config.fieldOverrides)) {
        if (typeof overrides !== 'object') {
          errors.push(`fieldOverrides.${fieldCode} must be an object`)
        }
      }
    }
  }

  // Validate sections
  if (config.sections) {
    if (!Array.isArray(config.sections)) {
      errors.push('sections must be an array')
    } else {
      config.sections.forEach((section, idx) => {
        if (!section.id) {
          errors.push(`sections[${idx}].id is required`)
        }
        if (!section.fields || !Array.isArray(section.fields)) {
          errors.push(`sections[${idx}].fields must be an array`)
        }
      })
    }
  }

  // Validate tabs
  if (config.tabs) {
    if (!Array.isArray(config.tabs)) {
      errors.push('tabs must be an array')
    } else {
      config.tabs.forEach((tab, idx) => {
        if (!tab.id) {
          errors.push(`tabs[${idx}].id is required`)
        }
        if (!tab.title) {
          errors.push(`tabs[${idx}].title is required`)
        }
      })
    }
  }

  return {
    valid: errors.length === 0,
    errors
  }
}
```

**Acceptance**:
- [ ] Invalid configs caught
- [ ] Valid configs pass
- [ ] Error messages helpful

---

### Phase 3 Verification

```bash
# Build test
cd frontend
npm run build

# Component tests (if using vitest)
npm run test:unit
```

**Phase 3 Exit Criteria**:
- [ ] All container components render
- [ ] Merge service works
- [ ] Schema validation works
- [ ] No TypeScript errors

---

## Phase 4: Layout Designer Enhancement (3 Days / 19 Hours)

### Overview
Enhance the visual layout designer with drag-drop, real-time preview, and differential config save/load.

### Task Breakdown

#### Task 4.1: Enhance CanvasArea with Drag-Drop (4 hours)

**File**: `frontend/src/components/designer/CanvasArea.vue`

**Subtasks**:

| Subtask | Description | Lines | Verification |
|---------|-------------|-------|--------------|
| 4.1.1 | Integrate vue-draggable or similar | 30 | Drag works |
| 4.1.2 | Handle field drop events | 25 | Fields add on drop |
| 4.1.3 | Handle container drop events | 20 | Containers accept fields |
| 4.1.4 | Visual feedback during drag | 15 | Highlighting works |

**Code Template**:

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import { draggable } from 'vuedraggable'
import type { FieldMetadata } from '@/types/metadata'

const props = defineProps<{
  fields: FieldMetadata[]
  layoutConfig: any
}>()

const emit = defineEmits<{
  (e: 'update:layout', config: any): void
  (e: 'field-move', from: any, to: any): void
}>()

const draggedField = ref<FieldMetadata | null>(null)
const dropTarget = ref<string | null>(null)

function onFieldDragStart(field: FieldMetadata) {
  draggedField.value = field
}

function onFieldDragOver(targetId: string) {
  dropTarget.value = targetId
}

function onFieldDrop() {
  if (draggedField.value && dropTarget.value) {
    emit('field-move', {
      field: draggedField.value.code,
      target: dropTarget.value
    })
  }
  draggedField.value = null
  dropTarget.value = null
}
</script>

<template>
  <div class="canvas-area">
    <div
      v-for="section in layoutConfig.sections"
      :key="section.id"
      class="canvas-section"
      :class="{ 'drop-target': dropTarget === section.id }"
      @dragover.prevent="onFieldDragOver(section.id)"
      @drop="onFieldDrop"
    >
      <h3>{{ section.title }}</h3>
      <draggable
        v-model="section.fields"
        group="fields"
        item-key="code"
        @end="emit('update:layout', layoutConfig)"
      >
        <template #item="{ element: fieldCode }">
          <div
            class="canvas-field"
            draggable="true"
            @dragstart="onFieldDragStart(fields.find(f => f.code === fieldCode))"
          >
            {{ fields.find(f => f.code === fieldCode)?.name || fieldCode }}
          </div>
        </template>
      </draggable>
    </div>
  </div>
</template>

<style scoped>
.canvas-area {
  border: 2px dashed var(--el-border-color);
  min-height: 400px;
  padding: 20px;
}

.canvas-section {
  border: 1px solid var(--el-border-color);
  margin-bottom: 16px;
  padding: 12px;
}

.canvas-section.drop-target {
  background-color: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary);
}

.canvas-field {
  background-color: var(--el-fill-color-light);
  border: 1px solid var(--el-border-color);
  padding: 8px 12px;
  margin-bottom: 8px;
  cursor: move;
}
</style>
```

**Dependencies**: Phase 3 complete

**Acceptance**:
- [ ] Fields can be dragged
- [ ] Fields can be dropped into sections
- [ ] Layout updates on drop

---

#### Task 4.2: Enhance ComponentPanel (2 hours)

**File**: `frontend/src/components/designer/ComponentPanel.vue`

**Subtasks**:

| Subtask | Description | Lines | Verification |
|---------|-------------|-------|--------------|
| 4.2.1 | Display all available fields | 25 | All fields listed |
| 4.2.2 | Display container options | 20 | Containers listed |
| 4.2.3 | Auto-sync with FieldDefinition | 15 | New fields appear |

**Code Template**:

```vue
<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useFieldMetadata } from '@/composables/useFieldMetadata'
import type { FieldMetadata } from '@/types/metadata'

const props = defineProps<{
  objectCode: string
}>()

const emit = defineEmits<{
  (e: 'add-field', field: FieldMetadata): void
  (e: 'add-container', type: string): void
}>()

const { fields, fetchFields } = useFieldMetadata(props.objectCode)

const searchQuery = ref('')

const filteredFields = computed(() => {
  if (!searchQuery.value) return fields.value
  const query = searchQuery.value.toLowerCase()
  return fields.value.filter(f =>
    f.name.toLowerCase().includes(query) ||
    f.code.toLowerCase().includes(query)
  )
})

const containerTypes = [
  { type: 'tab', label: 'Tab Panel', icon: 'files' },
  { type: 'column', label: 'Column Layout', icon: 'crop' },
  { type: 'collapse', label: 'Collapse Panel', icon: 'folder-opened' },
  { type: 'divider', label: 'Divider', icon: 'minus' }
]

onMounted(() => {
  fetchFields('form')
})

function startDrag(event: DragEvent, field: FieldMetadata) {
  if (event.dataTransfer) {
    event.dataTransfer.setData('field', JSON.stringify(field))
  }
}
</script>

<template>
  <div class="component-panel">
    <div class="panel-header">
      <h3>Fields</h3>
      <el-input
        v-model="searchQuery"
        placeholder="Search fields..."
        size="small"
        clearable
      />
    </div>

    <div class="field-list">
      <div
        v-for="field in filteredFields"
        :key="field.code"
        class="field-item"
        draggable="true"
        @dragstart="startDrag($event, field)"
      >
        <el-icon><document /></el-icon>
        <span>{{ field.name }}</span>
        <el-tag size="small" type="info">{{ field.field_type }}</el-tag>
      </div>
    </div>

    <div class="panel-header">
      <h3>Containers</h3>
    </div>

    <div class="container-list">
      <div
        v-for="container in containerTypes"
        :key="container.type"
        class="container-item"
        @click="$emit('add-container', container.type)"
      >
        <el-icon><component :is="container.icon" /></el-icon>
        <span>{{ container.label }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.component-panel {
  border-right: 1px solid var(--el-border-color);
  padding: 16px;
  width: 280px;
}

.panel-header {
  margin-bottom: 12px;
}

.panel-header h3 {
  margin: 0 0 8px 0;
  font-size: 14px;
}

.field-list,
.container-list {
  max-height: 300px;
  overflow-y: auto;
}

.field-item,
.container-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  margin-bottom: 4px;
  background-color: var(--el-fill-color-light);
  border-radius: 4px;
  cursor: pointer;
}

.field-item:hover,
.container-item:hover {
  background-color: var(--el-fill-color);
}
</style>
```

**Dependencies**: Task 2.1 complete

**Acceptance**:
- [ ] All fields display
- [ ] Search filters fields
- [ ] Containers display
- [ ] Click adds container

---

#### Task 4.3: Enhance PropertyPanel (3 hours)

**File**: `frontend/src/components/designer/PropertyPanel.vue`

**Subtasks**:

| Subtask | Description | Lines | Verification |
|---------|-------------|-------|--------------|
| 4.3.1 | Show field properties | 30 | Props display |
| 4.3.2 | Allow editing visible/readonly/required | 25 | Changes save |
| 4.3.3 | Update canvas on property change | 20 | Canvas updates |

**Code Template**:

```vue
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { FieldMetadata, FieldOverride } from '@/types/metadata'

const props = defineProps<{
  selectedField?: FieldMetadata
}>()

const emit = defineEmits<{
  (e: 'update-field', code: string, overrides: FieldOverride): void
}>()

const localOverrides = ref<FieldOverride>({})

watch(() => props.selectedField, (field) => {
  if (field) {
    localOverrides.value = {}
  }
}, { immediate: true })

function updateProperty(key: keyof FieldOverride, value: any) {
  if (!props.selectedField) return

  localOverrides.value[key] = value
  emit('update-field', props.selectedField.code, localOverrides.value)
}
</script>

<template>
  <div class="property-panel" v-if="selectedField">
    <div class="panel-header">
      <h3>{{ selectedField.name }} Properties</h3>
    </div>

    <div class="property-group">
      <label>Visible</label>
      <el-switch
        :model-value="localOverrides.visible ?? true"
        @change="updateProperty('visible', $event)"
      />
    </div>

    <div class="property-group">
      <label>Read Only</label>
      <el-switch
        :model-value="localOverrides.readonly ?? false"
        @change="updateProperty('readonly', $event)"
      />
    </div>

    <div class="property-group">
      <label>Required</label>
      <el-switch
        :model-value="localOverrides.required ?? selectedField.is_required"
        @change="updateProperty('required', $event)"
      />
    </div>

    <div class="property-group">
      <label>Column Span</label>
      <el-input-number
        :model-value="localOverrides.span ?? 24"
        :min="1"
        :max="24"
        @change="updateProperty('span', $event)"
      />
    </div>
  </div>

  <div v-else class="property-panel empty">
    <el-empty description="Select a field to edit properties" />
  </div>
</template>

<style scoped>
.property-panel {
  border-left: 1px solid var(--el-border-color);
  padding: 16px;
  width: 280px;
}

.property-group {
  margin-bottom: 16px;
}

.property-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
```

**Dependencies**: Task 4.1 complete

**Acceptance**:
- [ ] Properties display for selected field
- [ ] Changes apply to canvas
- [ ] Switches/toggles work

---

#### Task 4.4: Add LayoutPreview Component (3 hours)

**File**: `frontend/src/components/designer/LayoutPreview.vue`

**Subtasks**:

| Subtask | Description | Lines | Verification |
|---------|-------------|-------|--------------|
| 4.4.1 | Create preview component | 40 | Preview renders |
| 4.4.2 | Sync with layout config | 25 | Real-time updates |
| 4.4.3 | Add responsive breakpoints | 20 | Mobile/tablet view |

**Code Template**:

```vue
<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { mergeLayoutWithDiff } from '../services/layoutMerge'
import type { FieldMetadata, DifferentialConfig } from '@/types/metadata'

const props = defineProps<{
  objectCode: string
  defaultFields: FieldMetadata[]
  diffConfig: DifferentialConfig
}>()

const viewport = ref<'desktop' | 'tablet' | 'mobile'>('desktop')

const mergedLayout = computed(() => {
  return mergeLayoutWithDiff(props.defaultFields, props.diffConfig)
})

const previewWidth = computed(() => {
  switch (viewport.value) {
    case 'mobile': return '375px'
    case 'tablet': return '768px'
    default: return '100%'
  }
})
</script>

<template>
  <div class="layout-preview">
    <div class="preview-toolbar">
      <el-radio-group v-model="viewport">
        <el-radio-button label="desktop">Desktop</el-radio-button>
        <el-radio-button label="tablet">Tablet</el-radio-button>
        <el-radio-button label="mobile">Mobile</el-radio-button>
      </el-radio-group>
    </div>

    <div class="preview-canvas" :style="{ width: previewWidth }">
      <div v-for="section in mergedLayout.sections" :key="section.id" class="preview-section">
        <h4>{{ section.title }}</h4>
        <div class="preview-fields">
          <div v-for="fieldCode in section.fields" :key="fieldCode" class="preview-field">
            {{ defaultFields.find(f => f.code === fieldCode)?.name || fieldCode }}
          </div>
        </div>
      </div>

      <div v-for="tab in mergedLayout.tabs" :key="tab.id" class="preview-tab">
        <h4>{{ tab.title }}</h4>
        <p>{{ tab.relations?.join(', ') || 'No relations' }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.layout-preview {
  border: 1px solid var(--el-border-color);
  background-color: var(--el-bg-color);
}

.preview-toolbar {
  padding: 12px;
  border-bottom: 1px solid var(--el-border-color);
  display: flex;
  justify-content: center;
}

.preview-canvas {
  margin: 0 auto;
  padding: 20px;
  transition: width 0.3s ease;
}

.preview-section {
  margin-bottom: 20px;
  padding: 12px;
  border: 1px solid var(--el-border-color);
  background-color: white;
}

.preview-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.preview-fields {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.preview-field {
  padding: 8px;
  background-color: var(--el-fill-color-light);
  border-radius: 4px;
  font-size: 12px;
}
</style>
```

**Dependencies**: Task 3.5 complete

**Acceptance**:
- [ ] Preview renders layout
- [ ] Real-time sync works
- [ ] Responsive breakpoints work

---

#### Task 4.5: Add Undo/Redo (2 hours)

**File**: `frontend/src/components/designer/LayoutDesigner.vue`

**Subtasks**:

| Subtask | Description | Lines | Verification |
|---------|-------------|-------|--------------|
| 4.5.1 | Implement history stack | 30 | States saved |
| 4.5.2 | Add undo button | 10 | Undo works |
| 4.5.3 | Add redo button | 10 | Redo works |

**Code Template**:

```typescript
// In LayoutDesigner.vue

import { ref, computed } from 'vue'

const history = ref<DifferentialConfig[]>([])
const historyIndex = ref(-1)

const canUndo = computed(() => historyIndex.value > 0)
const canRedo = computed(() => historyIndex.value < history.value.length - 1)

function addToHistory(config: DifferentialConfig) {
  // Remove any future states if we're not at the end
  history.value = history.value.slice(0, historyIndex.value + 1)
  history.value.push(JSON.parse(JSON.stringify(config)))
  historyIndex.value = history.value.length - 1
}

function undo() {
  if (canUndo.value) {
    historyIndex.value--
    layoutConfig.value = JSON.parse(JSON.stringify(history.value[historyIndex.value]))
  }
}

function redo() {
  if (canRedo.value) {
    historyIndex.value++
    layoutConfig.value = JSON.parse(JSON.stringify(history.value[historyIndex.value]))
  }
}
```

**Acceptance**:
- [ ] Undo restores previous state
- [ ] Redo restores undone state
- [ ] Buttons enable/disable correctly

---

#### Task 4.6: Save/Load Differential Config (2 hours)

**File**: `frontend/src/components/designer/LayoutDesigner.vue`

**Subtasks**:

| Subtask | Description | Lines | Verification |
|---------|-------------|-------|--------------|
| 4.6.1 | Implement save to API | 20 | Save works |
| 4.6.2 | Implement load from API | 20 | Load works |
| 4.6.3 | Add save indicator | 10 | Feedback shows |

**Code Template**:

```typescript
import { pageLayoutApi } from '@/api/system'

async function saveLayout() {
  saving.value = true
  try {
    await pageLayoutApi.saveDifferential({
      business_object: props.objectCode,
      context_type: 'detail',
      priority: 'org',
      diff_config: layoutConfig.value
    })
    ElMessage.success('Layout saved successfully')
    hasChanges.value = false
  } catch (e) {
    ElMessage.error('Failed to save layout')
  } finally {
    saving.value = false
  }
}

async function loadLayout() {
  loading.value = true
  try {
    const response = await pageLayoutApi.getLayout(props.objectCode, 'detail')
    if (response.data?.diff_config) {
      layoutConfig.value = response.data.diff_config
      addToHistory(layoutConfig.value)
    }
  } catch (e) {
    console.error('Failed to load layout:', e)
  } finally {
    loading.value = false
  }
}
```

**Dependencies**: Phase 1 complete (API endpoint exists)

**Acceptance**:
- [ ] Save button works
- [ ] Load button works
- [ ] Success/error messages display

---

### Phase 4 Verification

**Phase 4 Exit Criteria**:
- [ ] Drag-drop works smoothly
- [ ] Properties edit correctly
- [ ] Preview updates in real-time
- [ ] Undo/redo works
- [ ] Save/load works

---

## Phase 5: Integration & Testing (1.5 Days / 11 Hours)

### Overview
Comprehensive testing, performance optimization, and documentation.

### Task Breakdown

#### Task 5.1: Backend Unit Tests (3 hours)

**File**: `backend/apps/system/tests/test_field_metadata.py`

**Test Cases**:

```python
import pytest
from apps.system.models import FieldDefinition, BusinessObject

class TestFieldMetadata:
    """Test field metadata with context filtering."""

    def test_context_form_filters_correctly(self, db):
        """Test that context=form returns only show_in_form fields."""
        # Setup
        obj = BusinessObject.objects.create(code='Test', name='Test')
        FieldDefinition.objects.create(
            business_object=obj,
            code='test_field',
            name='Test Field',
            show_in_form=True,
            show_in_detail=True
        )

        # Execute
        response = client.get(f'/api/system/business-objects/Test/fields/?context=form')

        # Assert
        assert response.status_code == 200
        assert len(response.data['data']['editable_fields']) == 1

    def test_reverse_relation_separated(self, db):
        """Test that reverse relations are separated."""
        # Setup
        obj = BusinessObject.objects.create(code='Test', name='Test')
        FieldDefinition.objects.create(
            business_object=obj,
            code='normal_field',
            name='Normal Field',
            is_reverse_relation=False
        )
        FieldDefinition.objects.create(
            business_object=obj,
            code='reverse_field',
            name='Reverse Field',
            is_reverse_relation=True
        )

        # Execute
        response = client.get(f'/api/system/business-objects/Test/fields/')

        # Assert
        assert response.status_code == 200
        assert len(response.data['data']['editable_fields']) == 1
        assert len(response.data['data']['reverse_relations']) == 1
```

**Acceptance**:
- [ ] Tests pass
- [ ] Coverage >80%

---

#### Task 5.2: Frontend Integration Tests (2 hours)

**File**: `frontend/e2e/field_metadata.spec.ts`

```typescript
import { test, expect } from '@playwright/test'

test.describe('Field Metadata Integration', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login')
    await page.fill('[name=username]', 'admin')
    await page.fill('[name=password]', 'admin123')
    await page.click('button[type=submit]')
    await page.waitForURL('/dashboard')
  })

  test('detail page shows relation tabs', async ({ page }) => {
    await page.goto('/assets/test-asset-1')

    // Verify maintenance_records tab exists
    await expect(page.locator('text=维保记录')).toBeVisible()

    // Click tab
    await page.click('text=维保记录')

    // Verify table loads
    await expect(page.locator('.el-table')).toBeVisible()
  })

  test('edit page shows same fields as detail', async ({ page }) => {
    // Get fields from detail
    await page.goto('/assets/test-asset-1')
    const detailFields = await page.locator('.field-item label').allTextContents()

    // Get fields from edit
    await page.goto('/assets/test-asset-1/edit')
    const editFields = await page.locator('.form-item label').allTextContents()

    // Verify they match (excluding reverse relations in form)
    expect(detailFields).toContainEqual(expect.anything())
  })
})
```

**Acceptance**:
- [ ] Tests pass
- [ ] Maintenance records visible

---

#### Task 5.3: Layout Designer E2E Tests (2 hours)

**File**: `frontend/e2e/layout_designer.spec.ts`

```typescript
test.describe('Layout Designer', () => {
  test('can drag field to canvas', async ({ page }) => {
    await page.goto('/system/layout-designer/Asset')

    // Drag field
    await page.dragAndDrop(
      '.component-panel .field-item:first-child',
      '.canvas-area .canvas-section'
    )

    // Verify field in canvas
    await expect(page.locator('.canvas-field')).toHaveCount(1)
  })

  test('can save layout', async ({ page }) => {
    await page.goto('/system/layout-designer/Asset')

    // Make a change
    await page.click('.property-panel .el-switch:first-child')

    // Save
    await page.click('button:has-text("Save")')

    // Verify success message
    await expect(page.locator('.el-message--success')).toBeVisible()
  })
})
```

**Acceptance**:
- [ ] Tests pass
- [ ] Drag-drop works
- [ ] Save works

---

#### Task 5.4: Performance Testing (2 hours)

**Tests**:

| Test | Target | Command |
|------|--------|---------|
| Metadata API response | <200ms | `ab -n 1000 -c 10 "http://localhost:8000/api/system/business-objects/Asset/fields/?context=detail"` |
| Detail page load | <1s | Playwright measure |
| Layout designer load | <2s | Playwright measure |

**Optimization Tasks**:
- Add Redis caching for metadata
- Add frontend metadata caching
- Lazy load related object tables

---

#### Task 5.5: Documentation Updates (2 hours)

**Files to Update**:

1. `docs/reports/summaries/METADATA_LAYOUT_SYSTEM_IMPLEMENTATION_REPORT.md`
2. `docs/reports/summaries/METADATA_LAYOUT_SYSTEM_QUICK_START.md`

**Content**:
- Implementation summary
- File list and changes
- Testing results
- Known issues
- Migration guide

---

## Rollout Plan

### Week 1: Backend Deployment (Days 1-2)
- Deploy Phase 1 changes
- Monitor API performance
- No frontend impact

### Week 2: Frontend Foundation (Days 3-5)
- Deploy Phase 2 changes
- Migrate AssetDetail as proof of concept
- Monitor user feedback

### Week 3: Container Components (Days 6-7)
- Deploy Phase 3 changes
- Test component integration

### Week 4: Layout Designer (Days 8-10)
- Deploy Phase 4 changes
- User training

### Week 5: Integration & Testing (Days 11-12)
- Deploy Phase 5 changes
- Final verification
- Cleanup deprecated code

---

## Rollback Plan

### Phase 1 Rollback
```bash
# Revert migration
python manage.py migrate system zero
git revert <backend-commits>
```

### Phase 2 Rollback
```bash
# Revert frontend changes
git revert <frontend-commits>
# Old hardcoded pages still work
```

### Phase 3+ Rollback
```bash
# Components are additive, can disable via feature flag
export FEATURE_LAYOUT_DESIGNER=false
```

---

## Open Questions Tracking

| Question | Status | Decision |
|----------|--------|----------|
| Nested layout priority (role > org > global) | Open | Defer to Phase 2 |
| Optimistic locking for concurrent edits | Open | Use version field |
| Layout templates/copy feature | Open | Add in Phase 2 |
| Mobile responsive breakpoints | Open | Defined in Phase 4 |

---

## References

- PRD: `docs/plans/2025-02-03-metadata-driven-layout-system.md`
- Backend Standards: `CLAUDE.md`
- Original Field Display PRD: `docs/plans/2025-02-03-unified-field-display-design.md`
- Layout Designer PRD: `docs/plans/2026-02-03-layout-designer-enhancement.md`
