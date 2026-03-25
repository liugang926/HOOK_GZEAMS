# Phase 7.3: Asset Tags - Frontend Implementation v2

## Document Information

| Project | Details |
|---------|---------|
| PRD Version | v2.0 (Updated for API Standardization) |
| Updated Date | 2026-01-22 |
| References | [frontend_api_standardization_design.md](../common_base_features/00_core/frontend_api_standardization_design.md) |

---

## Task Overview

Implement asset tagging functionality for flexible asset categorization and filtering.

---

## API Service Layer

### Type Definitions

```typescript
// frontend/src/types/tags.ts

export interface AssetTag {
  id: string
  name: string
  code: string
  color: string
  icon?: string
  description?: string
  isSystem: boolean
  usageCount: number
  organizationId: string
}

export interface TagGroup {
  id: string
  name: string
  code: string
  tags: AssetTag[]
  color?: string
}

export interface AssetTagAssignment {
  assetId: string
  tagIds: string[]
}
```

### API Service

```typescript
// frontend/src/api/tags.ts

import request from '@/utils/request'
import type { PaginatedResponse } from '@/types/api'
import type { AssetTag, TagGroup, AssetTagAssignment } from '@/types/tags'

export const tagApi = {
  // Tags
  listTags(params?: any): Promise<PaginatedResponse<AssetTag>> {
    return request.get('/tags/', { params })
  },

  getTag(id: string): Promise<AssetTag> {
    return request.get(`/tags/${id}/`)
  },

  createTag(data: Partial<AssetTag>): Promise<AssetTag> {
    return request.post('/tags/', data)
  },

  updateTag(id: string, data: Partial<AssetTag>): Promise<AssetTag> {
    return request.put(`/tags/${id}/`, data)
  },

  deleteTag(id: string): Promise<void> {
    return request.delete(`/tags/${id}/`)
  },

  // Tag Groups
  getGroups(): Promise<TagGroup[]> {
    return request.get('/tags/groups/')
  },

  createGroup(data: Partial<TagGroup>): Promise<TagGroup> {
    return request.post('/tags/groups/', data)
  },

  // Assignments
  assignTags(data: AssetTagAssignment): Promise<void> {
    return request.post('/tags/assign/', data)
  },

  removeTag(assetId: string, tagId: string): Promise<void> {
    return request.delete(`/tags/assets/${assetId}/tags/${tagId}/`)
  }
}
```

---

## Component: TagSelector

```vue
<!-- frontend/src/components/assets/TagSelector.vue -->
<template>
  <div class="tag-selector">
    <el-select
      v-model="selectedValues"
      multiple
      filterable
      allow-create
      placeholder="选择标签"
      @change="handleChange"
    >
      <el-option
        v-for="tag in tags"
        :key="tag.id"
        :label="tag.name"
        :value="tag.id"
      >
        <div class="tag-option">
          <span
            class="tag-color-dot"
            :style="{ backgroundColor: tag.color }"
          />
          <span>{{ tag.name }}</span>
        </div>
      </el-option>
    </el-select>

    <!-- Tag Groups (optional) -->
    <div v-if="showGroups" class="tag-groups">
      <div
        v-for="group in groupedTags"
        :key="group.id"
        class="tag-group"
      >
        <div class="group-label">{{ group.name }}</div>
        <div class="group-tags">
          <el-tag
            v-for="tag in group.tags"
            :key="tag.id"
            :color="tag.color"
            :class="{ selected: selectedValues.includes(tag.id) }"
            @click="toggleTag(tag.id)"
          >
            {{ tag.name }}
          </el-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { tagApi } from '@/api/tags'
import type { AssetTag, TagGroup } from '@/types/tags'

interface Props {
  modelValue: string[]
  showGroups?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: string[]): void
}

const props = withDefaults(defineProps<Props>(), {
  showGroups: false
})

const emit = defineEmits<Emits>()

const selectedValues = ref<string[]>(props.modelValue)
const tags = ref<AssetTag[]>([])
const groups = ref<TagGroup[]>([])

const groupedTags = computed(() => {
  return groups.value.map(group => ({
    ...group,
    tags: tags.value.filter(tag => tag.groupId === group.id)
  }))
})

const loadTags = async () => {
  try {
    const response = await tagApi.listTags({ pageSize: 100 })
    tags.value = response.results
  } catch (error) {
    // Error handled by interceptor
  }
}

const loadGroups = async () => {
  try {
    groups.value = await tagApi.getGroups()
  } catch (error) {
    // Error handled by interceptor
  }
}

const handleChange = () => {
  emit('update:modelValue', selectedValues.value)
}

const toggleTag = (tagId: string) => {
  const index = selectedValues.value.indexOf(tagId)
  if (index > -1) {
    selectedValues.value.splice(index, 1)
  } else {
    selectedValues.value.push(tagId)
  }
  handleChange()
}

onMounted(() => {
  loadTags()
  if (props.showGroups) {
    loadGroups()
  }
})
</script>

<style scoped>
.tag-selector {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tag-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tag-color-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.tag-groups {
  margin-top: 8px;
}

.tag-group {
  margin-bottom: 12px;
}

.group-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 6px;
}

.group-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.group-tags .el-tag {
  cursor: pointer;
}

.group-tags .el-tag.selected {
  opacity: 0.7;
}
</style>
```

---

## Output Files

| File | Description |
|------|-------------|
| `frontend/src/types/tags.ts` | Tag type definitions |
| `frontend/src/api/tags.ts` | Tag API service |
| `frontend/src/components/assets/TagSelector.vue` | Tag selector component |
| `frontend/src/views/assets/TagManagement.vue` | Tag management page |
