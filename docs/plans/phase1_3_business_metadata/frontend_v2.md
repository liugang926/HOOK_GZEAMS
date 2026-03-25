# Phase 1.3: Business Metadata Engine - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement metadata-driven dynamic form and list components that generate UI from business object definitions and field configurations.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/metadata.ts

export interface BusinessObject {
  id: string
  code: string
  name: string
  description?: string
  module: string
  enableWorkflow: boolean
  enableVersion: boolean
  organizationId: string
}

export interface FieldDefinition {
  id: string
  code: string
  name: string
  fieldType: FieldType
  isRequired: boolean
  isReadonly: boolean
  isSearchable: boolean
  sortable: boolean
  showInFilter: boolean
  isUnique: boolean
  maxLength?: number
  minValue?: number
  maxValue?: number
  placeholder?: string
  defaultValue?: any
  options?: FieldOption[]
  referenceObject?: string
  formula?: string
  description?: string
}

export enum FieldType {
  TEXT = 'text',
  TEXTAREA = 'textarea',
  INTEGER = 'integer',
  FLOAT = 'float',
  CURRENCY = 'currency',
  DATE = 'date',
  DATETIME = 'datetime',
  BOOLEAN = 'boolean',
  SELECT = 'select',
  MULTI_SELECT = 'multi_select',
  REFERENCE = 'reference',
  USER = 'user',
  DEPARTMENT = 'department',
  FORMULA = 'formula',
  SUB_TABLE = 'sub_table',
  FILE = 'file',
  IMAGE = 'image'
}

export interface FieldOption {
  value: string
  label: string
  color?: string
  icon?: string
}

export interface PageLayout {
  id: string
  code: string
  name: string
  layoutType: 'list' | 'form' | 'detail'
  businessObject: string
  layoutConfig: LayoutConfig
}

export interface LayoutConfig {
  columns?: ColumnConfig[]
  sections?: SectionConfig[]
  pageSize?: number
  defaultSortBy?: string
  defaultSortOrder?: 'asc' | 'desc'
}

export interface ColumnConfig {
  field: string
  label: string
  width: number
  visible: boolean
  sortable: boolean
  fixed?: 'left' | 'right'
  align?: 'left' | 'center' | 'right'
}

export interface SectionConfig {
  title: string
  collapsible?: boolean
  collapsed?: boolean
  columns: number
  fields: string[]
}

export interface DynamicData {
  id: string
  businessObject: string
  customFields: Record<string, any>
  organizationId: string
  createdAt: string
  updatedAt: string
  createdBy: string
}
```

### API Service

```typescript
// frontend/src/api/metadata.ts

import request from '@/utils/request'
import type { ApiResponse, PaginatedResponse } from '@/types/api'
import type {
  BusinessObject,
  FieldDefinition,
  PageLayout,
  DynamicData
} from '@/types/metadata'

export const metadataApi = {
  // Business Objects
  getBusinessObjects(): Promise<BusinessObject[]> {
    return request.get('/system/business-objects/')
  },

  getBusinessObject(code: string): Promise<BusinessObject> {
    return request.get(`/system/business-objects/${code}/`)
  },

  // Field Definitions
  getFieldDefinitions(objectCode: string): Promise<FieldDefinition[]> {
    return request.get('/system/field-definitions/', {
      params: { businessObject: objectCode }
    })
  },

  // Page Layouts
  getPageLayout(layoutCode: string): Promise<PageLayout> {
    return request.get(`/system/page-layouts/${layoutCode}/`)
  },

  getLayoutForObject(objectCode: string, layoutType: 'list' | 'form' | 'detail'): Promise<PageLayout> {
    return request.get('/system/page-layouts/', {
      params: { businessObject: objectCode, layoutType }
    })
  },

  // Dynamic Data CRUD
  getDynamicData(objectCode: string, params?: any): Promise<PaginatedResponse<DynamicData>> {
    return request.get(`/dynamic/${objectCode}/`, { params })
  },

  getDynamicDataDetail(objectCode: string, id: string): Promise<DynamicData> {
    return request.get(`/dynamic/${objectCode}/${id}/`)
  },

  createDynamicData(objectCode: string, data: any): Promise<DynamicData> {
    return request.post(`/dynamic/${objectCode}/`, data)
  },

  updateDynamicData(objectCode: string, id: string, data: any): Promise<DynamicData> {
    return request.put(`/dynamic/${objectCode}/${id}/`, data)
  },

  deleteDynamicData(objectCode: string, id: string): Promise<void> {
    return request.delete(`/dynamic/${objectCode}/${id}/`)
  }
}
```

---

## Component: MetadataDrivenList

```vue
<!-- frontend/src/components/metadata/MetadataDrivenList.vue -->
<template>
  <BaseListPage
    :title="layout?.name || 'Data List'"
    :fetch-method="fetchData"
    :columns="columns"
    :search-fields="searchFields"
    :filter-fields="filterFields"
    :batch-delete-method="batchDelete"
  />
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { metadataApi } from '@/api/metadata'
import type { PageLayout, FieldDefinition } from '@/types/metadata'

interface Props {
  objectCode: string
  layoutCode?: string
}

const props = defineProps<Props>()

const layout = ref<PageLayout>()
const fieldDefinitions = ref<FieldDefinition[]>([])

const columns = computed(() => {
  if (!layout.value?.layoutConfig.columns) return []
  return layout.value.layoutConfig.columns.map(col => ({
    prop: col.field,
    label: col.label,
    width: col.width,
    sortable: col.sortable,
    visible: col.visible
  }))
})

const searchFields = computed(() => {
  return fieldDefinitions.value
    .filter(f => f.isSearchable)
    .map(f => ({
      prop: f.code,
      label: f.name,
      placeholder: f.placeholder
    }))
})

const filterFields = computed(() => {
  return fieldDefinitions.value
    .filter(f => f.showInFilter)
    .map(f => ({
      prop: f.code,
      label: f.name,
      type: getFilterType(f.fieldType),
      options: f.options
    }))
})

const fetchData = async (params: any) => {
  return metadataApi.getDynamicData(props.objectCode, params)
}

const batchDelete = async (data: { ids: string[] }) => {
  return metadataApi.post(`/dynamic/${props.objectCode}/batch-delete/`, data)
}

const getFilterType = (fieldType: string) => {
  const typeMap: Record<string, string> = {
    text: 'text',
    select: 'select',
    date: 'date',
    datetime: 'datetime'
  }
  return typeMap[fieldType] || 'text'
}

onMounted(async () => {
  if (props.layoutCode) {
    layout.value = await metadataApi.getPageLayout(props.layoutCode)
  } else {
    layout.value = await metadataApi.getLayoutForObject(props.objectCode, 'list')
  }
  fieldDefinitions.value = await metadataApi.getFieldDefinitions(props.objectCode)
})
</script>
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/metadata.ts` | Metadata type definitions |
| `frontend/src/api/metadata.ts` | Metadata API service |
| `frontend/src/components/metadata/MetadataDrivenList.vue` | Metadata list component |
| `frontend/src/components/metadata/MetadataDrivenForm.vue` | Metadata form component |
| `frontend/src/components/metadata/FieldRenderer.vue` | Dynamic field renderer |
